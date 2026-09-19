"""Owner-scoped durable artifacts and cross-process single-flight leases (stdlib)."""
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from .contracts import dump


class Busy(ValueError):
    pass


class Store:
    def __init__(self, data_dir):
        self.path = Path(data_dir) / 'visual_agent_state.sqlite3'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS artifacts (
                  owner TEXT NOT NULL, kind TEXT NOT NULL, key TEXT NOT NULL,
                  value TEXT NOT NULL, updated REAL NOT NULL,
                  PRIMARY KEY(owner,kind,key));
                CREATE TABLE IF NOT EXISTS leases (
                  owner TEXT NOT NULL, key TEXT NOT NULL, token TEXT NOT NULL,
                  expires REAL NOT NULL, PRIMARY KEY(owner,key));
            ''')

    @contextmanager
    def db(self):
        db = sqlite3.connect(str(self.path), timeout=20)
        try:
            db.execute('PRAGMA busy_timeout=20000')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, owner, kind, key):
        if not owner:
            raise ValueError('缺少账号归属')
        with self.db() as db:
            row = db.execute('SELECT value FROM artifacts WHERE owner=? AND kind=? AND key=?',
                             (owner, kind, key)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, owner, kind, key, value):
        if not owner:
            raise ValueError('缺少账号归属')
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO artifacts VALUES (?,?,?,?,?)',
                       (owner, kind, key, dump(value), time.time()))

    @contextmanager
    def lease(self, owner, key, seconds=900):
        token = uuid.uuid4().hex
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM leases WHERE expires < ?', (time.time(),))
            if db.execute('SELECT 1 FROM leases WHERE owner=? AND key=?', (owner, key)).fetchone():
                raise Busy('相同任务已在处理，已保留检查点；请稍后继续，不重复提交分析')
            db.execute('INSERT INTO leases VALUES (?,?,?,?)', (owner, key, token, time.time() + seconds))
        try:
            yield
        finally:
            with self.db() as db:
                db.execute('DELETE FROM leases WHERE owner=? AND key=? AND token=?', (owner, key, token))
