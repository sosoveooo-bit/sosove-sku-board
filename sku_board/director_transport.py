"""Director-only upload timeout; keep requests, TLS validation and existing APIs.

urllib3 uses the connect timeout on the socket until request upload finishes.
Large vision JSON must not inherit an 8-second TCP/TLS connection budget.
Pool/connection subclasses are scoped to this adapter, never patched globally.
"""
import socket
import ssl
import time

from requests.adapters import HTTPAdapter

from . import image_cancellation


class DirectorUploadTimeout(RuntimeError):
    """Request body did not finish sending; no model response was received."""


class _UploadTimeoutMixin:
    _director_write_timeout = 90.0
    _director_deadline = None
    _director_stats = None
    _upload_deadline = None

    def request(self, *args, **kwargs):
        # HTTPS pools normally connect in _validate_conn. HTTP and a new proxy
        # connection still use the original short connect timeout here.
        if self.sock is None:
            self.connect()
        original_timeout = self.timeout
        self._upload_deadline = time.monotonic() + self._director_write_timeout
        if self._director_deadline is not None:
            self._upload_deadline = min(self._upload_deadline, self._director_deadline)
        self.timeout = max(0.001, self._upload_deadline - time.monotonic())
        started = time.monotonic()
        try:
            result = super().request(*args, **kwargs)
            if self._director_stats is not None:
                self._director_stats.update(uploadComplete=True, uploadMs=round((time.monotonic() - started) * 1000))
            return result
        except (TimeoutError, ssl.SSLWantWriteError) as exc:
            self.close()
            raise DirectorUploadTimeout('director request upload timed out') from exc
        except BaseException:
            self.close()
            raise
        finally:
            self.timeout = original_timeout
            self._upload_deadline = None

    def send(self, data):
        if self._upload_deadline is None:
            return super().send(data)
        # Keep Content-Length framing. Splitting socket writes is not HTTP
        # chunked transfer, and does not alter JSON or the image bytes.
        chunks = (data[i:i + 65536] for i in range(0, len(data), 65536)) if isinstance(
            data, (bytes, bytearray, memoryview)) else (data,)
        for chunk in chunks:
            image_cancellation.check()
            remaining = self._upload_deadline - time.monotonic()
            if remaining <= 0:
                raise DirectorUploadTimeout('director request upload deadline reached')
            self.sock.settimeout(remaining)
            super().send(chunk)

    def getresponse(self):
        # The pool has switched to its read timeout by now. Also respect the
        # chain deadline after time already spent connecting/uploading.
        if self._director_deadline is not None:
            remaining = self._director_deadline - time.monotonic()
            if remaining <= 0:
                raise socket.timeout('director response deadline reached')
            self.timeout = min(self.timeout, remaining) if self.timeout is not None else remaining
        return super().getresponse()


class DirectorHTTPAdapter(HTTPAdapter):
    def __init__(self, write_timeout=90, deadline=None, stats=None):
        self.write_timeout = float(write_timeout)
        self.deadline = deadline
        self.stats = stats
        # No hidden HTTP-library retries of billable POST requests.
        super().__init__(max_retries=0)

    def _configure(self, manager):
        if getattr(manager, '_director_upload_configured', False):
            return
        attributes = {'_director_write_timeout': self.write_timeout,
                      '_director_deadline': self.deadline, '_director_stats': self.stats}
        pools = dict(manager.pool_classes_by_scheme)
        for scheme in ('http', 'https'):
            base_pool = pools[scheme]
            connection = type('Director' + scheme.upper() + 'Connection',
                              (_UploadTimeoutMixin, base_pool.ConnectionCls), attributes)
            pools[scheme] = type('Director' + scheme.upper() + 'Pool', (base_pool,), {'ConnectionCls': connection})
        manager.pool_classes_by_scheme = pools
        manager._director_upload_configured = True

    def init_poolmanager(self, *args, **kwargs):
        super().init_poolmanager(*args, **kwargs)
        self._configure(self.poolmanager)

    def proxy_manager_for(self, proxy, **kwargs):
        manager = super().proxy_manager_for(proxy, **kwargs)
        self._configure(manager)
        return manager
