"""Persistent owner-scoped cooperative cancellation; never claims to revoke provider work."""
import contextvars
import hashlib
import json
import re
import threading
import time
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

_context = contextvars.ContextVar('image_operation', default=None)
_lock = threading.RLock()
_path = None
_records = None


class OperationCancelled(ValueError):
    pass


def configure(data_dir):
    global _path, _records
    path = Path(data_dir) / 'ai_image_cancellations.json'
    if path != _path:
        _path, _records = path, None


def valid_id(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[a-f0-9]{32}', value))


def _key(owner, operation_id):
    return hashlib.sha256((owner + '\0' + operation_id).encode()).hexdigest()


def _load():
    global _records
    if _records is None:
        try:
            data = json.loads(_path.read_text(encoding='utf-8')) if _path and _path.exists() else {}
            _records = {k:v for k,v in data.items() if isinstance(v,(int,float)) and time.time()-v < 7*86400}
        except (ValueError,OSError):
            # Fail closed instead of silently losing durable cancellation markers.
            raise RuntimeError('取消记录读取异常，请检查后台日志')
    return _records


def cancel(owner, operation_id):
    if not owner or not valid_id(operation_id):
        raise ValueError('任务取消编号不正确')
    with _lock:
        records = dict(_load())
        records[_key(owner,operation_id)] = time.time()
        records = {k:v for k,v in records.items() if time.time()-v < 7*86400}
        if _path:
            _path.parent.mkdir(parents=True,exist_ok=True)
            temporary = _path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
            temporary.write_text(json.dumps(records),encoding='utf-8')
            temporary.replace(_path)
        global _records
        _records = records


def is_cancelled(owner, operation_id):
    if not operation_id:
        return False
    with _lock:
        return _key(owner,operation_id) in _load()


def enter(owner, operation_id):
    if operation_id and not valid_id(operation_id):
        raise ValueError('任务操作编号不正确')
    return _context.set((owner,operation_id) if operation_id else None)


def check():
    context = _context.get()
    if context and is_cancelled(*context):
        raise OperationCancelled('已取消后续处理；已提交上游的请求可能仍在执行')


def leave(token):
    _context.reset(token)


def post(client, *args, **kwargs):
    check()
    return client.post(*args, **kwargs)


class OperationExecutor(ThreadPoolExecutor):
    def submit(self, fn, /, *args, **kwargs):
        context = contextvars.copy_context()
        def execute():
            check()
            return fn(*args,**kwargs)
        return super().submit(context.run,execute)
