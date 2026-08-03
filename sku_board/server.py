from __future__ import annotations

import argparse
import cgi
import html
import json
import mimetypes
import os
import uuid
from http.cookies import SimpleCookie
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from sku_board.backend import (
    add_feedback,
    add_item,
    add_note,
    add_refresh,
    add_suggested_weekly_tasks,
    analyze_meta_ads,
    assign_design_owner,
    authenticate_user,
    auth_state,
    bind_facebook_campaign,
    bind_meta_ad_account,
    change_own_password,
    check_ai_image_service,
    clear_session,
    create_ad_launch,
    create_auth_user,
    create_meta_credential,
    create_system_credential_from_wizard,
    create_design_task,
    delete_ad_launch,
    delete_ai_image_outputs,
    delete_auth_user,
    delete_meta_credential,
    delete_all_items,
    delete_design_task,
    delete_item,
    export_board_csv,
    generate_ad_launch_ai_image,
    generate_ad_launch_ai_image_edit,
    complete_meta_oauth,
    get_ai_image_config,
    get_ai_director_settings,
    get_ai_image_job,
    import_shopline_products,
    list_auth_users,
    list_ad_launches,
    list_board,
    list_design_tasks,
    list_facebook_campaign_options,
    list_meta_ad_accounts,
    list_meta_credentials,
    list_shopline_products,
    log_ai_image_error,
    plan_ai_image_suite,
    plan_ai_image_suite_upload,
    prune_ai_image_output_files,
    record_ai_image_quality_telemetry,
    regenerate_selling,
    review_ai_image_suite,
    recover_recent_ai_image_suite,
    refresh_ai_image_account_pool,
    read_ai_image_output,
    reset_user_password,
    resume_ai_image_jobs,
    save_ai_director_settings,
    start_ai_image_job,
    set_meta_credential_active,
    set_user_active,
    set_meta_ad_status,
    sync_facebook_ads,
    sync_meta_credential,
    start_meta_oauth,
    test_ai_director_service,
    publish_ad_launch,
    update_item,
    update_design_progress,
    update_ad_launch,
    update_design_task,
    upload_ad_launch_material,
    validate_meta_credential,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"


class SkuBoardHandler(BaseHTTPRequestHandler):
    server_version = "SkuBoard/0.1"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_common_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self.serve_static("index.html")
            return
        if parsed.path.startswith("/static/"):
            self.serve_static(parsed.path.removeprefix("/static/"))
            return
        if parsed.path == "/api/health":
            self.send_json({"ok": True, "service": "sku-board"})
            return
        if parsed.path == "/api/sku-board/session":
            self.send_json(auth_state(self.session_token()))
            return
        if parsed.path == "/api/sku-board/meta-oauth/callback":
            query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self.handle_meta_oauth_callback(query)
            return
        if parsed.path.startswith("/api/sku-board/ai-image-output/"):
            material_id = unquote(parsed.path.removeprefix("/api/sku-board/ai-image-output/")).strip("/")
            query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self.handle_auth_ai_image_output(material_id, query.get("remote", ""))
            return
        if parsed.path.startswith("/api/sku-board/ai-image-jobs/"):
            job_id = unquote(parsed.path.removeprefix("/api/sku-board/ai-image-jobs/")).strip("/")
            self.handle_auth_read(lambda user: get_ai_image_job(job_id, user))
            return
        if parsed.path == "/api/sku-board/users":
            self.handle_auth_read(lambda user: list_auth_users(user))
            return
        if parsed.path == "/api/sku-board/meta-credentials":
            self.handle_auth_read(lambda user: list_meta_credentials(user))
            return
        if parsed.path == "/api/sku-board/meta-assets":
            self.handle_auth_read(lambda user: list_meta_ad_accounts(user))
            return
        if parsed.path == "/api/sku-board/design-tasks":
            self.handle_auth_read(lambda user: list_design_tasks(user))
            return
        if parsed.path == "/api/sku-board/ad-launches":
            query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self.handle_auth_read(lambda user: list_ad_launches(user, query))
            return
        if parsed.path == "/api/sku-board/ai-image-health":
            query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self.handle_auth_read(lambda user: check_ai_image_service(user, query.get("nodeId", "")))
            return
        if parsed.path == "/api/sku-board/ai-image-config":
            self.handle_auth_read(lambda user: get_ai_image_config(user))
            return
        if parsed.path == "/api/sku-board/ai-director-settings":
            self.handle_auth_read(lambda user: get_ai_director_settings(user))
            return
        if parsed.path == "/api/sku-board/facebook-campaigns":
            query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self.handle_auth_read(lambda user: list_facebook_campaign_options(user, query))
            return
        if parsed.path == "/api/sku-board/meta-ad-analysis":
            query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self.handle_auth_read(lambda user: analyze_meta_ads(query, user))
            return
        if parsed.path == "/api/sku-board":
            query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self.handle_auth_read(lambda user: list_board(query))
            return
        if parsed.path == "/api/sku-board/shopline-products":
            self.handle_auth_read(lambda user: list_shopline_products())
            return
        if parsed.path == "/api/sku-board/export.csv":
            query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self.handle_auth_text(lambda user: export_board_csv(query), content_type="text/csv; charset=utf-8", filename="sku-board-export.csv")
            return
        self.send_json({"ok": False, "error": "route not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/sku-board/login":
            self.handle_login()
            return
        if parsed.path == "/api/sku-board/logout":
            self.handle_logout()
            return
        if parsed.path == "/api/sku-board/users":
            self.handle_auth_mutation(lambda payload, user: create_auth_user(payload, user), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/sku-board/meta-credentials":
            self.handle_auth_mutation(lambda payload, user: create_meta_credential(payload, user), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/sku-board/meta-credentials/oauth":
            self.handle_auth_mutation(lambda payload, user: start_meta_oauth(payload, user))
            return
        if parsed.path == "/api/sku-board/meta-credentials/system-wizard":
            self.handle_auth_mutation(lambda payload, user: create_system_credential_from_wizard(payload, user), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/sku-board/meta-asset-bindings":
            self.handle_auth_mutation(lambda payload, user: bind_meta_ad_account(payload, user))
            return
        if parsed.path == "/api/sku-board/users/password":
            self.handle_auth_mutation(lambda payload, user: change_own_password(payload, user))
            return
        if parsed.path == "/api/sku-board/design-tasks":
            self.handle_auth_mutation(lambda payload, user: create_design_task(payload, user), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/sku-board/ad-launches":
            self.handle_auth_mutation(lambda payload, user: create_ad_launch(payload, user), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/sku-board/ad-launch-materials":
            self.handle_auth_upload(lambda fields, files, user: upload_ad_launch_material(fields, files, user), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/sku-board/ad-launch-ai-image":
            self.handle_auth_mutation(
                lambda payload, user: start_ai_image_job("text", payload, user),
                HTTPStatus.CREATED,
                ai_image_operation="text-to-image",
            )
            return
        if parsed.path == "/api/sku-board/ad-launch-ai-image-edit":
            self.handle_auth_upload(
                lambda fields, files, user: start_ai_image_job("edit", fields, user, files),
                HTTPStatus.CREATED,
                ai_image_operation="reference-image",
            )
            return
        if parsed.path == "/api/sku-board/ai-image-suite-plan":
            self.handle_auth_mutation(lambda payload, user: plan_ai_image_suite(payload, user))
            return
        if parsed.path == "/api/sku-board/ai-image-suite-plan-upload":
            self.handle_auth_upload(lambda fields, files, user: plan_ai_image_suite_upload(fields, files, user))
            return
        if parsed.path == "/api/sku-board/ai-image-suite-review":
            self.handle_auth_upload(lambda fields, files, user: review_ai_image_suite(fields, files, user))
            return
        if parsed.path == "/api/sku-board/ai-director-settings":
            self.handle_auth_mutation(lambda payload, user: save_ai_director_settings(payload, user))
            return
        if parsed.path == "/api/sku-board/ai-director-test":
            self.handle_auth_mutation(lambda payload, user: test_ai_director_service(payload, user))
            return
        if parsed.path == "/api/sku-board/ai-image-recover":
            self.handle_auth_mutation(
                lambda payload, user: recover_recent_ai_image_suite(
                    user,
                    payload.get("suiteRunId"),
                    payload.get("knownPages"),
                    payload.get("suiteKey"),
                    payload.get("suiteCountry"),
                    payload.get("suiteCount"),
                )
            )
            return
        if parsed.path == "/api/sku-board/ai-image-accounts-refresh":
            self.handle_auth_mutation(lambda payload, user: refresh_ai_image_account_pool(user))
            return
        if parsed.path == "/api/sku-board/ai-image-quality-telemetry":
            self.handle_auth_mutation(lambda payload, user: record_ai_image_quality_telemetry(payload, user))
            return
        if parsed.path == "/api/sku-board/items":
            self.handle_auth_mutation(lambda payload, user: add_item(payload), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/sku-board/import-shopline":
            self.handle_auth_mutation(lambda payload, user: import_shopline_products(payload), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/sku-board/facebook-ads-sync":
            self.handle_auth_mutation(lambda payload, user: sync_facebook_ads(payload, user))
            return
        if parsed.path == "/api/sku-board/suggested-weekly-tasks":
            self.handle_auth_mutation(lambda payload, user: add_suggested_weekly_tasks(payload))
            return

        ad_launch_route = parse_ad_launch_route(parsed.path)
        if ad_launch_route:
            launch_id, action = ad_launch_route
            if action == "publish":
                self.handle_auth_mutation(lambda payload, user: publish_ad_launch(launch_id, payload, user))
                return
            if action == "status":
                self.handle_auth_mutation(lambda payload, user: set_meta_ad_status(launch_id, payload, user))
                return

        route = parse_item_route(parsed.path)
        if route:
            sku, action = route
            if action == "notes":
                self.handle_auth_mutation(lambda payload, user: add_note(sku, payload))
                return
            if action == "feedback":
                self.handle_auth_mutation(lambda payload, user: add_feedback(sku, payload))
                return
            if action == "refresh":
                self.handle_auth_mutation(lambda payload, user: add_refresh(sku, payload))
                return
            if action == "selling-auto":
                self.handle_auth_mutation(lambda payload, user: regenerate_selling(sku, payload))
                return
            if action == "design-owner":
                self.handle_auth_mutation(lambda payload, user: assign_design_owner(sku, payload, user))
                return
            if action == "design-progress":
                self.handle_auth_mutation(lambda payload, user: update_design_progress(sku, payload, user))
                return
            if action == "facebook-binding":
                self.handle_auth_mutation(lambda payload, user: bind_facebook_campaign(sku, payload, user))
                return

        user_route = parse_user_route(parsed.path)
        if user_route:
            username, action = user_route
            if action == "reset-password":
                self.handle_auth_mutation(lambda payload, user: reset_user_password(username, payload, user))
                return
            if action == "active":
                self.handle_auth_mutation(lambda payload, user: set_user_active(username, payload, user))
                return

        credential_route = parse_meta_credential_route(parsed.path)
        if credential_route:
            credential_id, action = credential_route
            if action == "validate":
                self.handle_auth_mutation(lambda payload, user: validate_meta_credential(credential_id, user))
                return
            if action == "sync":
                self.handle_auth_mutation(lambda payload, user: sync_meta_credential(credential_id, user))
                return
            if action == "active":
                self.handle_auth_mutation(lambda payload, user: set_meta_credential_active(credential_id, payload, user))
                return

        self.send_json({"ok": False, "error": "route not found"}, status=HTTPStatus.NOT_FOUND)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        design_task_route = parse_design_task_route(parsed.path)
        if design_task_route:
            task_id, _ = design_task_route
            self.handle_auth_mutation(lambda payload, user: update_design_task(task_id, payload, user))
            return
        ad_launch_route = parse_ad_launch_route(parsed.path)
        if ad_launch_route and not ad_launch_route[1]:
            launch_id, _ = ad_launch_route
            self.handle_auth_mutation(lambda payload, user: update_ad_launch(launch_id, payload, user))
            return
        route = parse_item_route(parsed.path)
        if route and not route[1]:
            sku, _ = route
            self.handle_item_patch(sku)
            return
        self.send_json({"ok": False, "error": "route not found"}, status=HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/sku-board/ai-image-outputs":
            self.handle_auth_mutation(lambda payload, user: delete_ai_image_outputs(payload, user))
            return
        if parsed.path == "/api/sku-board/items":
            self.handle_auth_mutation(lambda payload, user: delete_all_items(payload))
            return
        ad_launch_route = parse_ad_launch_route(parsed.path)
        if ad_launch_route and not ad_launch_route[1]:
            launch_id, _ = ad_launch_route
            self.handle_auth_mutation(lambda payload, user: delete_ad_launch(launch_id, user))
            return
        design_task_route = parse_design_task_route(parsed.path)
        if design_task_route:
            task_id, _ = design_task_route
            self.handle_auth_mutation(lambda payload, user: delete_design_task(task_id, user))
            return
        route = parse_item_route(parsed.path)
        if route and not route[1]:
            sku, _ = route
            self.handle_auth_mutation(lambda payload, user: delete_item(sku, payload))
            return
        user_route = parse_user_route(parsed.path)
        if user_route and not user_route[1]:
            username, _ = user_route
            self.handle_auth_mutation(lambda payload, user: delete_auth_user(username, user))
            return
        credential_route = parse_meta_credential_route(parsed.path)
        if credential_route and not credential_route[1]:
            credential_id, _ = credential_route
            self.handle_auth_mutation(lambda payload, user: delete_meta_credential(credential_id, user))
            return
        self.send_json({"ok": False, "error": "route not found"}, status=HTTPStatus.NOT_FOUND)

    def handle_mutation(self, callback: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        try:
            payload = self.read_json_body()
            self.send_json(callback(payload), status=status)
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_auth_read(self, callback: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        user = auth_state(self.session_token()).get("user")
        if not user:
            self.send_json({"ok": False, "error": "请先登录"}, status=HTTPStatus.UNAUTHORIZED)
            return
        try:
            self.send_json(callback(user), status=status)
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_auth_text(self, callback: Any, content_type: str = "text/plain; charset=utf-8", filename: str | None = None) -> None:
        user = auth_state(self.session_token()).get("user")
        if not user:
            self.send_json({"ok": False, "error": "请先登录"}, status=HTTPStatus.UNAUTHORIZED)
            return
        try:
            self.send_text(callback(user), content_type=content_type, filename=filename)
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_auth_ai_image_output(self, material_id: str, remote_url: str = "") -> None:
        if not auth_state(self.session_token()).get("user"):
            self.send_json({"ok": False, "error": "请先登录"}, status=HTTPStatus.UNAUTHORIZED)
            return
        try:
            content, content_type = read_ai_image_output(material_id, remote_url)
            self.send_bytes(content, content_type)
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.NOT_FOUND)
        except OSError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_item_patch(self, sku: str) -> None:
        try:
            if not auth_state(self.session_token()).get("user"):
                self.send_json({"ok": False, "error": "请先登录"}, status=HTTPStatus.UNAUTHORIZED)
                return
            payload = self.read_json_body()
            design = payload.get("design") if isinstance(payload.get("design"), dict) else {}
            if "owner" in design and not auth_state(self.session_token()).get("user"):
                self.send_json({"ok": False, "error": "请先登录后再分配设计负责人"}, status=HTTPStatus.UNAUTHORIZED)
                return
            self.send_json(update_item(sku, payload))
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_auth_mutation(
        self,
        callback: Any,
        status: HTTPStatus = HTTPStatus.OK,
        ai_image_operation: str = "",
    ) -> None:
        user = auth_state(self.session_token()).get("user")
        if not user:
            self.send_json({"ok": False, "error": "请先登录"}, status=HTTPStatus.UNAUTHORIZED)
            return
        try:
            payload = self.read_json_body()
            self.send_json(callback(payload, user), status=status)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return
        except ValueError as exc:
            if ai_image_operation:
                self.send_ai_image_error(exc, user, ai_image_operation, HTTPStatus.BAD_REQUEST)
            else:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            if ai_image_operation:
                self.send_ai_image_error(exc, user, ai_image_operation, HTTPStatus.INTERNAL_SERVER_ERROR)
            else:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_auth_upload(
        self,
        callback: Any,
        status: HTTPStatus = HTTPStatus.OK,
        ai_image_operation: str = "",
    ) -> None:
        user = auth_state(self.session_token()).get("user")
        if not user:
            self.send_json({"ok": False, "error": "璇峰厛鐧诲綍"}, status=HTTPStatus.UNAUTHORIZED)
            return
        try:
            fields, files = self.read_multipart_body()
            self.send_json(callback(fields, files, user), status=status)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return
        except ValueError as exc:
            if ai_image_operation:
                self.send_ai_image_error(exc, user, ai_image_operation, HTTPStatus.BAD_REQUEST)
            else:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            if ai_image_operation:
                self.send_ai_image_error(exc, user, ai_image_operation, HTTPStatus.INTERNAL_SERVER_ERROR)
            else:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_ai_image_error(
        self,
        exc: Exception,
        user: dict[str, Any],
        operation: str,
        status: HTTPStatus,
    ) -> None:
        """Return traceable, non-empty failures for every logged-in image role."""
        request_id = f"img-{uuid.uuid4().hex[:10]}"
        message = str(exc).strip()
        if not message:
            message = f"生图请求在 {type(exc).__name__} 阶段意外中断，请使用请求编号联系管理员排查。"
        context = {
            "requestId": request_id,
            "operation": operation,
            "username": str(user.get("username") or "unknown")[:80],
            "role": str(user.get("role") or "unknown")[:40],
            "exceptionType": type(exc).__name__,
            "message": message[:1200],
        }
        try:
            log_ai_image_error("panel-request-failed", context)
        except Exception:
            pass
        self.send_json(
            {
                "ok": False,
                "error": message,
                "errorCode": "ai_image_request_failed",
                "requestId": request_id,
                "operation": operation,
            },
            status=status,
        )

    def handle_login(self) -> None:
        try:
            payload = self.read_json_body()
            result = authenticate_user(payload)
            token = result.pop("token")
            self.send_json(
                result,
                headers={
                    "Set-Cookie": (
                        f"sku_board_session={token}; Path=/; Max-Age=604800; "
                        "HttpOnly; SameSite=Lax"
                    )
                },
            )
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.UNAUTHORIZED)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_logout(self) -> None:
        clear_session(self.session_token())
        self.send_json(
            {"ok": True},
            headers={"Set-Cookie": "sku_board_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"},
        )

    def handle_meta_oauth_callback(self, query: dict[str, str]) -> None:
        try:
            if query.get("error"):
                raise ValueError(query.get("error_description") or "Meta 授权被取消")
            result = complete_meta_oauth(query.get("code"), query.get("state"))
            credential = result.get("credential") if isinstance(result, dict) else {}
            name = html.escape(str((credential or {}).get("name") or "个人凭证"))
            message = f"{name} 已完成授权，可返回面板刷新凭证列表。"
            ok = True
        except ValueError as exc:
            message = html.escape(str(exc))
            ok = False
        body = (
            "<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>Meta 授权</title>"
            "<style>body{font:16px 'Microsoft YaHei',sans-serif;padding:44px;background:#f5f9ff;color:#1c2739}"
            ".card{max-width:520px;padding:28px;border:1px solid #d9e7f7;border-radius:16px;background:#fff;box-shadow:0 18px 44px rgba(70,101,150,.12)}"
            "strong{display:block;font-size:22px;margin-bottom:12px}.ok{color:#16825f}.error{color:#bc4545}</style><div class='card'>"
            f"<strong class={'ok' if ok else 'error'}>{'授权完成' if ok else '授权失败'}</strong><p>{message}</p><p>此窗口会自动关闭。</p></div>"
            f"<script>window.opener&&window.opener.postMessage({{type:'sku-board-meta-oauth',ok:{str(ok).lower()}}},window.location.origin);setTimeout(()=>window.close(),1800)</script>"
            "</html>"
        )
        self.send_text(body, content_type="text/html; charset=utf-8")

    def session_token(self) -> str:
        raw = self.headers.get("Cookie", "")
        cookie = SimpleCookie()
        cookie.load(raw)
        return cookie.get("sku_board_session").value if cookie.get("sku_board_session") else ""

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        if length > 1024 * 1024:
            raise ValueError("request body too large")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid json body") from exc
        if not isinstance(payload, dict):
            raise ValueError("json body must be an object")
        return payload

    def read_multipart_body(self) -> tuple[dict[str, Any], dict[str, Any]]:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data"):
            raise ValueError("request must be multipart/form-data")
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            raise ValueError("empty upload body")
        if length > 350 * 1024 * 1024:
            raise ValueError("upload file is too large")
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(length),
            },
            keep_blank_values=True,
        )
        fields: dict[str, Any] = {}
        files: dict[str, Any] = {}
        for key in form.keys():
            item = form[key]
            if isinstance(item, list):
                item = item[0]
            if getattr(item, "filename", ""):
                files[key] = item
            else:
                fields[key] = item.value
        return fields, files

    def serve_static(self, relative_path: str) -> None:
        target = (STATIC_DIR / relative_path).resolve()
        try:
            target.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_json({"ok": False, "error": "invalid path"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not target.exists() or not target.is_file():
            self.send_json({"ok": False, "error": "file not found"}, status=HTTPStatus.NOT_FOUND)
            return
        content = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type=content_type, cache=False)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_common_headers(self, content_type: str = "application/json; charset=utf-8", cache: bool = False) -> None:
        self.send_header("Content-Type", content_type)
        allowed_origin = os.environ.get("SKU_BOARD_ALLOWED_ORIGIN", "").rstrip("/")
        request_origin = self.headers.get("Origin", "").rstrip("/")
        if allowed_origin and request_origin == allowed_origin:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Vary", "Origin")
        self.send_header("Cache-Control", "public, max-age=300" if cache else "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")

    def send_json(
        self,
        payload: object,
        status: HTTPStatus = HTTPStatus.OK,
        headers: dict[str, str] | None = None,
    ) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_common_headers()
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_text(
        self,
        content: str,
        status: HTTPStatus = HTTPStatus.OK,
        content_type: str = "text/plain; charset=utf-8",
        filename: str | None = None,
    ) -> None:
        raw = content.encode("utf-8-sig")
        self.send_response(status)
        self.send_common_headers(content_type=content_type, cache=False)
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_bytes(self, content: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_common_headers(content_type=content_type, cache=False)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[sku-board] {self.address_string()} - {format % args}")


def parse_item_route(path: str) -> tuple[str, str] | None:
    prefix = "/api/sku-board/items/"
    if not path.startswith(prefix):
        return None
    rest = path.removeprefix(prefix).strip("/")
    if not rest:
        return None
    parts = rest.split("/", 1)
    sku = unquote(parts[0])
    action = parts[1] if len(parts) > 1 else ""
    return sku, action


def parse_user_route(path: str) -> tuple[str, str] | None:
    prefix = "/api/sku-board/users/"
    if not path.startswith(prefix):
        return None
    rest = path.removeprefix(prefix).strip("/")
    if not rest or rest == "password":
        return None
    parts = rest.split("/", 1)
    username = unquote(parts[0])
    action = parts[1] if len(parts) > 1 else ""
    return username, action


def parse_meta_credential_route(path: str) -> tuple[str, str] | None:
    prefix = "/api/sku-board/meta-credentials/"
    if not path.startswith(prefix):
        return None
    rest = path.removeprefix(prefix).strip("/")
    if not rest or rest == "oauth":
        return None
    parts = rest.split("/", 1)
    credential_id = unquote(parts[0])
    action = parts[1] if len(parts) > 1 else ""
    return credential_id, action


def parse_design_task_route(path: str) -> tuple[str, str] | None:
    prefix = "/api/sku-board/design-tasks/"
    if not path.startswith(prefix):
        return None
    rest = path.removeprefix(prefix).strip("/")
    if not rest:
        return None
    parts = rest.split("/", 1)
    task_id = unquote(parts[0])
    action = parts[1] if len(parts) > 1 else ""
    return task_id, action


def parse_ad_launch_route(path: str) -> tuple[str, str] | None:
    prefix = "/api/sku-board/ad-launches/"
    if not path.startswith(prefix):
        return None
    rest = path.removeprefix(prefix).strip("/")
    if not rest:
        return None
    parts = rest.split("/", 1)
    launch_id = unquote(parts[0])
    action = parts[1] if len(parts) > 1 else ""
    return launch_id, action


def run(host: str, port: int) -> None:
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((host, port), SkuBoardHandler)
    cleanup = prune_ai_image_output_files(force=True)
    recovery = resume_ai_image_jobs()
    print(f"SKU Board running at http://{host}:{port}/")
    if cleanup["removed"]:
        print(
            "Expired local AI image outputs removed: "
            f"files={cleanup['removed']}, bytes={cleanup['bytes']}"
        )
    if recovery["loaded"] or recovery["removed"]:
        print(
            "AI image jobs restored: "
            f"loaded={recovery['loaded']}, resumed={recovery['resumed']}, removed={recovery['removed']}"
        )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SKU operation board.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8793)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
