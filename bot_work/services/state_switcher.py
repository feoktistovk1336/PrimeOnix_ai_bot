USER_GLOBAL_BUTTONS = [
    "📦 Создать",
    "📚 Контент",
    "🧠 AI Профиль",
    "💎 Подписка",
    "📊 Кабинет",
    "👑 Админ",
    "⬅️ Главное меню",
    "⬅️ Назад в создание",
    "⬅️ Назад в профиль",
    "⬅️ Назад в контент",

    "✍️ Пост",
    "🖼 Пост с картинкой",
    "🎠 Карусель",
    "🎬 Reels",
    "🚀 Контент-пак",
    "💡 Идеи контента",
    "📅 Контент-план",
    "🎯 Viral Hooks",
    "🎯 Воронка продаж",
    "📅 Серия постов",
    "🚀 AI CTA",
    "✍️ Rewrite",
    "🎁 Лид-магнит",
    "🔎 Анализ поста",

    "🚀 PRIME PANEL",
    "🔗 IG→TG Воронка",
    "🎬 Viral Reels",
    "🎠 Viral Carousels",
    "🎯 Hook Generator",
    "🎁 Lead Magnet Lab",
    "📌 Контент-очередь",
    "📤 AutoPost Center",
    "⬅️ Назад в PRIME PANEL",
]


async def cancel_if_global_button(message, state):
    if message.text not in USER_GLOBAL_BUTTONS:
        return False

    await state.clear()

    await message.answer(
        "Ок, предыдущее действие отменено.\n\n"
        "Нажми нужную кнопку ещё раз."
    )

    return True
