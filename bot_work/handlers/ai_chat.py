from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards import ai_chat_menu, main_menu, admin_main_menu
from database.db import (
    register_user,
    get_user_profile,
    get_user_style,
    can_use_feature,
    track_usage,
    get_feature_limit,
    get_daily_usage,
)
from services.assistant_chat import ask_primeonix_assistant
from services.sender import send_long

router = Router()


class AIChatState(StatesGroup):
    waiting_question = State()


def _home(user_id: int):
    return admin_main_menu if settings.ADMIN_ID and user_id == settings.ADMIN_ID else main_menu


async def _profile_block(user_id: int) -> str:
    profile = await get_user_profile(user_id)
    return (
        "AI Профиль пользователя:\n"
        f"Ниша: {profile.get('niche') or 'не указано'}\n"
        f"Аудитория: {profile.get('audience') or 'не указано'}\n"
        f"Оффер: {profile.get('offer') or 'не указано'}\n"
        f"Город: {profile.get('city') or 'не указано'}\n"
        f"CTA: {profile.get('cta') or 'не указано'}\n"
        f"Цель контента: {profile.get('content_goal') or 'не указано'}\n"
    )


async def _style_block(user_id: int) -> str:
    style = await get_user_style(user_id)
    return "Стиль пользователя:\n" + (style or "не обучен")[:2500]


@router.message(F.text == "🤖 AI Чат")
async def open_ai_chat(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AIChatState.waiting_question)
    await register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    limit = await get_feature_limit(message.from_user.id, "ai_chat")
    used = await get_daily_usage(message.from_user.id, "ai_chat")
    await message.answer(
        "🤖 AI Чат\n\n"
        "Можешь спрашивать меня как обычного помощника: про контент, бота, n8n, Instagram, Reels, идеи, тексты, продажи.\n\n"
        "Я учитываю твой AI Профиль и обученный стиль.\n"
        f"Лимит на сегодня: {used}/{limit} сообщений.\n\n"
        "Чтобы выйти — нажми «⬅️ Главное меню».",
        reply_markup=ai_chat_menu,
    )



AI_CHAT_MODES = {
    "💬 Общий помощник": "общий помощник",
    "📈 SMM консультант": "SMM консультант",
    "📱 Telegram": "Telegram консультант",
    "📸 Instagram": "Instagram консультант",
    "🎯 Воронки": "консультант по воронкам и продажам",
    "🤖 Нейросети/n8n": "консультант по нейросетям, n8n и автоматизации",
    "💼 Бизнес": "бизнес-консультант",
}


@router.message(AIChatState.waiting_question, F.text.in_(set(AI_CHAT_MODES.keys()) | {"📊 Лимит AI Чата"}))
async def ai_chat_mode_or_limit(message: Message, state: FSMContext):
    if message.text == "📊 Лимит AI Чата":
        used = await get_daily_usage(message.from_user.id, "ai_chat")
        limit = await get_feature_limit(message.from_user.id, "ai_chat")
        await message.answer(f"🤖 AI Чат: {used}/{limit} сообщений сегодня", reply_markup=ai_chat_menu)
        return
    await state.update_data(ai_chat_mode=AI_CHAT_MODES[message.text])
    await message.answer(
        f"✅ Режим выбран: {message.text}\n\nЗадай вопрос — отвечу как консультант, без генерации постов и без лишнего расхода OpenRouter.",
        reply_markup=ai_chat_menu,
    )

@router.message(AIChatState.waiting_question)
async def answer_ai_chat(message: Message, state: FSMContext):
    if message.text == "⬅️ Главное меню":
        await state.clear()
        await message.answer("Главное меню 👇", reply_markup=_home(message.from_user.id))
        return

    question = (message.text or message.caption or "").strip()
    if len(question) < 2:
        await message.answer("Напиши вопрос текстом 👇", reply_markup=ai_chat_menu)
        return

    if not await can_use_feature(message.from_user.id, "ai_chat"):
        limit = await get_feature_limit(message.from_user.id, "ai_chat")
        await message.answer(
            f"❌ Лимит AI Чата на сегодня закончился ({limit} сообщений).\n\n"
            "Открой 💎 PRO, чтобы увеличить лимит.",
            reply_markup=ai_chat_menu,
        )
        return

    await message.answer("🤖 Думаю...")
    profile = await _profile_block(message.from_user.id)
    style = await _style_block(message.from_user.id)
    data = await state.get_data()
    mode = data.get("ai_chat_mode", "общий помощник")
    try:
        answer = await ask_primeonix_assistant(question, profile, style, mode=mode)
    except Exception as exc:
        answer = f"⚠️ AI-чат не ответил. Ошибка: {exc}"
    await send_long(message, answer)
    await track_usage(message.from_user.id, "ai_chat")
    used = await get_daily_usage(message.from_user.id, "ai_chat")
    limit = await get_feature_limit(message.from_user.id, "ai_chat")
    await message.answer(
        f"Можешь задать следующий вопрос 👇\nAI Чат: {used}/{limit} сегодня",
        reply_markup=ai_chat_menu,
    )
