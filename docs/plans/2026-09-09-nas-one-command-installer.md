# ARM64 NAS One-command Installer Plan

**Goal:** Deliver a self-contained, integrity-checked `.run` installer for a Debian12 ARM64 NAS without installing anything on a guessed host or publishing private configuration.

**Architecture:** Native Python3.11 virtual environment plus a dedicated nonroot systemd service, installed on a verified NAS data filesystem. Bundle current application source, ARM64 binary wheels, the public Open Image Prompts corpus and Linkfox prompt assets. Keep immutable releases separate from shared data/configuration; preserve existing managed installs during upgrades and roll back failed activation.

## Scope and safeguards

- The supplied public IP also identifies the earlier x86 Ubuntu VPS. Do not infer that it is the NAS and do not SSH/deploy to it for this task.
- Prefer native installation here to avoid Docker layers/build cache on the small system partition. The NAS forwards generation to user-configured upstream services; no large model weights or GPU runtime are installed.
- Default install directory: next to the installer on the NAS data volume. Require a separate, writable executable data filesystem with at least3GiB free, and sufficient system partition space for the small Debian dependencies. Stop before changes if architecture, filesystem or service ownership checks fail.
- Use Debian Python3.11/venv and offline ARM64 wheels, not global pip or source compilation. Existing Docker, SSH, network settings, unrelated services and system-wide logging remain untouched.
- First run generates a random admin password and encryption key. Default nonadmin seed accounts are inactive with random passwords. Existing users, provider keys and image records are never reset by upgrades.
- Provider credentials and historical images are excluded from the bundle. Optional user-supplied configuration import is explicit and limited to application connection settings; all NAS filesystem/runtime paths remain local to the install root.
- Use code/releases, `current` symlink, shared data/tmp/OIP cache, root-only config and private backups. Protect the service with least-privilege systemd settings and mounted-volume dependencies.
- Provide `--help` and a non-installing `--check` mode, package/file SHA-256 verification, port/service conflict detection, consistent upgrade backups and activation rollback.

## Verification

1. Isolated installer/argument/path/manifest/account/config-preservation/rollback tests; no apt, service creation or remote installation during development.
2. Validate Bash syntax and self-extractor marker/integrity; inspect binary wheel tags for CPython3.11 aarch64 or platform-independent compatibility.
3. Run application regressions including empty provider setup UI; build the artifact from a stable current source snapshot and include notices/licenses.
4. Deliver the installer, checksum and concise Chinese guide. Explain that missing Debian system packages may require Internet access and actual ARM64 NAS activation has not been performed.
