import asyncio
import os

from aiogram.types import FSInputFile

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


async def autopost_worker(bot):
    while True:
        try:
            if settings.CHANNEL_ID:
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

        except Exception as e:
            print(f"AUTOPOST WORKER ERROR: {e}")

        await asyncio.sleep(30)
