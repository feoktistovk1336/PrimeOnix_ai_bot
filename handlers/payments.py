from aiogram import Router, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery

from database.db import (
    activate_tariff,
    get_subscription_info,
    get_tariff_info,
    get_feature_limit,
    get_daily_usage
)
from keyboards import tariffs_menu


router = Router()


TARIFFS_FOR_PAYMENT = {
    "💎 Start Premium": {"code": "start_premium", "title": "Start Premium", "stars": 119, "days": 30, "description": "3 поста, 2 поста с картинкой, 1 карусель, AI Чат 20/день"},
    "➕ Plus": {"code": "plus", "title": "Plus", "stars": 179, "days": 30, "description": "5 постов, 4 поста с картинкой, 1 карусель, AI Чат 50/день, очередь"},
    "🔥 VIP": {"code": "vip", "title": "VIP", "stars": 299, "days": 30, "description": "8 постов, 6 постов с картинкой, 2 карусели, 1 Reels, AI Чат 100/день"},
    "👑 Premium": {"code": "premium", "title": "Premium", "stars": 399, "days": 30, "description": "12 постов, 8 постов с картинкой, 3 карусели, 2 Reels, обучение стилю"},
    "🚀 PRO": {"code": "pro", "title": "PRO", "stars": 599, "days": 30, "description": "16 постов, 10 постов с картинкой, 4 карусели, 3 Reels, AI Чат 600/день"},
}


@router.message(F.text.in_({"💎 Подписка", "💎 PRO"}))
async def subscription(message: Message):
    await message.answer(
        """💎 <b>PrimeOnix подписки</b>

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

Выбери тариф кнопкой ниже 👇""",
        reply_markup=tariffs_menu,
        parse_mode="HTML",
    )


@router.message(F.text.in_(list(TARIFFS_FOR_PAYMENT.keys())))
async def buy_tariff(message: Message):
    tariff = TARIFFS_FOR_PAYMENT[message.text]

    await message.answer_invoice(
        title=f"Тариф {tariff['title']}",
        description=tariff["description"],
        payload=f"tariff:{tariff['code']}:{tariff['days']}",
        currency="XTR",
        prices=[
            LabeledPrice(
                label=tariff["title"],
                amount=tariff["stars"]
            )
        ],
        provider_token=""
    )


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if not payload.startswith("tariff:"):
        await message.answer("❌ Неизвестный платёж.")
        return

    _, tariff_code, days = payload.split(":")

    await activate_tariff(
        user_id=message.from_user.id,
        tariff=tariff_code,
        days=int(days)
    )

    await message.answer(
        "✅ Оплата прошла успешно\n\n"
        f"Тариф активирован: {tariff_code}\n"
        f"Срок: {days} дней"
    )


@router.message(F.text == "📊 Моя подписка")
async def my_subscription(message: Message):
    user_id = message.from_user.id

    info = await get_subscription_info(user_id)
    tariff = await get_tariff_info(user_id)

    features = [
        ("content_factory", "✍️ Посты"),
        ("post_image", "🖼 Пост+картинка"),
        ("carousel", "🎠 Карусели"),
        ("reels", "🎬 Reels"),
        ("ai_chat", "🤖 AI Чат"),
        ("content_pack", "🚀 Контент-пак"),
        ("rewrite", "✍️ Rewrite"),
        ("brand_rewrite", "🎭 Brand Voice")
    ]

    limits_text = ""

    for feature, title in features:
        limit = await get_feature_limit(user_id, feature)
        used = await get_daily_usage(user_id, feature)

        limits_text += f"{title}: {used}/{limit} в день\n"

    await message.answer(
        "📊 Моя подписка\n\n"
        f"Тариф: {tariff['title']}\n"
        f"Осталось дней: {info['days_left']}\n"
        f"Дата окончания: {info['pro_until'] or 'нет'}\n\n"
        "Лимиты:\n"
        f"{limits_text}"
    )