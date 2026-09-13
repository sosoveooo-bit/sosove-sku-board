"""Isolated local UI fixture server. No real accounts, data, models or rendering.

Run: python -m sku_board.tests.atelier_preview_server --port 8795
Every project lives in a fresh temporary directory, removed on normal exit.
This intentionally does not subclass the production SKU Board HTTP handler.
"""

from __future__ import annotations

import argparse
import cgi
import json
import signal
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from sku_board import cod_prompt_atelier as atelier, cod_prompt_assets as assets, cod_prompt_queue as queues, cod_prompt_render as renderer
from sku_board.cod_prompt_contract import compile_execution_prompt, normalize_outline, normalize_page
from sku_board.tests.test_cod_prompt_atelier import FakeDirector


ACTOR = {"username": "fixtureowner", "name": "隔离验收测试账号", "role": "designer"}
PREFIX = "/api/sku-board/cod-atelier/projects"
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
STATIC_PATHS = {
    "/cod-prompt-generator.html": ("cod-prompt-generator.html", "text/html; charset=utf-8"),
    "/static/cod-prompt-generator.js": ("cod-prompt-generator.js", "text/javascript; charset=utf-8"),
    "/static/cod-prompt-generator.css": ("cod-prompt-generator.css", "text/css; charset=utf-8"),
    "/static/assets/sosove-logo.jpeg": ("assets/sosove-logo.jpeg", "image/jpeg"),
}
RENDER_DISABLED = "隔离验收服务已禁用真实生图。这里只测试模拟 Prompt、项目与版本，不会调用付费模型。"


class PreviewDirector(FakeDirector):
    """Deterministic responses derived only from each request's product context."""

    def __init__(self, delay: float = 0.2):
        super().__init__()
        self.settings.update(model="mock-director", baseUrl="mock://fixture-only", apiKey="fixture-only-not-a-secret")
        self.delay = delay
        self.stopping = threading.Event()
        self.failed_products: set[str] = set()

    def can_use_ai_image(self, actor):
        return isinstance(actor, dict) and actor.get("username") == ACTOR["username"]

    def load_board(self):
        return {"users": [ACTOR]}

    def find_user(self, board, username):
        return ACTOR if username == ACTOR["username"] else None

    def invoke_ai_director_chat(self, settings, messages):
        if self.stopping.wait(self.delay):
            raise ValueError("测试服务已停止。")
        content = messages[-1]["content"]
        source = content[0]["text"] if isinstance(content, list) else content
        context = json.loads(source.split("CURRENT_PRODUCT_DATA_JSON:\n", 1)[1])
        if "reviewKind" in context:
            settings["_lastDirectorCall"] = {"requestedModel": "mock-director", "model": "mock-director", "fallbackUsed": False, "attempts": []}
            return json.dumps({"issues": []}), 1
        product = context["form"]["product"]
        # Optional browser failure fixture: type this marker into style notes.
        if "FIXTURE_FAIL_ONCE" in context["form"].get("style", "") and product not in self.failed_products:
            self.failed_products.add(product)
            raise ValueError("[测试模拟] 本次模型请求故意失败；再次继续即可恢复。未调用外部服务。")
        return super().invoke_ai_director_chat(settings, messages)

    @staticmethod
    def outline(context):
        result = FakeDirector.outline(context)
        result["masterPrompt"] = "[测试夹具 · 非真实模型输出]\n" + result["masterPrompt"]
        return result

    @staticmethod
    def pages(context):
        current = context["form"]
        result = []
        for entry in context["outline"]:
            rewrite = context.get("rewriteInstruction", "") if context.get("rewriteTargetPage") == entry["page"] else ""
            result.append({**entry, "modelPrompt": (
                f"[测试夹具 · 非真实模型输出] {current['product']} 第{entry['page']}页："
                f"只围绕当前卖点「{entry['focus']}」，安排产品近景、本地人物使用场景和三层图文信息。"
                f"沿用当前视觉要求：{current.get('style', '')}。目标市场{current['market']}，"
                f"保留当前参考图编号与用途，匹配{current['size']}静态画布。"
                f"本页修改要求：{rewrite or '无，使用当前大纲'}。"
            )})
        return {"pages": result}


def model_config():
    return {
        "ok": True, "fixture": True, "products": [],
        "aiImage": {
            "enabled": True, "model": "mock-image-only", "models": ["mock-image-only"],
            "nodes": [{"id": "fixture-only", "name": "本地模拟"}], "nodeCount": 1, "maxCount": 1, "message": RENDER_DISABLED,
            "director": {"enabled": True, "configured": True, "model": "mock-director",
                         "activeModel": "mock-director", "requestedModel": "mock-director",
                         "modelChain": ["mock-director"], "fallbackModels": [],
                         "autoFallbackEnabled": False, "visionEnabled": True,
                         "source": "isolated-fixture", "shared": False},
        },
    }


def seed_project(name: str, partial: bool = False):
    """Seed only the patched temporary store; no real model is involved."""
    from PIL import Image, ImageDraw

    picture = Image.new("RGB", (180, 180), "#f5f1e9")
    draw = ImageDraw.Draw(picture)
    draw.rounded_rectangle((46, 25, 132, 153), 16, fill="#d96252", outline="#24363d", width=3)
    draw.text((61, 78), "TEST ONLY", fill="white")
    stream = BytesIO()
    picture.save(stream, "PNG")
    current_form = {
        "product": name, "market": "DE", "main": 5, "detail": 5, "size": "750x1000",
        "points": ["便携杯身", "方便日常携带", "清晰展示杯身细节"],
        "style": "[测试] 象牙白、珊瑚红与深蓝，本土日常场景，分层排版",
        "discount": "[测试] 20% OFF", "codText": "[TEST] Nachnahme", "allowPromo": True,
    }
    upload = SimpleNamespace(filename="fixture-reference.png", file=BytesIO(stream.getvalue()))
    try:
        project = atelier.save_project_upload({"form": json.dumps(current_form, ensure_ascii=False), "referencesMode": "replace"}, {"reference0": upload}, ACTOR)["project"]
    finally:
        upload.file.close()
    plan = normalize_outline(PreviewDirector.outline({"form": project["form"]}), project["form"])
    raw_pages = PreviewDirector.pages({"form": project["form"], "outline": plan["outline"]})["pages"]
    pages = []
    for raw, entry in zip(raw_pages, plan["outline"]):
        page = normalize_page(raw, entry, project["form"])
        page["executionPrompt"] = compile_execution_prompt(project["form"], plan["masterPrompt"], page, project["references"])
        page["promptSource"] = "fixture"
        pages.append(page)
    with atelier._LOCK:
        owner = atelier._owner(ACTOR)
        document = atelier._read(owner, project["id"])
        version = atelier._current_version(document, project["revision"])
        version.update(plan)
        version["suitePages"] = pages[:5] if partial else pages
        version["status"] = "partial" if partial else "complete"
        version["progress"] = {"stage": version["status"], "completed": len(version["suitePages"]), "total": 10}
        version["error"] = "[测试模拟] 第二批中断，前5页已保存；可点击继续生成。" if partial else ""
        version["director"] = {"model": "mock-director", "activeModel": "mock-director", "requestedModel": "mock-director", "status": "ok", "stage": "fixture", "fallbackUsed": False}
        atelier._write(owner, document)
    return project["id"]


class PreviewRenderer:
    """Synthetic saved PNG outputs only; never imports or calls live providers."""
    def __init__(self):
        self.jobs = {}
        self.lock = threading.RLock()

    def start(self, project_id, payload, actor):
        with self.lock:
            spec = atelier.get_render_spec(project_id, payload["revision"], payload["pageNumber"], actor)
            key = payload.get("requestKey", "fixture")
            found = self.find(project_id, payload, actor)
            if found:
                return found
            job_id = "FIXTURE-" + uuid.uuid4().hex[:12]
            self.jobs[job_id] = {"projectId": project_id, "revision": payload["revision"], "pageNumber": payload["pageNumber"], "requestKey": key, "ready": time.monotonic() + .25, "spec": spec, "result": None}
            return {"ok": True, "pending": True, "status": "running", "jobId": job_id, "requestKey": key}

    def find(self, project_id, payload, actor):
        with self.lock:
            for job_id, job in self.jobs.items():
                if job["projectId"] == project_id and job["requestKey"] == payload.get("requestKey", "fixture"):
                    return self.get(project_id, job_id, actor, job["requestKey"])
        return None

    def get(self, project_id, job_id, actor, request_key=""):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job or job["projectId"] != project_id:
                return None
            if time.monotonic() < job["ready"]:
                return {"ok": True, "pending": True, "status": "running", "jobId": job_id, "requestKey": job["requestKey"]}
            if job["result"] is None:
                content = job["spec"]["referenceImages"][0][1]
                material = assets.archive_material(project_id, job["revision"], job["pageNumber"], {"id": "AI-" + uuid.uuid4().hex[:10].upper(), "name": "MOCK-TEST-ONLY.png", "model": "mock-image-only", "jobId": job_id}, actor, content)
                job["result"] = {"ok": True, "pending": False, "status": "success", "jobId": job_id, "requestKey": job["requestKey"], "materials": [material]}
            return job["result"]


class PreviewHandler(BaseHTTPRequestHandler):
    server_version = "AtelierIsolatedFixture/1.0"

    def send_payload(self, payload, status=HTTPStatus.OK):
        self.send_content(json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def send_content(self, content, mime, status=HTTPStatus.OK):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Atelier-Fixture", "true")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(content)

    def not_found(self):
        self.send_payload({"ok": False, "fixture": True, "error": "隔离测试服务：此路由不可用，不能访问真实 SKU Board 数据。"}, HTTPStatus.NOT_FOUND)

    def guarded(self, callback):
        try:
            callback()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except PermissionError as exc:
            self.send_payload({"ok": False, "fixture": True, "error": str(exc)}, HTTPStatus.FORBIDDEN)
        except (ValueError, TypeError, KeyError) as exc:
            self.send_payload({"ok": False, "fixture": True, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self.send_payload({"ok": False, "fixture": True, "error": f"测试夹具异常：{type(exc).__name__}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self.guarded(self.read_route)

    def read_route(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in STATIC_PATHS:
            relative, mime = STATIC_PATHS[path]
            content = (STATIC_DIR / relative).read_bytes()
            if path == "/cod-prompt-generator.html":
                content = content.replace(b"<title>", "<title>[隔离验收 / MOCK] ".encode("utf-8"), 1)
                banner = '<aside role="note" style="padding:12px 20px;background:#24363d;color:#fff8ed;font:700 13px/1.6 sans-serif;text-align:center">隔离验收服务 · mock-director 模拟输出 · 临时数据 · 禁用真实生图 · 不访问真实商品库</aside>'
                content = content.replace(b"<body>", ("<body>" + banner).encode("utf-8"), 1)
            self.send_content(content, mime)
        elif path == "/api/sku-board/ai-image-config":
            self.send_payload(model_config())
        elif path == "/api/sku-board/session":
            self.send_payload({"ok": True, "fixture": True, "user": ACTOR, "users": [ACTOR]})
        elif path == PREFIX:
            self.send_payload(atelier.list_projects(ACTOR))
        elif path.startswith(PREFIX + "/"):
            parts = path[len(PREFIX) + 1:].strip("/").split("/")
            revision = parse_qs(parsed.query).get("revision", [None])[0]
            if len(parts) == 1:
                self.send_payload(atelier.get_project(parts[0], ACTOR, revision=revision))
            elif len(parts) == 2 and parts[1] == "render-queues":
                self.send_payload(queues.list_queues(parts[0], ACTOR, revision))
            elif len(parts) == 3 and parts[1] == "assets":
                content, mime = assets.read_asset(parts[0], parts[2], ACTOR, revision)
                self.send_content(content, mime)
            elif len(parts) == 2 and parts[1] == "images.zip":
                stream, _filename = assets.image_zip(parts[0], revision, ACTOR)
                with stream:
                    self.send_content(stream.read(), "application/zip")
            elif len(parts) == 3 and parts[1] == "references":
                content, mime = atelier.read_reference(parts[0], parts[2], ACTOR, revision=revision)
                self.send_content(content, mime)
            else:
                self.not_found()
        else:
            self.not_found()

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 1024 * 1024:
            raise ValueError("测试请求体须在 1MB 以内")
        result = json.loads(self.rfile.read(length).decode("utf-8-sig"))
        if not isinstance(result, dict):
            raise ValueError("测试请求体须为 JSON 对象")
        return result

    def read_upload(self):
        length = int(self.headers.get("Content-Length", "0"))
        content_type = self.headers.get("Content-Type", "")
        if not 0 < length <= 16 * 1024 * 1024 or not content_type.lower().startswith("multipart/form-data"):
            raise ValueError("测试上传须为 multipart/form-data，且不超过 16MB")
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type, "CONTENT_LENGTH": str(length)},
                                keep_blank_values=True)
        fields, files = {}, {}
        for key in form.keys():
            item = form[key]
            if isinstance(item, list):
                raise ValueError("测试上传不接受重复字段")
            if getattr(item, "filename", ""):
                files[key] = item
            else:
                fields[key] = item.value
        return form, fields, files

    def do_POST(self):
        self.guarded(self.write_route)

    def write_route(self):
        path = urlparse(self.path).path
        origin = self.headers.get("Origin")
        if origin and origin != f"http://127.0.0.1:{self.server.server_port}":
            raise PermissionError("测试服务仅接受本地同源操作")
        if path == PREFIX + "/upload":
            form, fields, files = self.read_upload()
            try:
                self.send_payload(atelier.save_project_upload(fields, files, ACTOR))
            finally:
                for item in files.values():
                    item.file.close()
        elif path.startswith(PREFIX + "/"):
            parts = path[len(PREFIX) + 1:].strip("/").split("/")
            if len(parts) == 4 and parts[1] == "render-queues" and parts[3] in {"resume", "cancel"}:
                action = queues.resume_queue if parts[3] == "resume" else queues.cancel_queue
                self.send_payload(action(parts[0], parts[2], self.read_json(), ACTOR))
                return
            if len(parts) == 2 and parts[1] == "render":
                self.send_payload({"ok": False, "fixture": True, "error": RENDER_DISABLED}, HTTPStatus.FORBIDDEN)
                return
            actions = {"generate": atelier.start_generation, "cancel": atelier.cancel_generation, "edit-page": atelier.edit_page,
                       "review": atelier.review_project, "render-queue": queues.start_queue, "archive-images": assets.archive_existing}
            if len(parts) == 2 and parts[1] in actions:
                self.send_payload(actions[parts[1]](parts[0], self.read_json(), ACTOR))
            else:
                self.not_found()
        else:
            self.not_found()


@contextmanager
def preview_server(port=8795, delay=0.2, seed=True):
    """Tests may pass port=0 for a private ephemeral loopback port."""
    if port in {8793, 8794}:
        raise ValueError("测试夹具不能占用真实工作台端口 8793/8794")
    director = PreviewDirector(delay)
    fake_renderer = PreviewRenderer()
    with tempfile.TemporaryDirectory(prefix="cod-atelier-preview-") as directory:
        with patch.object(atelier, "_root", return_value=Path(directory)), patch.object(atelier, "_backend", return_value=director), patch.object(renderer, "render_settings", side_effect=lambda spec, payload: {key: payload.get(key) or spec["form"][key] for key in ("model", "quality", "generationProfile")}), patch.object(renderer, "start_render", side_effect=fake_renderer.start), patch.object(renderer, "find_render_job", side_effect=fake_renderer.find), patch.object(renderer, "get_render_job", side_effect=fake_renderer.get):
            server = ThreadingHTTPServer(("127.0.0.1", port), PreviewHandler)
            server.daemon_threads = True
            try:
                if seed:
                    seed_project("[测试] 完整10页 · 便携杯")
                    seed_project("[测试] 断点续传 · 便携杯", partial=True)
                yield server
            finally:
                director.stopping.set()
                with queues._LOCK:
                    for (owner, project_id, queue_id), event in list(queues._RUNS.items()):
                        record = queues._read(owner, project_id, queue_id)
                        record["cancelRequested"] = True
                        queues._write(record)
                        event.set()
                server.server_close()
                # Local mock calls return immediately on the stopping event.
                deadline = time.monotonic() + 2
                while (atelier._RUNS or queues._RUNS) and time.monotonic() < deadline:
                    time.sleep(0.02)


def main():
    parser = argparse.ArgumentParser(description="隔离 Atelier 浏览器验收：临时数据、mock-director、禁用真实生图")
    parser.add_argument("--port", type=int, default=8795)
    parser.add_argument("--delay", type=float, default=0.2, help="每次模拟 AI 调用的延迟，0–5 秒")
    parser.add_argument("--no-seed", action="store_true", help="不预置测试商品")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535 or not 0 <= args.delay <= 5:
        parser.error("端口须为 1024–65535，模拟延迟须为 0–5 秒")

    def interrupt(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupt)
    try:
        with preview_server(args.port, args.delay, not args.no_seed) as server:
            print(f"[ISOLATED FIXTURE / NO LIVE MODEL] http://127.0.0.1:{server.server_port}/cod-prompt-generator.html", flush=True)
            print("临时目录存档；Ctrl+C 退出并清理。真实 SKU 路由全部不可用，真实生图始终拒绝。", flush=True)
            server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("隔离测试服务已退出，临时数据已清理。", flush=True)


if __name__ == "__main__":
    main()
