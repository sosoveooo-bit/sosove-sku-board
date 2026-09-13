"""Durable, owner-scoped Atelier render runs, independent of browser lifetime.

Each page has an immutable server-generated submission token. A persisted
``submitting`` state with no known backend job is uncertain, never a reason to
submit again. Explicit ``redo`` is the only action creating a new paid run.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import threading
import uuid
from typing import Any

from . import cod_prompt_atelier as atelier, cod_prompt_render as render

_LOCK = threading.RLock()
_RUNS: dict[tuple[str, str, str], threading.Event] = {}
_THREAD_FACTORY = threading.Thread
_POLL_SECONDS = 2.0
_ACTIVE = frozenset({"queued", "running"})
_IN_FLIGHT = frozenset({"submitting", "running"})
_PAGE_STATES = frozenset({"queued", "submitting", "running", "complete", "error", "needs_attention"})
_PUBLIC_FIELDS = (
    "id", "projectId", "revision", "fingerprint", "runFingerprint", "status", "settings",
    "pages", "completed", "total", "failed", "error", "createdAt", "updatedAt", "mode", "cancelRequested",
)


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _queue_id(value: Any) -> str:
    candidate = str(value or "")
    if not re.fullmatch(r"[a-f0-9]{32}", candidate):
        raise ValueError("后台生图队列编号不正确")
    return candidate


def _key(record: dict[str, Any]) -> tuple[str, str, str]:
    return record["_owner"], record["projectId"], record["id"]


def _path(owner: str, project_id: str, queue_id: str):
    return atelier._directory(owner, project_id) / "render-queues" / f"{_queue_id(queue_id)}.json"


def _write(record: dict[str, Any]) -> None:
    record["updatedAt"] = atelier._now()
    record["completed"] = sum(page["status"] == "complete" for page in record["pages"])
    record["failed"] = sum(page["status"] == "error" for page in record["pages"])
    atelier._atomic_json(_path(*_key(record)), record)


def _read(owner: str, project_id: str, queue_id: str) -> dict[str, Any]:
    try:
        record = json.loads(_path(owner, project_id, queue_id).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("生图队列不存在或不属于当前账号") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("生图队列记录无法读取；请保留文件，勿重复提交") from exc
    if (not isinstance(record, dict) or record.get("_owner") != owner or record.get("projectId") != project_id
            or record.get("id") != queue_id or not isinstance(record.get("pages"), list)
            or not record["pages"] or any(not isinstance(page, dict) or page.get("status") not in _PAGE_STATES for page in record["pages"])):
        raise ValueError("生图队列记录校验失败；请保留文件，勿重复提交")
    return record


def _records(owner: str, project_id: str) -> list[dict[str, Any]]:
    directory = atelier._directory(owner, project_id) / "render-queues"
    if not directory.exists():
        return []
    records = [_read(owner, project_id, path.stem) for path in directory.iterdir()
               if path.is_file() and re.fullmatch(r"[a-f0-9]{32}\.json", path.name)]
    return sorted(records, key=lambda item: (item["createdAt"], item["id"]), reverse=True)


def _public(record: dict[str, Any]) -> dict[str, Any]:
    result = {key: copy.deepcopy(record[key]) for key in _PUBLIC_FIELDS if key in record}
    for page in result["pages"]:
        for key in list(page):
            if key.startswith("_"):
                page.pop(key)
    return result


def _actor_snapshot(actor: dict[str, Any]) -> dict[str, str]:
    # No session token, password, API key, or configured endpoint is persisted.
    return {"username": str(actor.get("username") or actor.get("id") or ""), "role": str(actor.get("role") or "")}


def _restore_actor(record: dict[str, Any]) -> dict[str, Any]:
    """Recheck live account status/permissions instead of trusting a saved role."""
    backend = atelier._backend()
    snapshot = record.get("_actor") or {}
    username = str(snapshot.get("username") or "")
    user = backend.find_user(backend.load_board(), username)
    if not user or not user.get("active", True) or not backend.can_use_ai_image(user):
        raise PermissionError("原账号已停用或没有 AI 图片权限，后台队列已暂停")
    actor = _actor_snapshot(user)
    if atelier._owner(actor) != record["_owner"]:
        raise PermissionError("生图队列账号校验失败，后台队列已暂停")
    return actor


def _authenticate(project_id: str, actor: dict[str, Any], revision: Any = None) -> tuple[str, str]:
    owner, project_id = atelier._owner(actor), atelier._project_id(project_id)
    with atelier._LOCK:
        document = atelier._read(owner, project_id)
        if revision is not None:
            atelier._version(document, revision)
    return owner, project_id


def _page_snapshot(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt": spec["prompt"], "fingerprint": spec["fingerprint"], "size": spec["form"]["size"],
        "references": copy.deepcopy(spec.get("references") or []),
    }


def _new_record(project_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("revision") in (None, ""):
        raise ValueError("生图队列必须绑定商品版本")
    owner, project_id = _authenticate(project_id, actor, payload["revision"])
    revision = atelier._integer(payload["revision"], "版本")
    mode = payload.get("mode", "resume")
    if mode not in {"resume", "redo"}:
        raise ValueError("生图队列方式必须是 resume 或 redo")
    with atelier._LOCK:
        version = atelier._version(atelier._read(owner, project_id), revision)
        available = sorted(item["page"] for item in version["suitePages"] if item.get("executionPrompt"))
    numbers = payload.get("pageNumbers", available)
    if not isinstance(numbers, list) or not numbers or len(numbers) > 100:
        raise ValueError("请选择 1 至 100 个已保存提示词的页面")
    numbers = [atelier._integer(value, "页面编号") for value in numbers]
    if len(set(numbers)) != len(numbers) or any(number not in available for number in numbers):
        raise ValueError("页面编号重复或尚未生成完整提示词")
    numbers.sort()
    queue_id, snapshots, settings, fingerprint = uuid.uuid4().hex, {}, None, ""
    for number in numbers:
        spec = atelier.get_render_spec(project_id, revision, number, actor)
        snapshots[str(number)] = _page_snapshot(spec)
        settings = settings or render.render_settings(spec, payload)
        fingerprint = fingerprint or spec["fingerprint"]
    run_fingerprint = _hash({"owner": owner, "projectId": project_id, "revision": revision,
                             "settings": settings, "pageSnapshots": snapshots})
    now = atelier._now()
    return {
        "schemaVersion": 1, "id": queue_id, "projectId": project_id, "revision": revision,
        "fingerprint": fingerprint, "runFingerprint": run_fingerprint, "settings": settings,
        "mode": mode, "status": "queued", "pages": [
            {"page": number, "status": "queued", "jobId": "", "requestKey": "", "error": "",
             "_requestToken": f"queue:{queue_id}:page:{number}", "_snapshotHash": _hash(snapshots[str(number)])}
            for number in numbers],
        "total": len(numbers), "completed": 0, "failed": 0, "error": "",
        "createdAt": now, "updatedAt": now, "cancelRequested": False,
        "_owner": owner, "_actor": _actor_snapshot(actor), "_pageSnapshots": snapshots,
    }


def _has_pending_job(record: dict[str, Any]) -> bool:
    return any(page["status"] in _IN_FLIGHT for page in record["pages"])


def _capacity(record: dict[str, Any]) -> None:
    key = _key(record)
    for active in _RUNS:
        if active != key and active[:2] == key[:2]:
            raise ValueError("该商品已有后台生图队列运行；请先等待完成或停止后再试")
    if sum(active[0] == key[0] and active != key for active in _RUNS) >= 2:
        raise ValueError("当前账号已有两个后台生图队列运行，请等待其中一个完成")


def _start_worker_locked(record: dict[str, Any]) -> None:
    key = _key(record)
    if key in _RUNS:
        return
    _capacity(record)
    event = threading.Event()
    _RUNS[key] = event
    worker = _THREAD_FACTORY(target=_worker, args=(*key,), name=f"atelier-render-{record['id'][:8]}", daemon=True)
    try:
        worker.start()
    except Exception:
        _RUNS.pop(key, None)
        record.update(status="paused", error="后台队列未能启动；已保存的页面未丢失，可继续运行。")
        _write(record)
        raise


def _resume_locked(record: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
    if _key(record) in _RUNS:
        if record.get("cancelRequested"):
            record.update(cancelRequested=False, status="running", error="", _actor=_actor_snapshot(actor))
            _write(record)
            _RUNS[_key(record)].set()
        return {"ok": True, "queue": _public(record), "reused": True}
    pending = any(page["status"] in {"queued", "submitting", "running", "needs_attention"} for page in record["pages"])
    if not pending:
        return {"ok": True, "queue": _public(record), "reused": True}
    _capacity(record)
    record.update(cancelRequested=False, status="queued", error="", _actor=_actor_snapshot(actor))
    _write(record)
    _start_worker_locked(record)
    return {"ok": True, "queue": _public(_read(*_key(record))), "reused": True}


def _inherit_known_pages(candidate: dict[str, Any], records: list[dict[str, Any]]) -> None:
    """Resume a larger/different selection without repaying for known pages.

    A run-level fingerprint contains the selected page set, but submission
    history belongs to each page. Reuse both completed and uncertain records;
    an unknown old result must not silently become a fresh paid request.
    """
    for page in candidate["pages"]:
        for previous in records:
            if previous["settings"] != candidate["settings"]:
                continue
            source = next((item for item in previous["pages"] if item["page"] == page["page"]
                           and item["_snapshotHash"] == page["_snapshotHash"] and item["status"] != "queued"), None)
            if source:
                if previous["revision"] != candidate["revision"] and source["status"] != "complete":
                    raise ValueError(
                        f"第 {page['page']} 页的相同提示词在版本 {previous['revision']} 已提交但未确认成功；"
                        "请先核对原版本生图队列。继续不会自动重复扣费，如确认要再做，请明确选择重新生成。"
                    )
                page.update(copy.deepcopy(source))
                page["reusedFromQueueId"] = previous["id"]
                page["reusedOriginRevision"] = source.get("reusedOriginRevision", previous["revision"])
                page["reusedOriginQueueId"] = source.get("reusedOriginQueueId", previous["id"])
                break


def start_queue(project_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        candidate = _new_record(project_id, payload, actor)
        records = _records(candidate["_owner"], project_id)
        matching = [record for record in records if record["runFingerprint"] == candidate["runFingerprint"]]
        active_match = next((record for record in matching if _key(record) in _RUNS or record["status"] in _ACTIVE), None)
        if active_match:
            return _resume_locked(active_match, actor)
        if payload.get("mode", "resume") == "resume" and matching:
            return _resume_locked(matching[0], actor)
        if any(record["status"] in _ACTIVE or _key(record) in _RUNS for record in records):
            raise ValueError("该商品已有后台生图队列运行；请先等待完成或停止后再试")
        _capacity(candidate)
        if candidate["mode"] == "resume":
            _inherit_known_pages(candidate, records)
        _write(candidate)
        _start_worker_locked(candidate)
        return {"ok": True, "queue": _public(_read(*_key(candidate))), "reused": False}


def list_queues(project_id: str, actor: dict[str, Any], revision: Any = None) -> dict[str, Any]:
    owner, project_id = _authenticate(project_id, actor, revision)
    if revision is not None:
        revision = atelier._integer(revision, "版本")
    with _LOCK:
        records = [record for record in _records(owner, project_id) if revision is None or record["revision"] == revision]
        return {"ok": True, "queues": [_public(record) for record in records]}


def resume_queue(project_id: str, queue_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("继续队列请求必须是 JSON 对象")
    owner, project_id = _authenticate(project_id, actor)
    with _LOCK:
        record = _read(owner, project_id, _queue_id(queue_id))
        if payload.get("revision") is not None and atelier._integer(payload["revision"], "版本") != record["revision"]:
            raise ValueError("继续操作的版本与生图队列不一致")
        for field in ("model", "quality", "generationProfile"):
            if field in payload and payload[field] != record["settings"][field]:
                raise ValueError("继续队列不能更换模型、质量或策略；请使用明确的新生图任务")
        if "pageNumbers" in payload and payload["pageNumbers"] != [page["page"] for page in record["pages"]]:
            raise ValueError("继续队列不能修改原始页面集合")
        return _resume_locked(record, actor)


def cancel_queue(project_id: str, queue_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("停止队列请求必须是 JSON 对象")
    owner, project_id = _authenticate(project_id, actor)
    with _LOCK:
        record = _read(owner, project_id, _queue_id(queue_id))
        if payload.get("revision") is not None and atelier._integer(payload["revision"], "版本") != record["revision"]:
            raise ValueError("停止操作的版本与生图队列不一致")
        if record["status"] == "complete":
            return {"ok": True, "queue": _public(record)}
        record.update(cancelRequested=True, status="paused",
                      error="已停止提交后续页面；已交给生图服务的任务仍可能完成并产生费用。")
        _write(record)
        event = _RUNS.get(_key(record))
        if event:
            event.set()
        return {"ok": True, "queue": _public(record)}


def _payload(record: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    return {**record["settings"], "revision": record["revision"], "pageNumber": page["page"],
            "requestKey": page["_requestToken"], "queueId": record["id"]}


def _apply_job(page: dict[str, Any], result: dict[str, Any] | None) -> bool:
    """Return True when a known remote job still needs polling."""
    if not result:
        page.update(status="needs_attention", error="原提交记录的生图任务不存在或已过期；状态未知，已停止自动重发，避免重复扣费。")
        return False
    page["jobId"] = str(result.get("jobId") or page.get("jobId") or "")
    page["requestKey"] = str(result.get("requestKey") or page.get("requestKey") or "")
    if result.get("outcomeUncertain") or result.get("errorCode") == "atelier_outcome_uncertain":
        page.update(status="needs_attention", error=atelier._safe_error(result.get("error") or "原任务的提交结果无法确认；不会自动重发。"))
    elif result.get("pending") or result.get("status") in {"queued", "running"}:
        page.update(status="running", error="")
        return True
    elif result.get("status") == "error" or not result.get("ok", True):
        page.update(status="error", error=atelier._safe_error(result.get("error") or "生图服务未完成此页；继续队列不会重新提交失败页。"))
    else:
        page.update(status="complete", error="")
        if result.get("archiveWarning"):
            page["archiveWarning"] = atelier._safe_error(result["archiveWarning"])
    return False


def _settle(record: dict[str, Any]) -> None:
    if any(page["status"] == "needs_attention" for page in record["pages"]):
        record.update(status="needs_attention", error="有页面的提交结果无法确认，已停止自动重发。请先核实原任务，再决定是否重新生成。")
    elif all(page["status"] == "complete" for page in record["pages"]):
        record.update(status="complete", error="")
    elif record.get("cancelRequested"):
        record.update(status="paused", error="已停止提交后续页面；已交给生图服务的任务仍可能完成并产生费用。")
    elif any(page["status"] == "queued" for page in record["pages"]):
        record.update(status="queued", error="")
    else:
        completed = sum(page["status"] == "complete" for page in record["pages"])
        record.update(status="partial" if completed else "error", error="已完成页面已保留。失败页不会被自动重复提交；如需再做，请明确选择重新生成。")
    _write(record)


def _worker(owner: str, project_id: str, queue_id: str) -> None:
    key = (owner, project_id, queue_id)
    settled = False
    try:
        while True:
            with _LOCK:
                record = _read(*key)
                actor = _restore_actor(record)
                # Reconcile an already submitted page even when Stop was pressed.
                page = next((item for item in record["pages"] if item["status"] in _IN_FLIGHT), None)
                if page is None:
                    page = next((item for item in record["pages"] if item["status"] == "needs_attention"), None)
                if page is None and not record.get("cancelRequested"):
                    page = next((item for item in record["pages"] if item["status"] == "queued"), None)
                if page is None:
                    _settle(record)
                    settled = True
                    return
                current_payload = _payload(record, page)
                if page["status"] == "queued":
                    spec = atelier.get_render_spec(project_id, record["revision"], page["page"], actor)
                    if _hash(_page_snapshot(spec)) != page["_snapshotHash"]:
                        page.update(status="needs_attention", error="已保存的执行提示词或参考图与队列快照不一致；已停止提交。")
                        _settle(record)
                        return
                    # Holding _LOCK until enqueue completes makes Stop linear:
                    # once the stop response returns no further page can submit.
                    page.update(status="submitting", error="", submittedAt=atelier._now())
                    record["status"] = "running"
                    _write(record)
                    try:
                        result = render.start_render(project_id, current_payload, actor)
                    except Exception:
                        result = render.find_render_job(project_id, current_payload, actor)
                    pending = _apply_job(page, result)
                else:
                    if page.get("jobId"):
                        result = render.get_render_job(project_id, page["jobId"], actor, page.get("requestKey", ""))
                    else:
                        result = render.find_render_job(project_id, current_payload, actor)
                    pending = _apply_job(page, result)
                if page["status"] == "needs_attention":
                    _settle(record)
                    return
                record["status"] = "paused" if record.get("cancelRequested") else "running"
                _write(record)
                event = _RUNS.get(key)
            if pending:
                if event is None:
                    return
                event.wait(_POLL_SECONDS)
                event.clear()
    except Exception as exc:
        with _LOCK:
            try:
                record = _read(*key)
                if any(page["status"] == "submitting" for page in record["pages"]):
                    for page in record["pages"]:
                        if page["status"] == "submitting":
                            page.update(status="needs_attention", error="提交中断且状态未确认，已阻止重复提交。")
                    record["status"] = "needs_attention"
                else:
                    record["status"] = "paused"
                record["error"] = atelier._safe_error(exc)
                _write(record)
            except (ValueError, OSError):
                # Preserve damaged records; never delete or replace their pages.
                pass
    finally:
        with _LOCK:
            _RUNS.pop(key, None)
            # A user can resume in the tiny gap between a graceful settlement
            # and this cleanup. Their accepted resume must not be lost when the
            # exiting worker releases its slot. Do not loop after I/O failures.
            if settled:
                try:
                    record = _read(*key)
                    if record["status"] in _ACTIVE and not record.get("cancelRequested"):
                        _start_worker_locked(record)
                except (ValueError, OSError, RuntimeError):
                    pass


def resume_queues_on_startup() -> dict[str, int]:
    """Run after backend image jobs have been restored, never before.

    Intentionally paused queues do not submit new pages. Existing pending jobs
    can be observed to completion, while uncertain submissions stay stopped.
    """
    counts = {"loaded": 0, "resumed": 0, "paused": 0, "invalid": 0}
    root = atelier._root()
    if not root.exists():
        return counts
    with _LOCK:
        for owner_dir in root.iterdir():
            if not owner_dir.is_dir() or not re.fullmatch(r"[a-f0-9]{64}", owner_dir.name):
                continue
            for project_dir in owner_dir.iterdir():
                if not project_dir.is_dir() or not re.fullmatch(r"[a-f0-9]{32}", project_dir.name):
                    continue
                try:
                    atelier._read(owner_dir.name, project_dir.name)
                    records = _records(owner_dir.name, project_dir.name)
                except (ValueError, OSError):
                    counts["invalid"] += 1
                    continue
                for record in records:
                    counts["loaded"] += 1
                    if _key(record) in _RUNS or not (record["status"] in _ACTIVE or _has_pending_job(record)):
                        continue
                    try:
                        actor = _restore_actor(record)
                        record["_actor"] = _actor_snapshot(actor)
                        _capacity(record)
                        _start_worker_locked(record)
                        counts["resumed"] += 1
                    except (PermissionError, ValueError, OSError, RuntimeError) as exc:
                        record.update(status="paused", error=atelier._safe_error(exc))
                        _write(record)
                        counts["paused"] += 1
    return counts
