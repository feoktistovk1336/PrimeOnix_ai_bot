from aiogram import Router, F
from aiogram.types import Message

from database.db import get_referral_count, get_referral_stats


router = Router()


@router.message(F.text == "🎁 Пригласить друга")
async def referral_link(message: Message):
    user_id = message.from_user.id
    stats = await get_referral_stats(user_id)

    bot_username = (await message.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    await message.answer(
        "🎁 Пригласить друга\n\n"
        "Отправь ссылку другу и получи +3 дня Start Premium за каждого нового пользователя.\n\n"
        f"🔗 Твоя ссылка:\n`{link}`\n\n"
        f"👥 Уже приглашено: {stats['total_referrals']}",
        parse_mode="Markdown"
    )


@router.message(F.text == "🎁 Мои бонусы")
async def my_bonus(message: Message):
    stats = await get_referral_stats(message.from_user.id)

    await message.answer(
        "🎁 Мои бонусы\n\n"
        f"👥 Приглашено друзей: {stats['total_referrals']}\n"
        f"💎 Получено Premium-дней: {stats['premium_days']}\n\n"
        "Чем больше друзей — тем дольше доступ к Premium 🚀"
    )