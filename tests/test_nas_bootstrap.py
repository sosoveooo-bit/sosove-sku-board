"""Offline bootstrap contracts; all Linux/system tools are harmless local stubs."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "scripts" / "nas-bootstrap.sh.in"
BASH = (str(Path(r"C:\Program Files\Git\bin\bash.exe")) if os.name == "nt"
        else shutil.which("bash"))


def shell_path(path: Path) -> str:
    value = path.resolve().as_posix()
    if os.name == "nt":
        return "/" + value[0].lower() + value[2:]
    return value


@unittest.skipUnless(BASH and Path(BASH).is_file(), "Bash is required")
class NasBootstrapTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".run").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="nas-bootstrap-test-", dir=ROOT / ".run")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / "stub-bin"
        self.bin.mkdir()
        self.data = self.base / "NAS data"
        self.data.mkdir()
        self.system_calls = self.base / "system-calls.log"
        self.os_release = self.base / "os-release"
        # newline="\n" keeps the fixture LF-only: the bootstrap reads it with
        # `read`, so a CRLF file would make VERSION_ID "12\r" and look wrong.
        self.os_release.write_text('ID=debian\nVERSION_ID="12"\n', encoding="utf-8", newline="\n")
        self.env = os.environ.copy()
        self.env["PATH"] = str(self.bin) + os.pathsep + self.env.get("PATH", "")
        self.env["NAS_TEST_CALL_LOG"] = shell_path(self.system_calls)
        self.stub("uname", 'case "$1" in -s) echo Linux;; -m) echo "${NAS_TEST_ARCH:-aarch64}";; esac')
        self.stub("findmnt", '''if [[ "$*" == *MAJ:MIN* ]]; then
  if [[ "${@: -1}" == / || "${NAS_TEST_ROOT_DISK:-0}" == 1 ]]; then echo 0:1; else echo 0:2; fi
else echo "${NAS_TEST_MOUNT_OPTIONS:-rw,relatime}"; fi''')
        self.stub("df", '''free=${NAS_TEST_DATA_FREE:-8000000000}
[[ "${@: -1}" != / ]] || free=${NAS_TEST_ROOT_FREE:-1000000000}
printf 'Filesystem Blocks Used Available Capacity Mounted\nmock 9000000000 1 %s 1%% /mock\n' "$free"''')
        self.stub("dpkg-query", '[[ "${NAS_TEST_MISSING:-0}" != 1 ]] || exit 1; printf "ii "')
        self.stub("python3.11", "exec " + shlex.quote(shell_path(Path(sys.executable))) + ' "$@"')
        for name in ("apt-get", "systemctl", "useradd", "usermod", "chown"):
            self.stub(name, 'printf "%s\\n" "' + name + '" >> "$NAS_TEST_CALL_LOG"; exit 97')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\nset -eu\n" + body + "\n", encoding="utf-8", newline="\n")
        path.chmod(0o755)

    def package(self, *, entry=None, corrupt=False, core_exit=0):
        core = ("import json,os,sys\nprint('CORE_ARGS:'+json.dumps({"
                "'argv':sys.argv[1:],'tmp':os.environ.get('TMPDIR'),"
                "'pip':os.environ.get('PIP_CACHE_DIR')},ensure_ascii=False))\n"
                f"raise SystemExit({core_exit})\n")
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w:gz") as bundle:
            for name, content in (("installer/nas_installer.py", core.encode()),
                                  ("app/sku_board/example.txt", b"fixture"),
                                  ("manifest.json", b"{}")):
                member = tarfile.TarInfo(name)
                member.size, member.mode = len(content), 0o644
                bundle.addfile(member, io.BytesIO(content))
            if entry:
                member = tarfile.TarInfo(entry[0])
                member.type = entry[1]
                if member.issym() or member.islnk():
                    member.linkname = "../../outside"
                bundle.addfile(member, io.BytesIO(b""))
        payload = data.getvalue()
        header = TEMPLATE.read_text(encoding="utf-8")
        os_path = shlex.quote(shell_path(self.os_release))
        header = header.replace("[[ -r /etc/os-release ]]", "[[ -r " + os_path + " ]]")
        header = header.replace("done < /etc/os-release", "done < " + os_path)
        header = header.replace("__PAYLOAD_SHA256__", hashlib.sha256(payload).hexdigest())
        package = self.data / "sosove-nas-arm64.run"
        package.write_bytes(header.encode() + payload + (b"corrupt" if corrupt else b""))
        return package

    def run_package(self, *args, package=None, env=None):
        actual_env = self.env.copy()
        actual_env.update(env or {})
        command = [BASH, "-c", 'export PATH="$1:$PATH"; shift; source "$@"',
                   "nas-bootstrap-test", shell_path(self.bin), shell_path(package or self.package()), *args]
        result = subprocess.run(command,
                                env=actual_env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=30)
        self.assertFalse(self.system_calls.exists(), "A system-changing stub was called")
        return result

    def assert_no_stage(self):
        self.assertEqual(list(self.data.glob(".sosove-install.*")), [])

    def test_template_has_valid_bash_syntax(self):
        result = subprocess.run([BASH, "-n", shell_path(TEMPLATE)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_requires_no_platform_root_payload_or_dependencies(self):
        result = self.run_package("--help", env={"NAS_TEST_ARCH": "x86_64"}, package=TEMPLATE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--check", result.stdout)
        self.assertNotIn("CORE_ARGS:", result.stdout)
        self.assert_no_stage()

    def test_x86_vps_stops_before_unpacking(self):
        result = self.run_package("--check", env={"NAS_TEST_ARCH": "x86_64"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Architecture mismatch", result.stderr)
        self.assert_no_stage()

    def test_wrong_os_stops_before_unpacking(self):
        self.os_release.write_text('ID=debian\nVERSION_ID="11"\n', encoding="utf-8", newline="\n")
        result = self.run_package("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Debian 12 is required", result.stderr)
        self.assert_no_stage()

    def test_preflight_checks_root_volume_noexec_and_space(self):
        for env, expected in (({"NAS_TEST_ROOT_DISK": "1"}, "root filesystem"),
                              ({"NAS_TEST_MOUNT_OPTIONS": "rw,noexec"}, "noexec"),
                              ({"NAS_TEST_DATA_FREE": "3221225471"}, "3 GiB"),
                              ({"NAS_TEST_ROOT_FREE": "536870911"}, "512 MiB")):
            with self.subTest(env=env):
                result = self.run_package("--check", env=env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assert_no_stage()

    def test_check_reports_missing_packages_without_apt(self):
        result = self.run_package("--check", env={"NAS_TEST_MISSING": "1"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("python3.11-venv", result.stdout)
        self.assert_no_stage()

    def test_invalid_options_and_port_are_not_evaluated(self):
        for args in (("--port", "8793;touch HACKED"), ("--port", "0"),
                     ("--port", "65536"), ("--unknown",), ("--dir",)):
            with self.subTest(args=args):
                result = self.run_package(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("CORE_ARGS:", result.stdout)
        self.assertFalse((self.data / "HACKED").exists())
        self.assert_no_stage()

    def test_unsafe_install_directories_stop_before_unpacking(self):
        for target in ("relative/folder", "/", "/etc/sosove", "/var/lib/sosove",
                       shell_path(self.data) + "/../outside", shell_path(self.data) + "/newline\nfolder"):
            with self.subTest(target=target):
                result = self.run_package("--check", "--dir", target)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("CORE_ARGS:", result.stdout)
                self.assert_no_stage()

    def test_checksum_failure_stops_before_unpacking(self):
        result = self.run_package("--check", package=self.package(corrupt=True))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)
        self.assert_no_stage()

    def test_safe_check_invokes_core_with_default_data_volume_dir_then_cleans(self):
        result = self.run_package("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        info = json.loads(next(line.removeprefix("CORE_ARGS:") for line in result.stdout.splitlines()
                               if line.startswith("CORE_ARGS:")))
        argv = info["argv"]
        self.assertIn("--check", argv)
        self.assertEqual(argv[argv.index("--port") + 1], "8793")
        self.assertEqual(Path(argv[argv.index("--dir") + 1]).resolve(), self.data / "sosove-sku-board")
        self.assertTrue(Path(info["tmp"]).is_relative_to(self.data))
        self.assertTrue(Path(info["pip"]).is_relative_to(self.data))
        self.assertFalse((self.data / "sosove-sku-board").exists())
        self.assert_no_stage()

    def test_config_and_directory_are_forwarded_as_literal_arguments(self):
        # Shell metacharacters remain ordinary filename bytes, never commands.
        private = self.data / "private $(echo LEAK).json"
        private.write_text('{"token":"PRIVATE_VALUE_NOT_IN_OUTPUT"}', encoding="utf-8")
        target = self.data / "project $(echo HACKED)"
        result = self.run_package("--check", "--dir", shell_path(target), "--port", "08794",
                                  "--config-file", shell_path(private))
        self.assertEqual(result.returncode, 0, result.stderr)
        info = json.loads(next(line.removeprefix("CORE_ARGS:") for line in result.stdout.splitlines()
                               if line.startswith("CORE_ARGS:")))
        argv = info["argv"]
        self.assertEqual(Path(argv[argv.index("--config-file") + 1]).resolve(), private.resolve())
        self.assertEqual(Path(argv[argv.index("--dir") + 1]).resolve(), target.resolve())
        self.assertEqual(argv[argv.index("--port") + 1], "8794")
        self.assertNotIn("PRIVATE_VALUE_NOT_IN_OUTPUT", result.stdout + result.stderr)
        self.assert_no_stage()

    def test_unsafe_tar_entries_never_execute_core_and_are_cleaned(self):
        for entry in (("../outside", tarfile.REGTYPE), ("/absolute", tarfile.REGTYPE),
                      ("app/link", tarfile.SYMTYPE), ("app/hard", tarfile.LNKTYPE),
                      ("app/pipe", tarfile.FIFOTYPE), ("C:/windows", tarfile.REGTYPE),
                      ("app/../outside", tarfile.REGTYPE), ("unexpected/file", tarfile.REGTYPE),
                      ("manifest.json", tarfile.REGTYPE)):
            with self.subTest(entry=entry):
                result = self.run_package("--check", package=self.package(entry=entry))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Invalid installer payload", result.stderr)
                self.assertNotIn("CORE_ARGS:", result.stdout)
                self.assert_no_stage()

    def test_core_error_exit_code_is_preserved_and_temp_is_cleaned(self):
        result = self.run_package("--check", package=self.package(core_exit=23))
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assert_no_stage()

    def test_apt_scope_is_only_missing_dependencies_and_data_volume_caches(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn('install -y --no-install-recommends "${missing[@]}"', text)
        self.assertIn('Dir::State::lists=$stage/apt/lists', text)
        self.assertIn('Dir::Cache::archives=$stage/apt/archives', text)
        self.assertIn('NEEDRESTART_MODE=l', text)
        self.assertNotIn("apt-get upgrade", text)
        self.assertNotIn("--allow-unauthenticated", text)
        self.assertNotIn("--break-system-packages", text)
        self.assertNotIn("tar -x", text)
        self.assertNotIn("curl ", text)


if __name__ == "__main__":
    unittest.main()
