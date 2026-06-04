from aiogram import Router, F
from aiogram.types import Message

from database.db import can_use_feature, track_usage, register_user
from services.ai import ask_ai


router = Router()


@router.message(F.text == "✍️ Rewrite")
async def rewrite_button(message: Message):
    await message.answer(
        "✍️ Rewrite\n\n"
        "Отправь:\n"
        "/rewrite твой текст"
    )


@router.message(F.text.startswith("/rewrite"))
async def rewrite_handler(message: Message):
    user_id = message.from_user.id
    text = message.text.replace("/rewrite", "", 1).strip()

    if not text:
        await message.answer("Пример:\n/rewrite Сделай пост про AI для бизнеса")
        return

    if not await can_use_feature(user_id, "rewrite"):
        await message.answer("❌ Лимит FREE закончился. Оформи PRO.")
        return

    await register_user(user_id, message.from_user.username, message.from_user.first_name)

    await message.answer("🧠 Улучшаю текст...")

    prompt = f"""
Перепиши текст красиво для Telegram.

Исходный текст:
{text}

Сделай:
живее, сильнее, понятнее, дороже.

Запрещено:
markdown, звёздочки, ###, таблицы, палочки.

Нужно:
эмодзи, короткие абзацы, сильный хук, нормальный человеческий стиль.
"""

    result = await ask_ai(prompt)

    await track_usage(user_id, "rewrite")
    await message.answer(result)