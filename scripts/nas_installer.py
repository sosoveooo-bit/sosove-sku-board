#!/usr/bin/env python3
"""Offline, transactional native installer for the SOSOVE NAS bundle.

This module performs no work on import. Its command adapter and small validation
functions are deliberately separate so tests never need root or a Linux host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


INSTALLER_ID = "sosove-nas-installer-v1"
SERVICE = "sosove-sku-board-nas.service"
SERVICE_USER = "sosove-board"
MARKER = ".sosove-nas-install.json"
MIN_FREE = 3 * 1024**3
UNIT_DIR = Path("/etc/systemd/system")
PRIVATE_MODE = 0o600
CONNECT_PREFIXES = ("CHATGPT2API_", "AI_DIRECTOR_", "ACORE_", "SHOPLINE_", "META_", "FB_")
ACTIVE_STATES = {"queued", "pending", "running", "submitting", "generating", "planning", "reviewing", "processing"}


class InstallError(RuntimeError):
    pass


def run_command(arguments: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None,
                timeout: int = 90, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """Never echo command arguments/environment: they may contain credentials."""
    try:
        result = subprocess.run(arguments, cwd=cwd, env=env, text=True, capture_output=True,
                                timeout=timeout, check=False, input=input_text)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstallError(f"{Path(arguments[0]).name} 执行异常：{type(exc).__name__}") from exc
    if check and result.returncode:
        raise InstallError(f"{Path(arguments[0]).name} 返回状态 {result.returncode}；旧版本与配置已保留")
    return result


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InstallError(f"JSON 文件校验失败：{path.name}") from exc


def regular_tree(root: Path):
    """Reject links/devices before copying or hashing any payload/data tree."""
    if root.is_symlink() or not root.is_dir():
        raise InstallError(f"目录类型不正确：{root}")
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            item = Path(directory) / name
            mode = item.lstat().st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise InstallError(f"目录包含链接或特殊文件：{item.relative_to(root)}")
            if stat.S_ISREG(mode):
                yield item


def validate_manifest(source: Path) -> dict[str, Any]:
    source = source.absolute()
    manifest = read_json(source / "manifest.json")
    if not isinstance(manifest, dict):
        raise InstallError("安装清单格式不正确")
    release_id = str(manifest.get("releaseId", ""))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", release_id):
        raise InstallError("发行版编号不正确")
    if manifest.get("arch") != "aarch64" or manifest.get("python") != "3.11":
        raise InstallError("安装包需要 aarch64 / Python 3.11 发行版本")
    records = manifest.get("files")
    if not isinstance(records, list) or not records or len(records) > 100000:
        raise InstallError("安装清单缺少文件列表")
    expected: set[str] = set()
    for entry in records:
        if not isinstance(entry, dict):
            raise InstallError("安装清单文件项格式不正确")
        name = str(entry.get("path", ""))
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or ".." in path.parts or "\\" in name
                or ":" in name or any(ord(c) < 32 for c in name) or path.as_posix() != name
                or name in expected or name == "manifest.json"):
            raise InstallError("安装清单存在重复或越界路径")
        if path.parts[0] not in {"app", "wheels", "installer"}:
            raise InstallError("安装清单包含未知顶层目录")
        expected.add(name)
        digest = str(entry.get("sha256", ""))
        size = entry.get("size")
        if (not re.fullmatch(r"[0-9a-f]{64}", digest) or isinstance(size, bool)
                or not isinstance(size, int) or size < 0):
            raise InstallError("安装清单缺少有效校验值")
    actual = {str(path.relative_to(source).as_posix()) for path in regular_tree(source)}
    if actual != expected | {"manifest.json"}:
        raise InstallError("安装文件与清单不一致；请重新取得完整安装包")
    for entry in records:
        target = source / entry["path"]
        if target.stat().st_size != entry["size"]:
            raise InstallError(f"安装文件大小校验失败：{entry['path']}")
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != entry["sha256"]:
            raise InstallError(f"安装文件哈希校验失败：{entry['path']}")
    for required in ("app/sku_board/server.py", "app/sku_board/backend.py", "app/shopline_monitor/backend.py"):
        if required not in expected:
            raise InstallError(f"安装包缺少必要组件：{required}")
    wheels = [entry["path"] for entry in records if entry["path"].startswith("wheels/")]
    if not wheels or any(not name.endswith(".whl") for name in wheels):
        raise InstallError("安装包缺少离线 wheel 依赖")
    return manifest


def validate_target(raw: str | Path) -> Path:
    value = str(raw)
    if any(ord(c) < 32 for c in value) or "\\" in value or "$" in value or "`" in value:
        raise InstallError("安装目录含有不支持的特殊字符")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise InstallError("请指定NAS数据盘上的绝对安装路径")
    forbidden = ("/bin", "/boot", "/dev", "/etc", "/lib", "/lib64", "/proc", "/run", "/sbin", "/sys", "/usr", "/tmp", "/var", "/root", "/home")
    normalized = path.as_posix().rstrip("/")
    if not normalized or normalized in {"/", "/root", "/home", "/mnt", "/media", "/opt", "/data"}:
        raise InstallError("安装目标应为数据盘里的专用子目录")
    if any(normalized == root or normalized.startswith(root + "/") for root in forbidden):
        raise InstallError("安装目录应避开系统目录")
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise InstallError("安装目录及父级应使用真实目录，避免符号链接")
        if part.exists() and not part.is_dir():
            raise InstallError("安装路径被普通文件占用")
    if path.exists() and any(path.iterdir()) and not (path / MARKER).is_file():
        raise InstallError("目标目录已有其他文件；请选择新的专用目录")
    return path


def nearest_existing(path: Path) -> Path:
    while not path.exists():
        if path == path.parent:
            raise InstallError("安装目录没有有效父级")
        path = path.parent
    return path


def check_storage(root: Path, required_bytes: int = MIN_FREE) -> None:
    anchor = nearest_existing(root)
    if anchor.stat().st_dev == Path("/").stat().st_dev:
        raise InstallError("请放到独立NAS数据盘：当前目标仍属于系统根文件系统")
    options = run_command(["findmnt", "--noheadings", "--raw", "--output", "OPTIONS", "--target", str(anchor)]).stdout.strip()
    if not options or "noexec" in options.split(",") or "ro" in options.split(","):
        raise InstallError("目标数据盘需要读写及执行权限（rw、exec）")
    if shutil.disk_usage(anchor).free < max(MIN_FREE, required_bytes):
        raise InstallError("目标数据盘空闲空间不足，请至少预留3 GiB及完整升级备份空间")


def check_platform() -> None:
    if platform.system() != "Linux" or platform.machine().lower() not in {"aarch64", "arm64"}:
        raise InstallError("此安装包面向 Linux aarch64 NAS")
    if sys.version_info[:2] != (3, 11):
        raise InstallError("请使用 Python 3.11 执行安装器")
    try:
        release = dict(line.split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
        version = int(release.get("VERSION_ID", "").strip('"').split(".")[0])
    except (OSError, ValueError) as exc:
        raise InstallError("读取Debian系统版本失败") from exc
    if release.get("ID", "").strip('"') != "debian" or version < 12:
        raise InstallError("此安装包要求 Debian 12 或更新的Debian系统")
    if not Path("/run/systemd/system").is_dir() or not shutil.which("systemctl"):
        raise InstallError("此安装方式要求systemd服务管理器")


def systemd_quote(value: str | Path) -> str:
    value = str(value)
    if any(ord(c) < 32 for c in value):
        raise InstallError("systemd参数含控制字符")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%") + '"'


def env_quote(value: str) -> str:
    if "\x00" in value or "\n" in value or "\r" in value:
        raise InstallError("配置值需要保持单行")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_private_config(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    if path.is_symlink() or not path.is_file():
        raise InstallError("私有配置应为普通文件")
    if path.stat().st_mode & 0o077:
        raise InstallError("请先执行 chmod 600 保护私有配置文件")
    if path.stat().st_size > 1024 * 1024:
        raise InstallError("私有配置文件过大")
    allowed: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not key.startswith(CONNECT_PREFIXES):
            continue
        if key.endswith(("_PATH", "_DIR", "_ROOT", "_SCRIPT", "_FILE")):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
            value = value[1:-1]
        if re.search(r"(?:^|[\s=;])(?:[A-Za-z]:[\\/]|\\\\)", value) or any(ord(c) < 32 for c in value):
            continue
        if value:
            allowed[key] = value
    return allowed


def fresh_environment(root: Path, imported: dict[str, str], password: str, encryption_key: str) -> dict[str, str]:
    values = dict(imported)
    has_image_nodes = any(values.get(name) for name in ("CHATGPT2API_BASE_URL", "CHATGPT2API_BASE_URLS", "CHATGPT2API_NODES_JSON"))
    if not has_image_nodes:
        values["CHATGPT2API_NODES_JSON"] = '[{"id":"setup-required","enabled":false}]'
        values["CHATGPT2API_HEALTH_MONITOR_ENABLED"] = "false"
    else:
        values.setdefault("CHATGPT2API_HEALTH_MONITOR_ENABLED", "true")
    if not (values.get("AI_DIRECTOR_API_BASE_URL") and values.get("AI_DIRECTOR_API_KEY")):
        values["AI_DIRECTOR_ENABLED"] = "false"
    values.update({
        "SKU_BOARD_DATA_DIR": str(root / "shared/data"),
        "COD_ATELIER_DATA_DIR": str(root / "shared/data/cod_prompt_atelier"),
        "SKU_BOARD_ADMIN_PASSWORD": password,
        "SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY": encryption_key,
        "OPEN_IMAGE_PROMPTS_ROOT": str(root / "current/app/open-image-prompts"),
        "LINKFOX_CLOTH_SKILL_ROOT": str(root / "current/app/vendor/linkfox-cloth-skill"),
        "TMPDIR": str(root / "shared/tmp"),
        "HOME": str(root / "shared"),
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1", "PYTHONUTF8": "1",
        "TZ": "Asia/Shanghai",
        "CHATGPT2API_IMAGE_MODEL": "gpt-image-2.5-sunburst",
        "CHATGPT2API_PANEL_MAX_ACTIVE_REQUESTS": "2", "CHATGPT2API_PANEL_MAX_ACTIVE_PER_USER": "1",
        "CHATGPT2API_IMAGE_TASK_BATCH_SIZE": "1", "CHATGPT2API_IMAGE_MAX_BATCH": "1",
        "CHATGPT2API_HEDGE_NODE_COUNT": "1", "ACORE_IMAGE_MAX_WORKERS": "1",
        "AI_DIRECTOR_JP25_REFINEMENT_WORKERS": "1", "AI_IMAGE_MEMORY_CACHE_MB": "64",
        "AI_IMAGE_OUTPUT_TTL_SECONDS": "604800",
        "AI_IMAGE_JAPANESE_FONT_PATH": "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    })
    return values


def write_atomic(path: Path, content: bytes, mode: int = PRIVATE_MODE) -> None:
    if path.is_symlink():
        raise InstallError(f"文件目标为符号链接：{path}")
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_environment(path: Path, values: dict[str, str]) -> bool:
    """Existing deployment settings are deliberately byte-for-byte immutable."""
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise InstallError("现有配置文件类型异常")
        return False
    text = "# NAS runtime settings; keep this file private.\n" + "".join(f"{key}={env_quote(value)}\n" for key, value in sorted(values.items()))
    write_atomic(path, text.encode("utf-8"))
    return True


def make_fresh_board(backend: Any, password: str) -> dict[str, Any]:
    users = []
    for seed in backend.DEFAULT_USER_SEEDS:
        username, name, role, _old_password = seed
        user = backend.build_auth_user(username, name, role, password if username == "admin" else secrets.token_urlsafe(32))
        user["active"] = username == "admin"
        users.append(user)
    if not any(user.get("username") == "admin" for user in users):
        raise InstallError("账号初始化组件缺少管理员定义")
    timestamp = backend.now_iso()
    return {"users": users, "items": [], "designTasks": [], "adLaunches": [], "createdAt": timestamp, "updatedAt": timestamp}


def active_work(data: Path) -> list[str]:
    """Read only durable jobs/projects; corrupt stores block an upgrade."""
    active: list[str] = []
    jobs = data / "ai_image_jobs.json"
    if jobs.exists():
        payload = read_json(jobs)
        records = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(records, (dict, list)):
            raise InstallError("任务记录结构异常，请在面板中检查后再升级")
        for job in records.values() if isinstance(records, dict) else records:
            if not isinstance(job, dict):
                raise InstallError("任务记录存在异常项目")
            if job.get("status") in ACTIVE_STATES:
                active.append("image-job")
    atelier = data / "cod_prompt_atelier"
    if atelier.exists():
        for file in regular_tree(atelier):
            if file.suffix != ".json" or not (file.name == "project.json" or file.parent.name == "render-queues"):
                continue
            payload = read_json(file)
            if not isinstance(payload, dict):
                raise InstallError("工作台任务记录结构异常")
            if file.parent.name == "render-queues":
                if payload.get("status") in ACTIVE_STATES:
                    active.append("render-queue")
            else:
                versions = payload.get("revisions", payload.get("versions", {}))
                if isinstance(versions, dict):
                    versions = list(versions.values())
                if not isinstance(versions, list):
                    raise InstallError("工作台版本记录结构异常")
                if any(isinstance(item, dict) and item.get("status") in ACTIVE_STATES for item in versions):
                    active.append("director-plan")
    return active


def unit_text(root: Path, port: int) -> str:
    q = systemd_quote
    return f"""# Managed-By: {INSTALLER_ID}
# Installation-Root: {root}
[Unit]
Description=SOSOVE SKU Board (NAS)
After=network-online.target
Wants=network-online.target
RequiresMountsFor={q(root)}
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Type=simple
User={SERVICE_USER}
Group={SERVICE_USER}
WorkingDirectory={q(root / 'current/app')}
EnvironmentFile={q(root / 'config/runtime.env')}
ExecStart={q(root / 'current/.venv/bin/python')} -m sku_board.server --host 0.0.0.0 --port {port} --skip-startup-cleanup
Restart=on-failure
RestartSec=5
TimeoutStopSec=45
UMask=0077
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths={q(root / 'shared')}
CapabilityBoundingSet=
AmbientCapabilities=
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
LockPersonality=yes
TasksMax=128
LimitNOFILE=4096
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sosove-sku-board-nas

[Install]
WantedBy=multi-user.target
"""


def cleanup_unit_text(root: Path) -> str:
    q = systemd_quote
    # Run the same protected application process with its own lock/age checks.
    return f"""# Managed-By: {INSTALLER_ID}
# Installation-Root: {root}
[Unit]
Description=Prune expired temporary SOSOVE NAS images
RequiresMountsFor={q(root)}
After=sosove-sku-board-nas.service
[Service]
Type=oneshot
User={SERVICE_USER}
Group={SERVICE_USER}
WorkingDirectory={q(root / 'current/app')}
EnvironmentFile={q(root / 'config/runtime.env')}
ExecStart={q(root / 'current/.venv/bin/python')} -c "from sku_board.backend import prune_ai_image_output_files; prune_ai_image_output_files(force=True)"
UMask=0077
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths={q(root / 'shared')}
CapabilityBoundingSet=
"""


def timer_text(root: Path) -> str:
    return f"""# Managed-By: {INSTALLER_ID}
# Installation-Root: {root}
[Unit]
Description=Hourly SOSOVE NAS temporary-image cleanup
[Timer]
OnBootSec=10min
OnUnitActiveSec=1h
Persistent=true
Unit=sosove-sku-board-nas-cleanup.service
[Install]
WantedBy=timers.target
"""


class Installer:
    def __init__(self, source: Path, root: Path, port: int, config_file: Path | None = None):
        self.source = source.absolute()
        self.root = root
        self.port = port
        self.config_file = config_file
        self.manifest: dict[str, Any] = {}
        self.marker: dict[str, Any] | None = None
        self.uid = self.gid = -1

    @property
    def units(self) -> dict[Path, bytes]:
        return {
            UNIT_DIR / SERVICE: unit_text(self.root, self.port).encode(),
            UNIT_DIR / "sosove-sku-board-nas-cleanup.service": cleanup_unit_text(self.root).encode(),
            UNIT_DIR / "sosove-sku-board-nas-cleanup.timer": timer_text(self.root).encode(),
        }

    def systemctl(self, *arguments: str, check: bool = True) -> str:
        return run_command(["systemctl", *arguments], check=check).stdout.strip()

    def service_active(self) -> bool:
        return self.systemctl("is-active", SERVICE, check=False) == "active"

    def preflight(self) -> None:
        check_platform()
        self.root = validate_target(self.root)
        if not 1024 <= self.port <= 65535:
            raise InstallError("面板端口范围为1024至65535")
        self.manifest = validate_manifest(self.source)
        marker_path = self.root / MARKER
        if marker_path.exists():
            if marker_path.is_symlink():
                raise InstallError("安装标记应为普通文件")
            value = read_json(marker_path)
            if not isinstance(value, dict) or value.get("installer") != INSTALLER_ID or value.get("root") != str(self.root):
                raise InstallError("安装标记与目标目录不匹配")
            self.marker = value
        for path in self.units:
            if path.exists() or path.is_symlink():
                if path.is_symlink() or not path.is_file():
                    raise InstallError("已有systemd服务路径类型冲突")
                unit = path.read_text(encoding="utf-8")
                if (not self.marker or f"# Managed-By: {INSTALLER_ID}\n" not in unit
                        or f"# Installation-Root: {self.root}\n" not in unit):
                    raise InstallError("同名systemd服务属于其他安装，已保留原服务")
        fragment = self.systemctl("show", SERVICE, "--property=FragmentPath", "--value", check=False)
        if fragment and Path(fragment) != UNIT_DIR / SERVICE:
            raise InstallError("systemd同名服务来源冲突")
        estimate = sum(entry["size"] for entry in self.manifest["files"]) * 2 + 512 * 1024**2
        for directory in (self.root / "config", self.root / "shared/data"):
            if directory.exists():
                estimate += sum(path.stat().st_size for path in regular_tree(directory))
        check_storage(self.root, estimate)
        listeners = run_command(["ss", "-H", "-ltnp", f"sport = :{self.port}"], check=True).stdout
        if listeners.strip():
            main_pid = self.systemctl("show", SERVICE, "--property=MainPID", "--value", check=False)
            pids = re.findall(r"\bpid=(\d+)", listeners)
            if not self.marker or not self.service_active() or not pids or set(pids) != {main_pid}:
                raise InstallError("面板端口已被其他进程使用，请指定新的--port")
        if self.marker and self.config_file:
            raise InstallError("升级会保留现有runtime.env；--config-file仅用于首次安装")
        parse_private_config(self.config_file)
        if self.marker:
            self.assert_idle()

    def assert_idle(self) -> None:
        if active_work(self.root / "shared/data"):
            raise InstallError("面板仍有生图或导演任务，请完成或在面板中取消后再升级")
        if self.service_active():
            connections = run_command(["ss", "-H", "-tn", "state", "established", f"sport = :{self.marker.get('port', self.port) if self.marker else self.port}"], check=True).stdout
            if connections.strip():
                raise InstallError("面板仍有连接正在处理，请稍后再升级")

    def ensure_layout(self) -> None:
        for directory in (self.root, self.root / "releases", self.root / "config", self.root / "backups", self.root / "shared"):
            directory.mkdir(mode=0o755, parents=True, exist_ok=True)
        for directory in (self.root / "config", self.root / "backups"):
            directory.chmod(0o700)
        if self.marker is None:
            self.marker = {"installer": INSTALLER_ID, "root": str(self.root), "phase": "prepared", "port": self.port}
            write_atomic(self.root / MARKER, json.dumps(self.marker).encode())
        import pwd
        import grp
        try:
            account = pwd.getpwnam(SERVICE_USER)
            if account.pw_dir != str(self.root / "shared") or account.pw_shell not in {"/usr/sbin/nologin", "/sbin/nologin", "/bin/false"}:
                raise InstallError("专用服务账号已属于其他安装")
        except KeyError:
            run_command(["useradd", "--system", "--user-group", "--no-create-home", "--home-dir", str(self.root / "shared"), "--shell", "/usr/sbin/nologin", SERVICE_USER])
            account = pwd.getpwnam(SERVICE_USER)
        self.uid, self.gid = account.pw_uid, account.pw_gid
        try:
            if grp.getgrnam(SERVICE_USER).gr_gid != self.gid:
                raise InstallError("专用服务账号的用户组与安装定义不同")
        except KeyError as exc:
            raise InstallError("专用服务用户组缺失") from exc
        for name in ("data", "tmp", "oip-cache"):
            path = self.root / "shared" / name
            path.mkdir(mode=0o700, exist_ok=True)
            os.chown(path, self.uid, self.gid)
            path.chmod(0o700)

    def build_release(self) -> Path:
        release = self.root / "releases" / self.manifest["releaseId"]
        # A failed/staged release is retained for diagnosis; a new directory makes
        # rerunning an installer deterministic without trusting partial contents.
        if release.exists() or release.is_symlink():
            release = release.with_name(release.name + "-" + uuid.uuid4().hex[:8])
        release.mkdir(mode=0o755)
        shutil.copytree(self.source / "app", release / "app")
        for path in [release / "app", *(release / "app").rglob("*")]:
            path.chmod(0o755 if path.is_dir() else 0o644)
        oip = release / "app/open-image-prompts/.oip"
        if oip.exists() or oip.is_symlink():
            raise InstallError("公共安装包包含OIP私有运行目录")
        if (release / "app/open-image-prompts").is_dir():
            oip.symlink_to(self.root / "shared/oip-cache", target_is_directory=True)
        environment = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": str(self.root / "shared"),
                       "TMPDIR": str(self.root / "shared/tmp"), "PYTHONDONTWRITEBYTECODE": "1", "PIP_CONFIG_FILE": os.devnull,
                       "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PYTHONUTF8": "1"}
        run_command([sys.executable, "-m", "venv", str(release / ".venv")], env=environment, timeout=180)
        python = release / ".venv/bin/python"
        run_command([str(python), "-m", "pip", "install", "--no-index", "--no-cache-dir", "--find-links", str(self.source / "wheels"),
                     "--only-binary=:all:", "Pillow>=10,<13", "requests>=2.31,<3", "cryptography>=42,<46"],
                    env=environment, timeout=300)
        smoke = dict(environment, SKU_BOARD_DATA_DIR=str(self.root / "shared/tmp/import-check"),
                     CHATGPT2API_NODES_JSON='[{"id":"setup-required","enabled":false}]',
                     CHATGPT2API_HEALTH_MONITOR_ENABLED="false", AI_DIRECTOR_ENABLED="false")
        run_command([str(python), "-c", "import cgi,sqlite3; import PIL,requests,cryptography; import sku_board.server; print('imports-ok')"],
                    cwd=release / "app", env=smoke, timeout=90)
        return release

    def initialize_fresh(self, release: Path) -> None:
        config = self.root / "config/runtime.env"
        board = self.root / "shared/data/sku_board.json"
        if config.exists():
            # A interrupted first install may have written env but not users.
            # Resume with the same admin secret rather than spawning weak seeds.
            if board.exists():
                return
            values = {}
            for line in config.read_text(encoding="utf-8").splitlines():
                if line.startswith("SKU_BOARD_ADMIN_PASSWORD="):
                    value = line.split("=", 1)[1].strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    values["SKU_BOARD_ADMIN_PASSWORD"] = value
            password = values.get("SKU_BOARD_ADMIN_PASSWORD", "")
            if not re.fullmatch(r"[A-Za-z0-9_-]{24,}", password):
                raise InstallError("首次安装记录未完成，请核对已保留的私有配置")
        else:
            if board.exists():
                raise InstallError("首次安装的账号数据已存在，请保留文件并检查安装目录")
            password = secrets.token_urlsafe(24)
            values = fresh_environment(self.root, parse_private_config(self.config_file), password, secrets.token_urlsafe(48))
            write_environment(config, values)
        login = self.root / "config/initial-login.txt"
        if not login.exists():
            write_atomic(login, ("管理员账号：admin\n首次密码：" + password + "\n登录后请在账号设置中更换密码。\n").encode("utf-8"))
        # Send credentials only through stdin, never argv or process output. The
        # installed backend remains the single source of its password schema.
        bootstrap = """import sys,json,os,importlib.util
from sku_board import backend
spec=importlib.util.spec_from_file_location('nas_bootstrap',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
payload=json.load(sys.stdin)
backend.save_board(module.make_fresh_board(backend,payload['password']))
os.chmod(backend.DATA_FILE,0o600)
"""
        env = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
               "HOME": str(self.root / "shared"), "SKU_BOARD_DATA_DIR": str(self.root / "shared/data"),
               "CHATGPT2API_NODES_JSON": '[{"id":"setup-required","enabled":false}]', "AI_DIRECTOR_ENABLED": "false"}
        run_command([str(release / ".venv/bin/python"), "-c", bootstrap, str(Path(__file__).resolve())],
                    input_text=json.dumps({"password": password}), env=env, cwd=release / "app", timeout=90)
        os.chown(board, self.uid, self.gid)

    def backup(self) -> Path:
        target = self.root / "backups" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
        target.mkdir(mode=0o700)
        for name, source in (("config", self.root / "config"), ("data", self.root / "shared/data")):
            # No symlinks are followed out of account-owned storage.
            list(regular_tree(source))
            shutil.copytree(source, target / name)
        return target

    def switch_current(self, release: Path) -> None:
        current = self.root / "current"
        if current.exists() and not current.is_symlink():
            raise InstallError("current 应为安装器管理的版本链接")
        temporary = self.root / (".current-" + uuid.uuid4().hex)
        temporary.symlink_to(release, target_is_directory=True)
        os.replace(temporary, current)

    def check_health(self) -> None:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(25):
            try:
                with opener.open(f"http://127.0.0.1:{self.port}/api/health", timeout=2) as response:
                    if response.status == 200:
                        payload = json.loads(response.read(1024 * 1024))
                        if isinstance(payload, dict) and payload.get("ok") is True:
                            return
            except (OSError, ValueError):
                pass
            time.sleep(1)
        raise InstallError("新版本健康检查未通过，开始恢复上一版本")

    def activate(self, release: Path, *, fresh: bool) -> None:
        current = self.root / "current"
        old_release = current.resolve() if current.is_symlink() else None
        if old_release is not None and old_release.parent != self.root / "releases":
            raise InstallError("当前版本链接越出专用发行目录")
        old_units = {path: path.read_bytes() if path.exists() else None for path in self.units}
        old_marker = (self.root / MARKER).read_bytes()
        was_active = self.service_active()
        backup = None
        stopped = False
        try:
            if not fresh:
                self.assert_idle()
            self.systemctl("stop", "sosove-sku-board-nas-cleanup.timer", check=False)
            self.systemctl("stop", "sosove-sku-board-nas-cleanup.service", check=False)
            if was_active:
                self.systemctl("stop", SERVICE)
                stopped = True
            if not fresh:
                backup = self.backup()
            for path, content in self.units.items():
                write_atomic(path, content, 0o644)
            self.switch_current(release)
            self.systemctl("daemon-reload")
            self.systemctl("start", SERVICE)
            self.check_health()
            self.systemctl("enable", SERVICE)
            self.systemctl("enable", "--now", "sosove-sku-board-nas-cleanup.timer")
            self.marker = {"installer": INSTALLER_ID, "root": str(self.root), "phase": "installed", "port": self.port,
                           "release": release.name, "previousRelease": old_release.name if old_release else "", "updatedAt": datetime.now(timezone.utc).isoformat()}
            write_atomic(self.root / MARKER, json.dumps(self.marker, ensure_ascii=False, indent=2).encode())
        except Exception as original:
            self.systemctl("stop", SERVICE, check=False)
            self.systemctl("stop", "sosove-sku-board-nas-cleanup.timer", check=False)
            if old_release is not None:
                self.switch_current(old_release)
            elif current.is_symlink():
                current.unlink()
            for path, content in old_units.items():
                if content is not None:
                    write_atomic(path, content, 0o644)
                elif path.exists() and path.read_text(encoding="utf-8").startswith(f"# Managed-By: {INSTALLER_ID}\n"):
                    path.unlink()
            write_atomic(self.root / MARKER, old_marker)
            self.systemctl("daemon-reload", check=False)
            # Runtime data is never overwritten by rollback: completed images or
            # task receipts written during startup remain valuable. The exact
            # pre-switch data snapshot is retained for explicit restoration.
            if was_active and old_release is not None:
                self.systemctl("start", SERVICE, check=False)
                self.systemctl("start", "sosove-sku-board-nas-cleanup.timer", check=False)
            suffix = f"；一致备份保留在 {backup}" if backup else "；新发行目录与诊断文件已保留"
            raise InstallError(f"升级未激活，已恢复原版本服务和配置{suffix}") from original

    def execute(self, *, check_only: bool = False) -> None:
        self.preflight()
        if check_only:
            print("检查通过：平台、安装包、数据盘空间、端口及现有服务均满足要求。未修改系统。")
            return
        if os.geteuid() != 0:
            raise InstallError("安装阶段请使用sudo或root运行")
        fresh = self.marker is None or self.marker.get("phase") != "installed"
        self.ensure_layout()
        release = self.build_release()
        if fresh:
            self.initialize_fresh(release)
        self.activate(release, fresh=fresh)
        print(f"安装完成：NAS_IP:{self.port}；服务：{SERVICE}")
        print(f"管理员首次登录信息：{self.root / 'config/initial-login.txt'}（仅root读取）")
        print(f"私有模型配置：{self.root / 'config/runtime.env'}；升级保留账号、密钥及图片。")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SOSOVE Debian aarch64 NAS离线安装器")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--dir", required=True, type=Path, dest="directory")
    parser.add_argument("--port", type=int, default=8793)
    parser.add_argument("--config-file", type=Path)
    parser.add_argument("--check", action="store_true", help="仅检查，不修改服务或数据")
    args = parser.parse_args(argv)
    try:
        Installer(args.source, args.directory, args.port, args.config_file).execute(check_only=args.check)
        return 0
    except (InstallError, OSError, subprocess.SubprocessError) as exc:
        print(f"安装已暂停：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
