from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards import (
    main_menu,
    admin_main_menu,
    create_menu,
    content_menu,
    publish_plan_menu,
    subscription_menu,
    profile_menu,
    ig_tg_funnel_menu,
)

router = Router()


def _home_kb(user_id: int):
    return admin_main_menu if user_id == settings.ADMIN_ID else main_menu


PRO_TEXT = """💎 <b>PrimeOnix подписки</b>

Лимиты указаны на 1 день. Оплата — Telegram Stars.

🆓 <b>FREE — 0 Stars</b>
• Посты: 1
• Пост+картинка: 1
• Карусели: 0
• Reels: 0
• AI Чат: 10 сообщений
• Обучение стилю: нет
• Очередь: нет

💎 <b>Start Premium — 119 Stars / 30 дней</b>
• Посты: 3
• Пост+картинка: 2
• Карусели: 1
• Reels: 0
• AI Чат: 20 сообщений
• Для старта личного канала

➕ <b>Plus — 179 Stars / 30 дней</b>
• Посты: 5
• Пост+картинка: 4
• Карусели: 1
• Reels: 0
• AI Чат: 50 сообщений
• Очередь контента: да

🔥 <b>VIP — 299 Stars / 30 дней</b>
• Посты: 8
• Пост+картинка: 6
• Карусели: 2
• Reels: 1
• AI Чат: 100 сообщений
• Улучшенные картинки и приоритет

👑 <b>Premium — 399 Stars / 30 дней</b>
• Посты: 12
• Пост+картинка: 8
• Карусели: 3
• Reels: 2
• AI Чат: 300 сообщений
• Обучение стилю: 3 обучения/день
• Улучшенные карусели и Reels Generator PRO

🚀 <b>PRO — 599 Stars / 30 дней</b>
• Посты: 16
• Пост+картинка: 10
• Карусели: 4
• Reels: 3
• AI Чат: 600 сообщений
• Обучение стилю: без ограничений
• Очередь, приоритет, все новые функции

🤖 AI Чат работает через Groq и предназначен для консультаций: SMM, Telegram, Instagram, n8n, воронки, бизнес. Для генерации постов используй «🚀 Создать» или «📣 Контент Центр».

Выбери тариф кнопкой ниже 👇"""


@router.message(F.text.in_({"🚀 Создать", "🚀 Создать контент", "📦 Создать", "⬅️ Назад в создание"}))
async def ui_create(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🚀 <b>Создать контент</b>\n\n"
        "Генерация контента: посты, карусели, Reels, картинки и AI-инструменты.",
        reply_markup=create_menu,
        parse_mode="HTML",
    )


@router.message(F.text.in_({"🛠 Инструменты", "🛠 AI-инструменты", "📚 Контент"}))
async def ui_tools(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🛠 <b>Инструменты</b>\n\n"
        "Хуки, идеи, лид-магниты, rewrite, CTA, анализ и серии постов.",
        reply_markup=content_menu,
        parse_mode="HTML",
    )


@router.message(F.text.in_({"📲 Публикации", "📅 План и публикации", "⬅️ Назад в публикации"}))
async def ui_publish(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📲 <b>Публикации</b>\n\n"
        "Здесь связки Instagram → Telegram, пакеты публикаций, очередь и отложенные задачи.",
        reply_markup=publish_plan_menu,
        parse_mode="HTML",
    )


@router.message(F.text == "💎 PRO")
async def ui_pro(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(PRO_TEXT, reply_markup=subscription_menu, parse_mode="HTML")


@router.message(F.text == "🧠 AI Профиль")
async def ui_profile(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🧠 <b>AI Профиль</b>\n\n"
        "Здесь бот запоминает твою нишу, стиль, аудиторию, оффер и CTA.\n"
        "Чем лучше профиль — тем точнее посты, Reels и карусели.",
        reply_markup=profile_menu,
        parse_mode="HTML",
    )


@router.message(F.text == "🔗 IG→TG Воронка")
async def ui_ig_tg(message: Message, state: FSMContext):
    await state.clear()
    from handlers.ig_tg_funnel import IgTgFunnelState, IG_TG_INTRO_TEXT
    await state.set_state(IgTgFunnelState.waiting_type)
    await message.answer(IG_TG_INTRO_TEXT, reply_markup=ig_tg_funnel_menu, parse_mode="HTML")


@router.message(F.text.in_({"📲 Instagram пакет", "📲 Отправить в Instagram"}))
async def ui_instagram_package(message: Message, state: FSMContext):
    await state.clear()
    from handlers.prime_autopost import _send_last_to_n8n_publish
    await _send_last_to_n8n_publish(message, "publish_instagram", "instagram", "Instagram пакет")


@router.message(F.text.in_({"📣 Telegram пакет", "📣 Отправить в Telegram"}))
async def ui_telegram_package(message: Message, state: FSMContext):
    await state.clear()
    from handlers.prime_autopost import _send_last_to_n8n_publish
    await _send_last_to_n8n_publish(message, "publish_telegram", "telegram", "Telegram пакет")


@router.message(F.text == "⬅️ Главное меню")
async def ui_home(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню 👇", reply_markup=_home_kb(message.from_user.id))
