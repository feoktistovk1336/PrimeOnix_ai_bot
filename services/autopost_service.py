"""Legacy autopost helper.

The active scheduled-post worker is `services/autopost_worker.py`.
This module is kept safe for compatibility with older imports.
"""

from config import settings
from services.ai import ask_ai
from keyboards import post_action_buttons


async def auto_post(bot):
    """Generate and publish one simple text post to CHANNEL_ID.

    This helper is optional. It is not used by `main.py` by default.
    """
    if not settings.CHANNEL_ID:
        print("AUTOPOST SKIPPED: CHANNEL_ID is not set")
        return False

    try:
        text = await ask_ai(
            "Создай короткий полезный Telegram-пост для AI-SMM бота. "
            "Без markdown, с сильным хуком и CTA."
        )

        text = str(text or "").strip()

        if not text:
            print("AUTOPOST SKIPPED: generated empty text")
            return False

        await bot.send_message(
            chat_id=settings.CHANNEL_ID,
            text=text[:4000],
            reply_markup=post_action_buttons()
        )

        print("AUTOPOST SUCCESS")
        return True

    except Exception as e:
        print("AUTOPOST ERROR:", e)
        return False
