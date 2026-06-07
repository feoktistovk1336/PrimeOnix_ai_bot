import json
import os
from typing import Any

QUEUE_FILE = os.getenv("PRIME_CONTENT_QUEUE_FILE", "data/prime_content_queue.json")

STATUS_DRAFT = "draft"
STATUS_READY = "ready"
STATUS_IG_READY = "ig_ready"
STATUS_SCHEDULED = "scheduled"
STATUS_PUBLISHED = "published"
STATUS_FAILED = "failed"
STATUS_SENT_TO_N8N = "sent_to_n8n"
STATUS_IG_SENT = "ig_sent"
STATUS_TG_SENT = "tg_sent"


def _now() -> str:
    from services.timezone_utils import now_text
    return now_text()


def _ensure_file():
    folder = os.path.dirname(QUEUE_FILE)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _load() -> list[dict[str, Any]]:
    _ensure_file()
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(items: list[dict[str, Any]]) -> None:
    _ensure_file()
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_prime_content(
    user_id: int,
    tool: str,
    topic: str,
    content: str,
    status: str = STATUS_DRAFT,
    scheduled_at: str | None = None,
    meta: dict[str, Any] | None = None,
    platform: str = "all",
    content_type: str | None = None,
    caption: str | None = None,
    media_url: str | None = None,
) -> dict[str, Any]:
    items = _load()
    next_id = 1
    if items:
        next_id = max(int(i.get("id", 0) or 0) for i in items) + 1
    item = {
        "id": next_id,
        "user_id": int(user_id),
        "tool": tool,
        "topic": topic,
        "content": content,
        "status": status,
        "platform": platform,
        "content_type": content_type or tool,
        "caption": caption,
        "media_url": media_url,
        "created_at": _now(),
        "updated_at": _now(),
        "scheduled_at": scheduled_at,
        "published_at": None,
        "meta": meta or {},
    }
    items.append(item)
    _save(items)
    return item


def list_prime_content(user_id: int | None = None, limit: int = 10, statuses: set[str] | None = None) -> list[dict[str, Any]]:
    items = _load()
    if user_id is not None:
        items = [i for i in items if int(i.get("user_id", 0) or 0) == int(user_id)]
    if statuses:
        items = [i for i in items if str(i.get("status", "")) in statuses]
    return list(reversed(items))[:limit]


def get_prime_content(item_id: int, user_id: int | None = None) -> dict[str, Any] | None:
    for item in _load():
        if int(item.get("id", 0) or 0) != int(item_id):
            continue
        if user_id is not None and int(item.get("user_id", 0) or 0) != int(user_id):
            continue
        return item
    return None


def update_prime_content(item_id: int, **updates: Any) -> dict[str, Any] | None:
    items = _load()
    updated = None
    for item in items:
        if int(item.get("id", 0) or 0) == int(item_id):
            item.update(updates)
            item["updated_at"] = _now()
            updated = item
            break
    if updated:
        _save(items)
    return updated


def mark_prime_content(item_id: int, status: str) -> bool:
    updates: dict[str, Any] = {"status": status}
    if status == STATUS_PUBLISHED:
        updates["published_at"] = _now()
    return update_prime_content(item_id, **updates) is not None


def schedule_prime_content(item_id: int, scheduled_at: str, status: str = STATUS_SCHEDULED) -> dict[str, Any] | None:
    return update_prime_content(item_id, status=status, scheduled_at=scheduled_at)


def delete_prime_content(item_id: int) -> bool:
    items = _load()
    new_items = [i for i in items if int(i.get("id", 0) or 0) != int(item_id)]
    if len(new_items) == len(items):
        return False
    _save(new_items)
    return True


def build_publish_payload(item: dict[str, Any], action: str = "publish_prepare") -> dict[str, Any]:
    """Create a stable payload for n8n/Instagram/Telegram workflows."""
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    return {
        "action": action,
        "source": "telegram_bot",
        "queue_id": item.get("id"),
        "user_id": item.get("user_id"),
        "tool": item.get("tool"),
        "topic": item.get("topic"),
        "content": item.get("content"),
        "status": item.get("status"),
        "platform": item.get("platform") or meta.get("platform") or "all",
        "content_type": item.get("content_type") or meta.get("content_type") or item.get("tool"),
        "caption": item.get("caption") or meta.get("caption"),
        "media_url": item.get("media_url") or meta.get("media_url"),
        "scheduled_at": item.get("scheduled_at"),
        "created_at": item.get("created_at"),
        "meta": meta,
        "expected_response": {
            "text": "Human-readable status/result for Telegram",
            "status": "ok/failed",
            "platform_result": "Instagram/Telegram/n8n result",
        },
    }


def list_due_scheduled(now_text: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Return scheduled items due now or earlier. Simple string compare works for YYYY-MM-DD HH:MM."""
    now_text = now_text or _now()
    items = _load()
    due = [
        i for i in items
        if str(i.get("status")) == STATUS_SCHEDULED
        and str(i.get("scheduled_at") or "9999-99-99 99:99") <= now_text
    ]
    return sorted(due, key=lambda x: str(x.get("scheduled_at") or ""))[:limit]


def queue_stats(user_id: int | None = None) -> dict[str, int]:
    items = _load()
    if user_id is not None:
        items = [i for i in items if int(i.get("user_id", 0) or 0) == int(user_id)]
    stats: dict[str, int] = {}
    for item in items:
        status = str(item.get("status") or STATUS_DRAFT)
        stats[status] = stats.get(status, 0) + 1
    return stats


def find_prime_content_by_meta(key: str, value: Any, user_id: int | None = None) -> dict[str, Any] | None:
    """Find first queue item where meta[key] == value."""
    for item in reversed(_load()):
        if user_id is not None and int(item.get("user_id", 0) or 0) != int(user_id):
            continue
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        if str(meta.get(key) or "") == str(value):
            return item
    return None


def append_media_to_prime_content(item_id: int, media: dict[str, Any], caption: str | None = None) -> dict[str, Any] | None:
    """Append Telegram media file_id to an existing queue item album without creating a second post."""
    items = _load()
    updated = None
    for item in items:
        if int(item.get("id", 0) or 0) != int(item_id):
            continue
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        album_items = meta.get("album_items")
        if not isinstance(album_items, list):
            album_items = []
            # Preserve the first media if it was stored before album mode.
            if meta.get("telegram_file_id"):
                album_items.append({
                    "media_type": meta.get("media_type") or "photo",
                    "telegram_file_id": meta.get("telegram_file_id"),
                    "file_unique_id": meta.get("file_unique_id"),
                })
        album_items.append(media)
        meta["album_items"] = album_items
        meta["album_count"] = len(album_items)
        meta["media_type"] = "album" if len(album_items) > 1 else meta.get("media_type", media.get("media_type"))
        item["meta"] = meta
        item["content_type"] = "custom_album" if len(album_items) > 1 else item.get("content_type")
        if caption:
            item["content"] = caption
            item["caption"] = caption
        item["updated_at"] = _now()
        updated = item
        break
    if updated:
        _save(items)
    return updated
