import asyncio
import os

from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo, InputMediaDocument

from config import settings
from database.db import get_due_posts, mark_post_published
from keyboards import post_action_buttons


def normalize_post_text(text):
    if text is None:
        return ""
    return str(text).strip()


async def publish_post(bot, post_id, text, image_path):
    text = normalize_post_text(text)

    if not text:
        print(f"AUTOPOST SKIPPED: post #{post_id} has empty text")
        await mark_post_published(post_id)
        return

    if image_path and os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(
            chat_id=settings.CHANNEL_ID,
            photo=photo,
            caption=text[:1024],
            reply_markup=post_action_buttons()
        )
        if len(text) > 1024:
            await bot.send_message(
                chat_id=settings.CHANNEL_ID,
                text=text,
                reply_markup=post_action_buttons()
            )
    else:
        await bot.send_message(
            chat_id=settings.CHANNEL_ID,
            text=text,
            reply_markup=post_action_buttons()
        )

    await mark_post_published(post_id)


def _media_input(media_type: str, file_id: str, caption: str | None = None):
    media_type = (media_type or "photo").lower()
    if media_type == "video":
        return InputMediaVideo(media=file_id, caption=caption)
    if media_type == "document":
        return InputMediaDocument(media=file_id, caption=caption)
    return InputMediaPhoto(media=file_id, caption=caption)


async def publish_prime_queue_item(bot, item: dict):
    """Publish scheduled items from services.content_queue to Telegram channel."""
    from services.content_queue import mark_prime_content, update_prime_content, STATUS_PUBLISHED, STATUS_FAILED

    item_id = int(item.get("id", 0) or 0)
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    text = normalize_post_text(item.get("content") or item.get("caption") or "")
    media_url = item.get("media_url") or meta.get("telegram_file_id") or meta.get("media_url")
    media_type = meta.get("media_type") or ("media" if media_url else "text")
    album_items = meta.get("album_items") if isinstance(meta.get("album_items"), list) else []

    try:
        if album_items:
            media = []
            for idx, m in enumerate(album_items[:10]):
                fid = m.get("telegram_file_id") or m.get("file_id") or m.get("media_url")
                if not fid:
                    continue
                caption = text[:1024] if idx == 0 and text else None
                media.append(_media_input(m.get("media_type") or "photo", fid, caption=caption))
            if media:
                await bot.send_media_group(chat_id=settings.CHANNEL_ID, media=media)
            elif text:
                await bot.send_message(chat_id=settings.CHANNEL_ID, text=text)
        elif media_url and media_type == "photo":
            await bot.send_photo(chat_id=settings.CHANNEL_ID, photo=media_url, caption=text[:1024] if text else None)
            if len(text) > 1024:
                await bot.send_message(chat_id=settings.CHANNEL_ID, text=text)
        elif media_url and media_type == "video":
            await bot.send_video(chat_id=settings.CHANNEL_ID, video=media_url, caption=text[:1024] if text else None)
            if len(text) > 1024:
                await bot.send_message(chat_id=settings.CHANNEL_ID, text=text)
        elif media_url and media_type == "document":
            await bot.send_document(chat_id=settings.CHANNEL_ID, document=media_url, caption=text[:1024] if text else None)
            if len(text) > 1024:
                await bot.send_message(chat_id=settings.CHANNEL_ID, text=text)
        else:
            await bot.send_message(chat_id=settings.CHANNEL_ID, text=text or f"Материал #{item_id}")

        mark_prime_content(item_id, STATUS_PUBLISHED)
        print(f"PRIME QUEUE PUBLISHED item_id={item_id}")
    except Exception as e:
        update_prime_content(item_id, status=STATUS_FAILED, error=str(e))
        print(f"PRIME QUEUE PUBLISH ERROR item_id={item_id}: {e}")


async def autopost_worker(bot):
    while True:
        try:
            if settings.CHANNEL_ID:
                # Legacy scheduled posts table
                posts = await get_due_posts()
                for post_id, text, image_path, publish_at in posts:
                    try:
                        await publish_post(
                            bot=bot,
                            post_id=post_id,
                            text=text,
                            image_path=image_path
                        )
                    except Exception as e:
                        print(f"AUTOPOST ERROR post_id={post_id}: {e}")

                # Prime content queue scheduled items
                try:
                    from services.content_queue import list_due_scheduled
                    due_items = list_due_scheduled(limit=10)
                    for item in due_items:
                        await publish_prime_queue_item(bot, item)
                except Exception as e:
                    print(f"PRIME QUEUE WORKER ERROR: {e}")

        except Exception as e:
            print(f"AUTOPOST WORKER ERROR: {e}")

        await asyncio.sleep(30)
