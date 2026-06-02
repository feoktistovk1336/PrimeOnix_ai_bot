from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from keyboards import cabinet_menu

from database.db import (
    get_tariff_info,
    get_subscription_info,
    get_feature_limit,
    get_referral_stats,
    get_daily_usage
)


router = Router()


@router.message(F.text == "📊 Кабинет")
async def cabinet(message: Message):
    user_id = message.from_user.id
    ref_stats = await get_referral_stats(user_id)

    tariff = await get_tariff_info(user_id)
    sub = await get_subscription_info(user_id)

    features = [
        ("content_factory", "✍️ Посты"),
        ("post_image", "🖼 Пост+картинка"),
        ("carousel", "🎠 Карусели"),
        ("reels", "🎬 Reels"),
        ("ai_chat", "🤖 AI Чат"),
        ("content_pack", "🚀 Контент-пак"),
        ("rewrite", "✍️ Rewrite"),
        ("brand_rewrite", "🎭 Brand Voice"),
    ]

    limits_text = ""

    for feature, title in features:
        used = await get_daily_usage(user_id, feature)
        limit = await get_feature_limit(user_id, feature)
        limits_text += f"{title}: {used}/{limit}\n"

    await message.answer(
        "📊 Личный кабинет\n\n"
        f"Тариф: {tariff['title']}\n"
        f"Осталось дней: {sub['days_left']}\n"
        f"Дата окончания: {sub['pro_until'] or 'нет'}\n\n"
        f"🎁 Приглашено друзей: {ref_stats['total_referrals']}\n"
        f"⏳ Бонусных дней получено: {ref_stats['premium_days']}\n\n"
        "Лимиты на сегодня:\n"
        f"{limits_text}\n"
        "💡 Чтобы увеличить лимиты — открой «💎 Подписка».",

        reply_markup=cabinet_menu
    )