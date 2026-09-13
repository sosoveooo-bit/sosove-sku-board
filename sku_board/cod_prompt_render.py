"""Submit a saved Atelier page without the legacy suite/template compiler."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import threading
from io import BytesIO
from types import SimpleNamespace
from typing import Any


_RENDER_LOCK = threading.RLock()


class SubmissionUncertainError(ValueError):
    """A local submission receipt exists; starting another job could charge twice."""


def render_settings(spec: dict[str, Any], payload: dict[str, Any]) -> dict[str, str]:
    from . import backend

    form = spec["form"]
    model = backend.limited_text(payload.get("model"), form.get("model", "gpt-image-2"), 120)
    quality = str(payload.get("quality", form.get("quality", "high")))
    profile = str(payload.get("generationProfile", form.get("generationProfile", "standard")))
    if quality not in {"auto", "low", "medium", "high"} or profile not in {"fast", "standard", "quality"}:
        raise ValueError("生图质量或策略无效")
    return {"model": model, "quality": quality, "generationProfile": profile}


def _context(project_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, str], str]:
    from . import cod_prompt_atelier as atelier

    if not isinstance(payload, dict):
        raise ValueError("生图请求必须是 JSON 对象")
    owner = atelier._owner(actor)
    spec = atelier.get_render_spec(project_id, payload.get("revision"), payload.get("pageNumber"), actor)
    if not spec.get("referenceImages"):
        raise ValueError("真实生图需要当前商品参考图；请上传后生成新版本")
    settings = render_settings(spec, payload)
    token = payload.get("requestKey", "single")
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9:_-]{1,200}", token):
        raise ValueError("生图请求编号不正确")
    if payload.get("queueId") and not re.fullmatch(r"[a-f0-9]{32}", str(payload["queueId"])):
        raise ValueError("无效的后台队列编号")
    source = {
        "owner": owner, "projectId": project_id, "revision": int(payload["revision"]),
        "pageNumber": int(payload["pageNumber"]), "settings": settings, "size": spec["form"]["size"],
        "fingerprint": spec["fingerprint"], "promptSha256": hashlib.sha256(spec["prompt"].encode("utf-8")).hexdigest(),
        "requestToken": token,
    }
    request_key = hashlib.sha256(json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return owner, spec, settings, request_key


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    from . import cod_prompt_atelier as atelier

    status = str(job.get("status") or "queued")
    fields = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    uncertain = bool(job.get("atelierOutcomeUncertain") or fields.get("atelierOutcomeUncertain"))
    result = copy.deepcopy(job.get("result")) if status == "success" and isinstance(job.get("result"), dict) else {}
    result.update({
        "ok": status != "error", "pending": status in {"queued", "running"},
        "jobId": job["id"], "status": status,
        "message": atelier._safe_error(job.get("message")) if job.get("message") else ("图片已生成" if status == "success" else "后台生图任务"),
        "requestKey": fields.get("atelierRequestKey", ""), "updatedAt": job.get("updatedAt", ""),
    })
    if status == "error":
        result.update(error=atelier._safe_error(job.get("error") or "远端生图任务失败"),
                      errorCode="atelier_outcome_uncertain" if uncertain else "ai_image_job_failed")
    if uncertain:
        result["outcomeUncertain"] = True
    return result


def _find_job(request_key: str, actor: dict[str, Any]) -> dict[str, Any] | None:
    from . import backend

    username = str(actor.get("username") or actor.get("id") or "").strip().casefold()
    with backend._AI_IMAGE_JOB_LOCK:
        for job in backend._AI_IMAGE_JOBS.values():
            fields = job.get("payload") if isinstance(job.get("payload"), dict) else {}
            if fields.get("atelierRequestKey") == request_key and str(job.get("owner") or "").strip().casefold() == username:
                return copy.deepcopy(job)
    return None


def find_render_job(project_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any] | None:
    """Recover a response lost after backend persistence without resubmitting."""
    with _RENDER_LOCK:
        _owner, _spec, _settings, key = _context(project_id, payload, actor)
        existing = _find_job(key, actor)
        return _public_job(existing) if existing else None


def get_render_job(project_id: str, job_id: str, actor: dict[str, Any], request_key: str = "") -> dict[str, Any] | None:
    """Read our known job without the generic endpoint pruning its result first."""
    from . import backend, cod_prompt_atelier as atelier

    owner = atelier._owner(actor)
    with atelier._LOCK:
        atelier._read(owner, atelier._project_id(project_id))
    with backend._AI_IMAGE_JOB_LOCK:
        job = copy.deepcopy(backend._AI_IMAGE_JOBS.get(job_id))
    if not job:
        return None
    fields = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    username = str(actor.get("username") or actor.get("id") or "").strip().casefold()
    if (str(job.get("owner") or "").strip().casefold() != username or fields.get("atelierProjectId") != project_id
            or (request_key and fields.get("atelierRequestKey") != request_key)):
        raise PermissionError("该生图任务不属于当前商品请求")
    return _public_job(job)


def start_render(project_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
    """Submit once for a durable request key, including across HTTP retries.

    Receipts intentionally outlive the short-lived image-job cache. An absent
    cached job is not evidence that the provider never received the request.
    An explicit new queue/attempt token is needed for paid regeneration.
    """
    from . import cod_prompt_atelier as atelier

    with _RENDER_LOCK:
        owner, spec, settings, request_key = _context(project_id, payload, actor)
        revision, page_number = int(payload["revision"]), int(payload["pageNumber"])
        identity = {"projectId": project_id, "revision": revision, "pageNumber": page_number, "requestKey": request_key}
        existing = _find_job(request_key, actor)
        if existing:
            return {**_public_job(existing), **identity, "reusedJob": True}
        receipt_path = atelier._directory(owner, project_id) / "render-requests" / f"{request_key}.json"
        now = atelier._now()
        receipt = {**identity, "owner": owner, "status": "submitting", "jobId": "", "createdAt": now, "updatedAt": now}
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # O_EXCL via "x" protects the billing boundary even if a second
            # local server accidentally uses the same data directory. A crash
            # during this first write leaves a receipt and fails closed.
            with receipt_path.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(receipt, handle, ensure_ascii=False, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise SubmissionUncertainError("提交记录已存在，但原生图任务已过期或状态无法确认；已停止自动重复扣费。请核实结果后再明确重新生成。") from exc
        return _submit_once(project_id, payload, actor, spec, settings, owner, receipt, receipt_path)


def _submit_once(project_id, payload, actor, spec, settings, owner, receipt, receipt_path):
    from . import backend, cod_prompt_atelier as atelier

    revision, page_number = receipt["revision"], receipt["pageNumber"]
    identity = {key: receipt[key] for key in ("projectId", "revision", "pageNumber", "requestKey")}
    fields = {
        "prompt": spec["prompt"], "mode": "edit", **settings,
        "size": spec["form"]["size"],
        "count": 1, "lockLevel": "strict",
        "atelierProjectId": project_id, "atelierRevision": revision,
        "atelierPageNumber": page_number, "atelierFingerprint": spec["fingerprint"],
        "atelierRequestKey": receipt["requestKey"], "atelierOwner": owner,
    }
    queue_id = payload.get("queueId")
    if queue_id:
        fields["atelierQueueId"] = queue_id
    files = {
        f"reference{index}": SimpleNamespace(filename=name, file=BytesIO(content))
        for index, (name, content, mime) in enumerate(spec["referenceImages"])
    }
    try:
        result = backend.start_ai_image_job("edit", fields, actor, files)
        if not isinstance(result, dict) or not result.get("jobId"):
            raise ValueError("后台生图没有返回可恢复的任务编号")
    except Exception as exc:
        # The backend may persist successfully and then fail starting its local
        # worker. Find that exact job instead of creating a second paid request.
        existing = _find_job(receipt["requestKey"], actor)
        if existing:
            result = {**_public_job(existing), "reusedJob": True}
        else:
            receipt.update(status="needs_attention", error=atelier._safe_error(exc), updatedAt=atelier._now())
            atelier._atomic_json(receipt_path, receipt)
            raise SubmissionUncertainError("提交结果无法确认，已停止自动重发以防重复扣费；请核实原任务后再重新生成。") from exc
    finally:
        for item in files.values():
            item.file.close()
    receipt.update(status="submitted", jobId=result["jobId"], updatedAt=atelier._now())
    atelier._atomic_json(receipt_path, receipt)
    return {**result, **identity}


def validate_execution(fields: dict[str, Any], actor: dict[str, Any], prompt: str) -> dict[str, Any] | None:
    if not fields.get("atelierProjectId"):
        return None
    from . import cod_prompt_atelier

    spec = cod_prompt_atelier.get_render_spec(
        fields["atelierProjectId"], fields.get("atelierRevision"), fields.get("atelierPageNumber"), actor,
    )
    if fields.get("suiteKey") or fields.get("templateKey") or int(fields.get("count", 1)) != 1:
        raise ValueError("Atelier页面不能与其他套图模板混用")
    if fields.get("atelierFingerprint") != spec["fingerprint"] or prompt != spec["prompt"]:
        raise ValueError("商品版本或提示词不匹配，请重新读取已保存版本")
    if fields.get("size") != spec["form"]["size"]:
        raise ValueError("画布与已保存的提示词版本不匹配")
    return spec


def validate_references(spec: dict[str, Any], references: list[tuple[str, bytes, str]]) -> None:
    expected = spec.get("referenceImages", [])
    if not expected or len(expected) != len(references):
        raise ValueError("参考图数量与当前商品版本不匹配")
    if any(hashlib.sha256(original[1]).digest() != hashlib.sha256(submitted[1]).digest() for original, submitted in zip(expected, references)):
        raise ValueError("参考图内容与当前商品版本不匹配，已阻止串品生图")


def archive_results(fields: dict[str, Any], actor: dict[str, Any], materials: list[dict[str, Any]], images: list[tuple[bytes, str]] | None = None) -> str:
    from . import cod_prompt_atelier, cod_prompt_assets

    errors = []
    for index, material in enumerate(materials):
        material.update({
            "projectId": fields["atelierProjectId"], "revision": int(fields["atelierRevision"]),
            "page": int(fields["atelierPageNumber"]), "pageNumber": int(fields["atelierPageNumber"]),
            "fingerprint": fields["atelierFingerprint"],
        })
        try:
            content = images[index][0] if images and index < len(images) else None
            archived = cod_prompt_assets.archive_material(fields["atelierProjectId"], fields["atelierRevision"], fields["atelierPageNumber"], material, actor, content)
            material.update(archived)
        except (ValueError, OSError) as exc:
            material.update({"archiveStatus": "failed", "archiveError": str(exc)[:180]})
            try:
                cod_prompt_atelier.record_material(fields["atelierProjectId"], fields["atelierRevision"], fields["atelierPageNumber"], material, actor)
            except (ValueError, OSError):
                pass
            errors.append(f"图片已完成，但长期存档失败：{str(exc)[:180]}；请先保存图片后再重试存档。")
    return "；".join(errors)
