"""Independent loopback UI; fixed-origin allowlisted proxy to the existing engine."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import http.client
import json
import time
import sys
import logging
import uuid
import re
from plan_preview import text_fields, enrich_plan, load_engine, compile_existing_plan

ROOT = Path(__file__).parent
ALLOWED_HOSTS = {
    '127.0.0.1:8795', 'localhost:8795',
    'manage.sosove.ggff.net', 'manage.sosove.ggff.net:443',
}
ALLOWED_ORIGINS = {
    'http://127.0.0.1:8795', 'http://localhost:8795',
    'https://manage.sosove.ggff.net',
}
ALLOWED = {
    '/api/sku-board/session', '/api/sku-board/login',
    '/api/sku-board/ai-image-config', '/api/sku-board/ai-image-suite-plan-upload',
    '/api/sku-board/ad-launch-ai-image-edit',
    '/api/sku-board/studio-compile',
    '/api/sku-board/ai-image-cancel',
}


def compile_failure(exc):
    error_id = uuid.uuid4().hex[:12]
    logging.getLogger('studio.compiler').error('Local compilation failed; id=%s', error_id,
        exc_info=(type(exc), exc, exc.__traceback__))
    if isinstance(exc, ModuleNotFoundError):
        module = re.sub(r'[^\w.\-]', '', exc.name or 'unknown')[:80]
        code = 'COMPILER_DEPENDENCY_MISSING'
        message = f'本地编译器缺少依赖 {module}。请使用项目虚拟环境重启8795，再点“重试本地编译”，无需重新AI策划。'
    elif isinstance(exc, (ValueError, KeyError)):
        code = 'COMPILER_PLAN_INVALID'
        message = f'本地方案编译校验失败：{str(exc)[:200]}。方案已保留。'
    else:
        code = 'COMPILER_INTERNAL_ERROR'
        message = f'本地编译器异常（{type(exc).__name__}），请按错误编号检查服务日志，无需反复重新AI策划。'
    return {'studioCompiledReady':False, 'studioCompileError':message,
            'studioCompileErrorCode':code, 'studioCompileErrorId':error_id}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def dispatch(self):
        path = urlsplit(self.path).path
        if self.headers.get('Host') not in ALLOWED_HOSTS:
            self.send_error(403)
            return
        origin = self.headers.get('Origin')
        if origin and origin not in ALLOWED_ORIGINS:
            self.send_error(403)
            return
        if path == '/health':
            try:
                load_engine()
                health = {'ok':True,'service':'cod-chat-studio','compilerReady':True,
                    'projectVenv':Path(sys.prefix).resolve() == (ROOT.parent / '.venv').resolve(),
                    'pythonVersion':sys.version.split()[0]}
                self.reply(200, json.dumps(health).encode(), 'application/json')
            except Exception:
                self.reply(503, b'{"ok":false,"service":"cod-chat-studio","compilerReady":false}', 'application/json')
            return
        assets = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}
        assets['/company-layout.css'] = ('company-layout.css', 'text/css')
        assets['/workflow.js'] = ('workflow.js', 'text/javascript')
        assets['/workflow.css'] = ('workflow.css', 'text/css')
        assets['/history-menu.js'] = ('history-menu.js', 'text/javascript')
        assets['/history-menu.css'] = ('history-menu.css', 'text/css')
        if self.command == 'GET' and path in assets:
            name, mime = assets[path]
            self.reply(200, (ROOT / name).read_bytes(), mime + '; charset=utf-8')
            return
        if path not in ALLOWED and not path.startswith(('/api/sku-board/ai-image-jobs/', '/api/sku-board/ai-image-output/')):
            self.send_error(404)
            return
        conn = http.client.HTTPConnection('127.0.0.1', 8793, timeout=650)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 <= length <= 64 * 1024 * 1024:
                self.send_error(413)
                return
            body = self.rfile.read(length) if length else None
            headers = {k: self.headers[k] for k in ('Content-Type', 'Cookie') if self.headers.get(k)}
            if path == '/api/sku-board/studio-compile':
                if self.command != 'POST':
                    self.send_error(405)
                    return
                # Reuse engine authentication, but never send a planning/generation request.
                conn.request('GET', '/api/sku-board/session', headers={k:v for k,v in headers.items() if k == 'Cookie'})
                auth_response = conn.getresponse()
                auth = json.loads(auth_response.read())
                actor = auth.get('user')
                if auth_response.status != 200 or not actor:
                    self.reply(401, b'{"ok":false,"error":"Login required"}', 'application/json')
                    return
                if actor.get('role') not in {'admin','ops','selection','designer'}:
                    self.send_error(403)
                    return
                started = time.perf_counter()
                try:
                    if length > 4 * 1024 * 1024:
                        raise ValueError('编译请求超过4MB，请检查逐页方案')
                    data = json.loads(body or b'{}')
                    if not isinstance(data, dict):
                        raise ValueError('方案必须是JSON对象')
                    result = compile_existing_plan(data)
                except Exception as exc:
                    result = {'ok':True, **compile_failure(exc)}
                result['studioTimings'] = {'upstreamMs':0,'compileMs':round((time.perf_counter()-started)*1000),
                    'compileCacheHit':result.get('studioCompileCacheHit',False),'compileOnly':True}
                self.reply(200, json.dumps(result,ensure_ascii=False).encode(), 'application/json')
                return
            upstream_started = time.perf_counter()
            conn.request(self.command, self.path, body, headers)
            response = conn.getresponse()
            payload = response.read()
            upstream_ms = round((time.perf_counter() - upstream_started) * 1000)
            if self.command == 'POST' and path == '/api/sku-board/ai-image-suite-plan-upload' and response.status == 200:
                result = json.loads(payload)
                try:
                    result = enrich_plan(result, text_fields(self.headers.get('Content-Type', ''), body or b''))
                except Exception as exc:
                    result.update(compile_failure(exc))
                result['studioTimings'] = {'upstreamMs': upstream_ms, 'compileMs': result.get('studioCompileMs', 0),
                                          'compileCacheHit': result.get('studioCompileCacheHit', False)}
                payload = json.dumps(result, ensure_ascii=False).encode('utf-8')
            self.reply(response.status, payload, response.getheader('Content-Type', 'application/json'), response.getheader('Set-Cookie'))
        except Exception as e:
            self.reply(502, json.dumps({
                'ok': False,
                'status': 'error',
                'code': 'ENGINE_UNAVAILABLE',
                'error': '本地引擎连接中断。已提交的图片请先同步任务，不要重复提交。',
                'detail': str(e),
                'outcomeUncertain': True,
            }, ensure_ascii=False).encode(), 'application/json')
        finally:
            conn.close()

    def reply(self, status, body, mime, cookie=None):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass


if __name__ == '__main__':
    load_engine()  # Fail before opening a misleadingly healthy UI with missing dependencies.
    if '--check-compiler' in sys.argv:
        print(json.dumps({'ok':True,'compilerReady':True,'pythonVersion':sys.version.split()[0]}))
        raise SystemExit(0)
    print('COD Chat Studio http://127.0.0.1:8795/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8795), Handler).serve_forever()
