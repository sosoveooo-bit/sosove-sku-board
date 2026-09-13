"""Private, content-addressed Atelier assets outside the shared temporary cache."""
from __future__ import annotations

import copy
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, BinaryIO
import uuid
import zipfile


_FORMATS = {"PNG": (".png", "image/png"), "JPEG": (".jpg", "image/jpeg"), "WEBP": (".webp", "image/webp")}
_MAX_BYTES = 50 * 1024 * 1024


def _asset_id(value: Any) -> str:
    digest = str(value or "")
    if not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("图片存档编号无效")
    return digest


def _path(owner: str, project_id: str, digest: str, suffix: str) -> Path:
    from . import cod_prompt_atelier as atelier
    if suffix not in {".png", ".jpg", ".webp"}:
        raise ValueError("图片格式无效")
    project_directory = atelier._directory(owner, project_id).resolve()
    directory = (project_directory / "assets").resolve()
    if directory.parent != project_directory:
        raise ValueError("项目图片目录不能指向其他位置")
    target = (directory / f"{_asset_id(digest)}{suffix}").resolve()
    if target.parent != directory:
        raise ValueError("图片目录无效")
    return target


def _image_format(content: bytes) -> tuple[str, str]:
    from PIL import Image
    if not isinstance(content, bytes) or not content or len(content) > _MAX_BYTES:
        raise ValueError("存档图片为空或超过50MB")
    try:
        with Image.open(BytesIO(content)) as image:
            format_name = image.format
            image.verify()
    except Exception as exc:
        raise ValueError("生成结果不是完整可读的图片，不能标记为长期存档") from exc
    if format_name not in _FORMATS:
        raise ValueError("长期素材仅支持PNG/JPEG/WEBP")
    return _FORMATS[format_name]


def _write_bytes(target: Path, content: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def archive_material(project_id: str, revision: Any, page_number: Any, material: dict[str, Any], actor: dict[str, Any], content: bytes | None = None) -> dict[str, Any]:
    from . import cod_prompt_atelier as atelier
    owner, project_id = atelier._owner(actor), atelier._project_id(project_id)
    number = atelier._integer(page_number, "成图页码")
    with atelier._LOCK:
        version = atelier._version(atelier._read(owner, project_id), revision)
        revision = version["revision"]
        if not any(page["page"] == number for page in version["suitePages"]):
            raise ValueError("该页尚无保存的提示词，不可归档")
        # No raw client URL/path is ever accepted. Old-image migration uses only
        # the material found in this authenticated project version.
        if content is None:
            stored = next((item for item in version["materials"] if item.get("id") == material.get("id") and item.get("page") == number), None)
            if not stored:
                raise ValueError("当前项目没有这张成图记录")
            material = copy.deepcopy(stored)
    if content is None and material.get("assetId"):
        read_asset(project_id, material["assetId"], actor, revision)
        return material
    if content is None:
        from . import backend
        material_id = str(material.get("id", ""))
        if not re.fullmatch(r"AI-[A-F0-9]{10}", material_id):
            raise ValueError("旧成图标识无效，不能自动读取")
        remote = str(material.get("remoteUrl") or "")
        if remote and not backend.ai_image_configured_node_for_remote_url(remote):
            raise ValueError("旧图地址不属于已配置的生图节点，请手动保存后导入")
        content, _mime = backend.read_ai_image_output(material_id, remote)
    suffix, mime = _image_format(content)
    digest = hashlib.sha256(content).hexdigest()
    target = _path(owner, project_id, digest, suffix)
    if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        _write_bytes(target, content)
    url = f"/api/sku-board/cod-atelier/projects/{project_id}/assets/{digest}?revision={revision}"
    result = {**material, "assetId": digest, "assetSuffix": suffix, "archiveStatus": "archived",
              "archiveError": "", "storage": "project-permanent", "mime": mime, "size": len(content),
              "assetUrl": url, "previewUrl": url, "downloadUrl": url,
              "originRevision": material.get("originRevision") or revision, "archivedAt": atelier._now()}
    # Original provider URL is metadata only; all displayed access now goes
    # through the owning project's authenticated permanent-asset route.
    result.pop("path", None)
    atelier.record_material(project_id, revision, number, result, actor)
    return result


def read_asset(project_id: str, asset_id: str, actor: dict[str, Any], revision: Any = None) -> tuple[bytes, str]:
    from . import cod_prompt_atelier as atelier
    owner, project_id = atelier._owner(actor), atelier._project_id(project_id)
    digest = _asset_id(asset_id)
    with atelier._LOCK:
        version = atelier._version(atelier._read(owner, project_id), revision)
        material = next((item for item in version.get("materials", []) if item.get("assetId") == digest and item.get("archiveStatus") == "archived"), None)
        if not material:
            raise ValueError("这张图片不属于当前账号和商品版本")
        suffix, mime = material.get("assetSuffix"), material.get("mime", "image/png")
    try:
        content = _path(owner, project_id, digest, suffix).read_bytes()
    except OSError as exc:
        raise ValueError("项目图片文件缺失，请保留记录并重新归档可用原图") from exc
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("图片完整性校验失败")
    return content, mime


def archive_existing(project_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
    from . import cod_prompt_atelier as atelier
    if payload.get("revision") in (None, ""):
        raise ValueError("归档必须选择明确版本")
    project = atelier.get_project(project_id, actor, payload["revision"])["project"]
    completed, errors = 0, []
    for item in project.get("materials", []):
        try:
            archive_material(project_id, project["revision"], item["page"], item, actor)
            completed += 1
        except (ValueError, OSError) as exc:
            message = atelier._safe_error(exc)[:240]
            errors.append({"page": item.get("page"), "id": item.get("id"), "message": message})
            try:
                atelier.record_material(project_id, project["revision"], item["page"], {**item, "archiveStatus": "failed", "archiveError": message}, actor)
            except (ValueError, OSError):
                pass
    result = atelier.get_project(project_id, actor, project["revision"])
    return {**result, "archived": completed, "errors": errors,
            "message": f"{completed}张图片已长期保存" + (f"；{len(errors)}张原图不可用，请查看详情" if errors else "")}


def image_zip(project_id: str, revision: Any, actor: dict[str, Any]) -> tuple[BinaryIO, str]:
    from . import cod_prompt_atelier as atelier
    project = atelier.get_project(project_id, actor, revision)["project"]
    stream = tempfile.TemporaryFile(prefix="atelier-images-", suffix=".zip")
    included, missing = [], []
    total_bytes = 0
    try:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
            for index, material in enumerate(project.get("materials", []), 1):
                try:
                    content, _mime = read_asset(project_id, material.get("assetId"), actor, project["revision"])
                    total_bytes += len(content)
                    if total_bytes > 1024 * 1024 * 1024:
                        raise ValueError("整套图片超过1GB，请分版本或单张下载")
                    filename = f"page-{int(material['page']):02d}-source-v{int(material.get('originRevision') or project['revision'])}-{index:02d}{material['assetSuffix']}"
                    archive.writestr(filename, content)
                    included.append({"file": filename, "page": material["page"], "originRevision": material.get("originRevision") or project["revision"], "assetId": material["assetId"]})
                except (ValueError, OSError, KeyError) as exc:
                    missing.append({"page": material.get("page"), "id": material.get("id"), "reason": str(exc)[:240]})
            expected_pages = {page["page"] for page in project.get("outline", [])}
            archived_pages = {item["page"] for item in included}
            manifest = {"product": project["name"], "revision": project["revision"], "projectId": project_id,
                        "complete": not missing and expected_pages <= archived_pages,
                        "included": included, "unavailable": missing, "pagesWithoutImage": sorted(expected_pages - archived_pages)}
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
        if not included:
            raise ValueError("当前版本没有可下载的长期图片，请先生成或归档可用旧图")
        stream.seek(0)
        return stream, f"atelier-v{project['revision']}-images.zip"
    except BaseException:
        stream.close()
        raise


def protected_legacy_material_ids() -> set[str]:
    """Read-only cleanup protection for images referenced before v3 migration.

    Raises on a damaged project rather than allowing cleanup to destroy its
    last remaining original. The caller then conservatively skips cleanup.
    """
    from . import cod_prompt_atelier as atelier
    root = atelier._root()
    if not root.exists():
        return set()
    protected: set[str] = set()
    with atelier._LOCK:
        for owner_dir in root.iterdir():
            if not owner_dir.is_dir() or not re.fullmatch(r"[a-f0-9]{64}", owner_dir.name):
                continue
            for directory in owner_dir.iterdir():
                if not directory.is_dir() or not re.fullmatch(r"[a-f0-9]{32}", directory.name):
                    continue
                path = directory / "project.json"
                if not path.exists():
                    continue
                document = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(document, dict) or not isinstance(document.get("revisions"), list):
                    raise ValueError("商品版本存档格式损坏，已暂停旧图清理")
                for version in document["revisions"]:
                    if not isinstance(version, dict) or not isinstance(version.get("materials", []), list):
                        raise ValueError("商品图片记录格式损坏，已暂停旧图清理")
                    for material in version.get("materials", []):
                        if not isinstance(material, dict):
                            raise ValueError("商品图片记录格式损坏，已暂停旧图清理")
                        material_id = str(material.get("id", ""))
                        if re.fullmatch(r"AI-[A-F0-9]{10}", material_id) and material.get("archiveStatus") != "archived":
                            protected.add(material_id)
    return protected
