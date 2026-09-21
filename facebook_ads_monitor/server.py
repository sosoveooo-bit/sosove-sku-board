from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from facebook_ads_monitor.backend import build_dashboard_payload, copy_campaigns, pause_campaigns, redact_token_text

STATIC_DIR = Path(__file__).resolve().parent / "static"


class FacebookAdsHandler(BaseHTTPRequestHandler):
    server_version = "FacebookAdsMonitor/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self.serve_static("index.html")
            return
        if parsed.path.startswith("/static/"):
            self.serve_static(parsed.path.removeprefix("/static/"))
            return
        if parsed.path == "/api/health":
            self.send_json({"ok": True, "service": "facebook-ads-monitor"})
            return
        if parsed.path == "/api/metrics":
            query = parse_qs(parsed.query)
            report = query.get("report", [""])[0] or None
            range_name = query.get("range", [""])[0] or query.get("preset", [""])[0] or None
            refresh = (query.get("refresh", ["0"])[0] or "").lower() in {"1", "true", "yes", "on"}
            try:
                self.send_json(build_dashboard_payload(report=report, range_name=range_name, refresh=refresh))
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_json({"ok": False, "error": "route not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/campaigns/pause":
            try:
                payload = self.read_json_body()
                self.send_json(
                    pause_campaigns(
                        payload.get("campaignIds") or payload.get("campaign_ids"),
                        confirm=payload.get("confirm"),
                    )
                )
            except ValueError as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                self.send_json(
                    {"ok": False, "error": redact_token_text(str(exc))},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
            return
        if parsed.path == "/api/campaigns/copy":
            try:
                payload = self.read_json_body()
                self.send_json(
                    copy_campaigns(
                        payload.get("campaignIds") or payload.get("campaign_ids"),
                        confirm=payload.get("confirm"),
                        rename_suffix=payload.get("renameSuffix") or payload.get("rename_suffix"),
                        status_option=str(payload.get("statusOption") or payload.get("status_option") or "PAUSED"),
                        deep_copy=bool(payload.get("deepCopy", True)),
                    )
                )
            except ValueError as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                self.send_json(
                    {"ok": False, "error": redact_token_text(str(exc))},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
            return
        self.send_json({"ok": False, "error": "route not found"}, status=HTTPStatus.NOT_FOUND)

    def read_json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        if length > 65536:
            raise ValueError("request body too large")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid json body") from exc
        if not isinstance(payload, dict):
            raise ValueError("json body must be an object")
        return payload

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
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[facebook-ads-monitor] {self.address_string()} - {format % args}")


def run(host: str, port: int) -> None:
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((host, port), FacebookAdsHandler)
    print(f"Facebook Ads Monitor running at http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Facebook ads monitoring dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
