import asyncio
import os
from typing import Any

import aiohttp


GRAPH_API_VERSION = os.getenv("META_GRAPH_API_VERSION", "v21.0")
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def get_instagram_config() -> dict[str, str | None]:
    return {
        "access_token": os.getenv("META_ACCESS_TOKEN") or os.getenv("INSTAGRAM_ACCESS_TOKEN"),
        "ig_user_id": os.getenv("IG_USER_ID") or os.getenv("INSTAGRAM_USER_ID"),
        "page_id": os.getenv("FB_PAGE_ID") or os.getenv("FACEBOOK_PAGE_ID"),
        "graph_version": GRAPH_API_VERSION,
    }


def instagram_config_status() -> tuple[bool, list[str], dict[str, str | None]]:
    cfg = get_instagram_config()
    missing = []
    if not cfg["access_token"]:
        missing.append("META_ACCESS_TOKEN")
    if not cfg["ig_user_id"]:
        missing.append("IG_USER_ID")
    return len(missing) == 0, missing, cfg


async def check_instagram_connection() -> dict[str, Any]:
    ok, missing, cfg = instagram_config_status()
    if not ok:
        return {"ok": False, "error": "missing_config", "missing": missing, "config": cfg}

    url = f"{GRAPH_BASE_URL}/{cfg['ig_user_id']}"
    params = {
        "fields": "id,username,account_type,media_count",
        "access_token": cfg["access_token"],
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=30) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                return {"ok": False, "error": "api_error", "status": resp.status, "data": data}
            return {"ok": True, "data": data, "config": cfg}


async def create_reel_container(video_url: str, caption: str) -> dict[str, Any]:
    ok, missing, cfg = instagram_config_status()
    if not ok:
        return {"ok": False, "error": "missing_config", "missing": missing}

    url = f"{GRAPH_BASE_URL}/{cfg['ig_user_id']}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": cfg["access_token"],
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, timeout=60) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                return {"ok": False, "error": "container_error", "status": resp.status, "data": data}
            return {"ok": True, "creation_id": data.get("id"), "data": data}


async def wait_container_ready(creation_id: str, attempts: int = 20, delay: int = 6) -> dict[str, Any]:
    cfg = get_instagram_config()
    url = f"{GRAPH_BASE_URL}/{creation_id}"
    params = {"fields": "status_code,status", "access_token": cfg["access_token"]}

    async with aiohttp.ClientSession() as session:
        for _ in range(attempts):
            async with session.get(url, params=params, timeout=30) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    return {"ok": False, "error": "status_error", "status": resp.status, "data": data}
                status_code = str(data.get("status_code", "")).upper()
                if status_code == "FINISHED":
                    return {"ok": True, "ready": True, "data": data}
                if status_code in {"ERROR", "EXPIRED"}:
                    return {"ok": False, "error": "container_not_ready", "data": data}
            await asyncio.sleep(delay)

    return {"ok": False, "error": "timeout", "data": {"creation_id": creation_id}}


async def publish_container(creation_id: str) -> dict[str, Any]:
    ok, missing, cfg = instagram_config_status()
    if not ok:
        return {"ok": False, "error": "missing_config", "missing": missing}

    url = f"{GRAPH_BASE_URL}/{cfg['ig_user_id']}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": cfg["access_token"],
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, timeout=60) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                return {"ok": False, "error": "publish_error", "status": resp.status, "data": data}
            return {"ok": True, "media_id": data.get("id"), "data": data}


async def publish_reel(video_url: str, caption: str) -> dict[str, Any]:
    container = await create_reel_container(video_url, caption)
    if not container.get("ok"):
        return container

    creation_id = container.get("creation_id")
    if not creation_id:
        return {"ok": False, "error": "no_creation_id", "data": container}

    ready = await wait_container_ready(creation_id)
    if not ready.get("ok"):
        ready["creation_id"] = creation_id
        return ready

    published = await publish_container(creation_id)
    published["creation_id"] = creation_id
    return published


async def create_image_container(image_url: str, caption: str = '') -> dict[str, Any]:
    """Create Instagram photo container. image_url must be public https URL, not data:image."""
    ok, missing, cfg = instagram_config_status()
    if not ok:
        return {"ok": False, "error": "missing_config", "missing": missing}
    if not image_url.startswith('http'):
        return {"ok": False, "error": "media_url_not_public", "message": "Instagram Graph API needs a public https image_url. data:image/base64 from OpenRouter must be uploaded to hosting first."}

    url = f"{GRAPH_BASE_URL}/{cfg['ig_user_id']}/media"
    payload = {"image_url": image_url, "caption": caption or '', "access_token": cfg["access_token"]}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, timeout=60) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                return {"ok": False, "error": "container_error", "status": resp.status, "data": data}
            return {"ok": True, "creation_id": data.get("id"), "data": data}


async def publish_photo(image_url: str, caption: str = '') -> dict[str, Any]:
    container = await create_image_container(image_url, caption)
    if not container.get('ok'):
        return container
    creation_id = container.get('creation_id')
    if not creation_id:
        return {"ok": False, "error": "no_creation_id", "data": container}
    published = await publish_container(creation_id)
    published['creation_id'] = creation_id
    return published


async def create_carousel_child(image_url: str) -> dict[str, Any]:
    ok, missing, cfg = instagram_config_status()
    if not ok:
        return {"ok": False, "error": "missing_config", "missing": missing}
    if not image_url.startswith('http'):
        return {"ok": False, "error": "media_url_not_public"}
    url = f"{GRAPH_BASE_URL}/{cfg['ig_user_id']}/media"
    payload = {"image_url": image_url, "is_carousel_item": "true", "access_token": cfg["access_token"]}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, timeout=60) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                return {"ok": False, "error": "child_container_error", "status": resp.status, "data": data}
            return {"ok": True, "creation_id": data.get("id"), "data": data}


async def publish_carousel(image_urls: list[str], caption: str = '') -> dict[str, Any]:
    ok, missing, cfg = instagram_config_status()
    if not ok:
        return {"ok": False, "error": "missing_config", "missing": missing}
    public_urls = [u for u in image_urls if isinstance(u, str) and u.startswith('http')]
    if len(public_urls) < 2:
        return {"ok": False, "error": "not_enough_public_images", "message": "Carousel publishing needs 2-10 public https image URLs."}

    children = []
    for u in public_urls[:10]:
        child = await create_carousel_child(u)
        if not child.get('ok'):
            return child
        children.append(child['creation_id'])

    url = f"{GRAPH_BASE_URL}/{cfg['ig_user_id']}/media"
    payload = {"media_type": "CAROUSEL", "children": ','.join(children), "caption": caption or '', "access_token": cfg["access_token"]}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, timeout=60) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                return {"ok": False, "error": "carousel_container_error", "status": resp.status, "data": data}
            creation_id = data.get('id')
    published = await publish_container(creation_id)
    published['creation_id'] = creation_id
    published['children'] = children
    return published
