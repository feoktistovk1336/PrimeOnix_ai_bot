from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.admin import is_admin
from config import settings
from keyboards import (
    admin_menu,
    prime_panel_menu,
    prime_funnel_hub_menu,
    prime_content_hub_menu,
    prime_publish_hub_menu,
    prime_instagram_hub_menu,
    prime_agents_hub_menu,
    prime_system_hub_menu,
    prime_telegram_hub_menu,
    prime_broadcast_menu,
    prime_users_menu,
    prime_limits_menu,
    prime_publish_hub_menu,
    prime_stats_menu,
    prime_checks_menu,
    prime_after_generation_menu,
)


router = Router()

# Shared last generated material storage used by PRIME action buttons (improve/save/prepare).
from handlers.prime_viral import LAST_PRIME_RESULT


class AdminPrimeN8NState(StatesGroup):
    waiting_task_prompt = State()
    waiting_edit_prompt = State()



PRIME_PANEL_TEXT = (
    "👑 <b>PRIME PANEL</b>\n\n"
    "Это главный пульт твоей AI-SMM системы.\n\n"
    "Логика проекта:\n"
    "• <b>Telegram-бот</b> — ты управляешь и одобряешь\n"
    "• <b>n8n</b> — выполняет автоматизацию\n"
    "• <b>Instagram</b> — даёт трафик\n"
    "• <b>Telegram</b> — удерживает, прогревает и продаёт\n\n"
    "Чтобы не было хаоса, всё собрано по блокам 👇"
)


SYSTEM_MAP_TEXT = (
    "🧭 <b>Карта PRIME-системы</b>\n\n"
    "Вот что куда относится:\n\n"
    "🔗 <b>Воронки IG→TG</b>\n"
    "Создаёт связку: Reels/карусель/лид-магнит → кодовое слово → DM → Telegram-пост.\n\n"
    "🧠 <b>Генерация контента</b>\n"
    "Viral Reels, карусели, хуки, лид-магниты, AI-агенты.\n\n"
    "📦 <b>Очередь и публикации</b>\n"
    "Сохранить материал, подготовить к публикации, запланировать, отправить в TG/IG.\n\n"
    "📲 <b>Instagram / AutoPost</b>\n"
    "Проверка n8n/IG pipeline, подготовка Reels, отправка в Instagram, DM funnel.\n\n"
    "🤖 <b>Агенты и аналитика</b>\n"
    "AI-стратег, viral analyzer, анализ связок и улучшение контента.\n\n"
    "⚙️ <b>Система</b>\n"
    "Проверки n8n, Instagram, API и технических связок."
)


HUBS = {
    "🧭 Карта системы": (SYSTEM_MAP_TEXT, prime_panel_menu),
    "📣 Контент Центр": (
        "📣 <b>Контент Центр</b>\n\n"
        "Быстро создаём отдельные материалы: Telegram, Instagram, Reels, карусели, лид-магниты.\n\n"
        "Выбери формат 👇",
        prime_content_hub_menu,
    ),
    "📢 Telegram": (
        "📢 <b>Telegram</b>\n\n"
        "Отдельная ветка для Telegram: посты, картинки, серии, лид-магниты, прогрев и автопостинг.",
        prime_telegram_hub_menu,
    ),
    "📲 Instagram": (
        "📲 <b>Instagram</b>\n\n"
        "Отдельная ветка для Instagram: посты, карусели, Reels, обложки, caption и автопостинг.",
        prime_instagram_hub_menu,
    ),
    "🎯 Воронки IG→TG": (
        "🎯 <b>Воронки IG → TG</b>\n\n"
        "Instagram даёт охват → человек пишет кодовое слово → Telegram выдаёт конкретный материал.\n\n"
        "Выбери формат входа 👇",
        prime_funnel_hub_menu,
    ),
    "📬 Рассылки": (
        "📬 <b>Рассылки</b>\n\n"
        "Рассылки всем, PRO, FREE, по сегментам и по воронкам.",
        prime_broadcast_menu,
    ),
    "👥 Пользователи": (
        "👥 <b>Пользователи</b>\n\n"
        "Поиск пользователей, выдача PRO, бонусы, блокировка, история.",
        prime_users_menu,
    ),
    "💎 Подписки и лимиты": (
        "💎 <b>Подписки и лимиты</b>\n\n"
        "Выдача PRO, лимиты тарифов, бонусные генерации и сброс лимитов.",
        prime_limits_menu,
    ),
    "📦 Очередь": (
        "📦 <b>Очередь</b>\n\n"
        "Публикации, отложка, ошибки, готовые материалы и повтор публикаций.",
        prime_publish_hub_menu,
    ),
    "🤖 AI Лаборатория": (
        "🤖 <b>AI Лаборатория</b>\n\n"
        "Viral Reels, карусели, хуки, лид-магниты и тест промптов.",
        prime_agents_hub_menu,
    ),
    "📈 Статистика": (
        "📈 <b>Статистика</b>\n\n"
        "Это отдельный раздел с метриками. Выбери, какую статистику посмотреть 👇",
        prime_stats_menu,
    ),
    "🧪 Проверки": (
        "🧪 <b>Проверки</b>\n\n"
        "Это отдельный раздел диагностики связей. Нажимаешь кнопку — проверяем конкретную интеграцию 👇",
        prime_checks_menu,
    ),
    "⚙️ Система": (
        "⚙️ <b>Система</b>\n\n"
        "Технические настройки: webhooks, API, логи, интеграции и backup.",
        prime_system_hub_menu,
    ),
}


PRIME_SECTIONS = {
    "📈 Analytics": (
        "📈 <b>Analytics</b>\n\n"
        "Раздел аналитики контента, роста и воронок.\n\n"
        "Будем отслеживать:\n"
        "• охваты\n"
        "• сохранения\n"
        "• переходы в Telegram\n"
        "• лучшие темы\n"
        "• лучшие хуки\n"
        "• связки, которые стоит повторять\n\n"
        "Пока это информационный блок. Реальные метрики подключим после автопостинга."
    ),
}


@router.message(F.text.in_({"👑 Админ", "👑 PRIME PANEL", "🚀 PRIME PANEL"}))
async def open_prime_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.clear()
    await message.answer(PRIME_PANEL_TEXT, reply_markup=prime_panel_menu, parse_mode="HTML")


@router.message(F.text == "⬅️ Назад в PRIME PANEL")
async def back_to_prime_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer(PRIME_PANEL_TEXT, reply_markup=prime_panel_menu, parse_mode="HTML")


@router.message(F.text.in_(HUBS.keys()))
async def open_prime_hub(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.clear()
    text, keyboard = HUBS[message.text]

    if message.text in {"🎯 Воронки IG→TG", "🔗 Воронки IG→TG"}:
        from handlers.ig_tg_funnel import IgTgFunnelState
        await state.set_state(IgTgFunnelState.waiting_type)

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text.in_(PRIME_SECTIONS.keys()))
async def prime_panel_section(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.clear()
    await message.answer(PRIME_SECTIONS[message.text], reply_markup=prime_system_hub_menu, parse_mode="HTML")


N8N_ADMIN_TASKS = {
    "📢 Telegram пост": {"action": "telegram_post", "platform": "telegram", "workflow": "telegram", "content_type": "post", "keyboard": "telegram", "title": "📢 Telegram пост"},
    "🖼 TG пост + картинка": {"action": "telegram_post_image", "platform": "telegram", "workflow": "telegram", "content_type": "post_image", "keyboard": "telegram", "title": "🖼 TG пост + картинка"},
    "📚 Серия постов": {"action": "telegram_series", "platform": "telegram", "workflow": "telegram", "content_type": "series", "keyboard": "telegram", "title": "📚 Серия постов"},
    "🎁 Лид-магниты TG": {"action": "telegram_lead_magnet", "platform": "telegram", "workflow": "telegram", "content_type": "lead_magnet", "keyboard": "telegram", "title": "🎁 Лид-магнит TG"},
    "🚀 Прогрев TG": {"action": "telegram_warmup", "platform": "telegram", "workflow": "telegram", "content_type": "warmup", "keyboard": "telegram", "title": "🚀 Прогрев TG"},
    "🚀 Автопостинг TG": {"action": "telegram_autopost", "platform": "telegram", "workflow": "telegram", "content_type": "autopost", "keyboard": "telegram", "title": "🚀 Автопостинг TG"},
    "📷 Instagram пост": {"action": "instagram_post", "platform": "instagram", "workflow": "instagram", "content_type": "post", "keyboard": "instagram", "title": "📷 Instagram пост"},
    "🎠 Instagram карусель": {"action": "instagram_carousel", "platform": "instagram", "workflow": "carousel", "content_type": "carousel", "keyboard": "instagram", "title": "🎠 Instagram карусель"},
    "🎬 Instagram Reels": {"action": "instagram_reels", "platform": "instagram", "workflow": "reels", "content_type": "reels", "keyboard": "instagram", "title": "🎬 Instagram Reels"},
    "📅 Контент-план": {"action": "content_plan", "platform": "telegram", "workflow": "telegram", "content_type": "content_plan", "keyboard": "content", "title": "📅 Контент-план"},
    "🎬 Reels → Telegram": {"action": "funnel_reels_to_telegram", "platform": "ig_tg", "workflow": "funnel", "content_type": "reels_to_telegram", "keyboard": "funnel", "title": "🎬 Reels → Telegram"},
    "🎠 Карусель → Telegram": {"action": "funnel_carousel_to_telegram", "platform": "ig_tg", "workflow": "funnel", "content_type": "carousel_to_telegram", "keyboard": "funnel", "title": "🎠 Карусель → Telegram"},
    "📷 Пост → Telegram": {"action": "funnel_post_to_telegram", "platform": "ig_tg", "workflow": "funnel", "content_type": "post_to_telegram", "keyboard": "funnel", "title": "📷 Пост → Telegram"},
    "🎁 Лид-магнит → Telegram": {"action": "funnel_lead_magnet_to_telegram", "platform": "ig_tg", "workflow": "funnel", "content_type": "lead_magnet_to_telegram", "keyboard": "funnel", "title": "🎁 Лид-магнит → Telegram"},
    "📨 DM Funnel": {"action": "dm_funnel", "platform": "ig_tg", "workflow": "funnel", "content_type": "dm_funnel", "keyboard": "funnel", "title": "📨 DM Funnel"},
}


def _keyboard_by_key(key: str):
    return {
        "telegram": prime_telegram_hub_menu,
        "instagram": prime_instagram_hub_menu,
        "funnel": prime_funnel_hub_menu,
        "content": prime_content_hub_menu,
    }.get(key, prime_panel_menu)


ADMIN_ACTION_TEXTS = {
    "📢 Telegram пост": "WF Telegram Post: текст для Telegram.",
    "🖼 TG пост + картинка": "WF Telegram Post + Image: текст + картинка для Telegram.",
    "📚 Серия постов": "WF Telegram Series: серия постов для канала.",
    "🎁 Лид-магниты TG": "WF Lead Magnet: промпты, чек-лист, инструкция или мини-гайд.",
    "🚀 Прогрев TG": "WF Telegram Warm-up: welcome, доверие, экспертность, боль, решение, продажа.",
    "🚀 Автопостинг TG": "WF Telegram Auto Posting: публикация/отложка в Telegram.",
    "📷 Instagram пост": "WF Instagram Post: caption + visual + hashtags.",
    "🎠 Instagram карусель": "WF Instagram Carousel: cover + 8 слайдов + caption.",
    "🎬 Instagram Reels": "WF Instagram Reels: hook + script + cover + video prompt.",
    "📅 Контент-план": "WF Content Plan: 7/14/30 дней.",
    "🚀 Автопостинг IG": "WF Instagram Auto Posting: публикация в IG после подключения API.",
    "🎬 Reels → Telegram": "WF Funnel Reels → Telegram: Reels + keyword + DM + TG material.",
    "🎠 Карусель → Telegram": "WF Funnel Carousel → Telegram: карусель + CTA + TG material.",
    "📷 Пост → Telegram": "WF Funnel Post → Telegram: пост + keyword + TG material.",
    "🎁 Лид-магнит → Telegram": "WF Lead Magnet Delivery: выдача материала по funnel_id.",
    "📨 DM Funnel": "WF DM Funnel Handler: keyword → ответ → ссылка в Telegram.",
    "🧭 Все funnel_id": "Список и статистика funnel_id. Подключим к БД/n8n.",
    "📬 Новая рассылка": "WF Broadcast: новая рассылка.",
    "📣 Рассылка всем": "WF Broadcast: всем пользователям.",
    "💎 Рассылка PRO": "WF Broadcast: только PRO.",
    "🆓 Рассылка FREE": "WF Broadcast: только FREE.",
    "🎯 Рассылка по сегменту": "WF Broadcast: выбранный сегмент/воронка.",
    "👥 Список пользователей": "Админ: список пользователей. Подключим пагинацию.",
    "🔎 Найти пользователя": "Админ: поиск пользователя по ID/username.",
    "🚫 Забрать PRO": "Админ: забрать PRO у пользователя.",
    "➕ Выдать бонусы": "Админ: добавить бонусные генерации/дни.",
    "🔄 Сбросить лимиты": "Админ: сбросить лимиты пользователя.",
    "📊 Проверить подписку": "Админ: проверка тарифа и лимитов пользователя.",
    "🧪 Проверить OpenRouter": "Проверка OpenRouter через n8n/system webhook.",
    "🧪 Проверить Telegram Bot": "Проверка Telegram Bot статуса.",
    "🔗 Webhooks n8n": "Список webhook-переменных Railway/n8n.",
    "📜 Логи": "Логи ошибок и последних запусков.",
    "🕒 Запланированные": "Раздел запланированных рассылок. Здесь будут будущие рассылки и расписание.",
    "📜 История рассылок": "История рассылок: дата, сегмент, текст, отправлено, ошибки.",
    "⚙️ Лимиты FREE": "Настройка лимитов FREE: посты, картинки, rewrite, карусели, Reels.",
    "⚙️ Лимиты PRO": "Настройка лимитов PRO: расширенные лимиты, воронки, автопостинг, приоритет.",
    "👥 Статистика пользователей": "Показывает: всего, новые, активные, FREE, PRO, заблокированные.",
    "⚡ Статистика генераций": "Показывает генерации: посты, картинки, карусели, Reels, лид-магниты.",
    "💎 Статистика подписок": "Показывает подписки: FREE, Plus, Premium, PRO, истекающие, оплаты.",
    "📈 Статистика лимитов": "Показывает использование лимитов по тарифам и пользователям.",
    "🎯 Статистика воронок": "Показывает funnel_id, переходы IG→TG, keyword, выдачи лид-магнитов.",
    "📲 Статистика Instagram": "Показывает Instagram-материалы, карусели, Reels и ошибки публикаций.",
    "📢 Статистика Telegram": "Показывает Telegram-посты, лид-магниты, подписчиков и активность.",
    "🚨 Ошибки n8n": "Показывает ошибки workflow, таймауты, неудачные публикации и повторы.",
    "🧪 Проверить n8n": "Проверка доступности n8n system webhook.",
    "🧪 Проверить Image Generator": "Проверка генерации картинок через OpenRouter/image workflow.",
    "🧪 Проверить Video Generator": "Проверка видео workflow для Reels.",
}


@router.message(F.text.in_(ADMIN_ACTION_TEXTS.keys()))
async def admin_action_placeholder(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.clear()

    if message.text in N8N_ADMIN_TASKS:
        task = N8N_ADMIN_TASKS[message.text]
        await state.update_data(admin_n8n_task=task)
        await state.set_state(AdminPrimeN8NState.waiting_task_prompt)
        await message.answer(
            f"{task['title']}\n\n"
            "Напиши тему, нишу, продукт или задачу 👇\n\n"
            "Я отправлю это в нужный n8n workflow и верну готовый пакет.",
            reply_markup=_keyboard_by_key(task.get('keyboard', '')),
        )
        return

    if message.text in {"📬 Новая рассылка", "📣 Рассылка всем", "💎 Рассылка PRO", "🆓 Рассылка FREE", "🎯 Рассылка по сегменту"}:
        from handlers.admin import AdminState
        await state.set_state(AdminState.waiting_broadcast_text)
        await message.answer(
            f"📬 <b>{message.text}</b>\n\n"
            "Отправь текст рассылки. После подключения n8n этот маршрут сможет отправлять по выбранному сегменту.",
            reply_markup=prime_broadcast_menu,
            parse_mode="HTML",
        )
        return

    # Real diagnostics must call n8n/Telegram immediately, not show old placeholder text.
    if message.text == "🧪 Проверить n8n":
        from services.n8n_client import ping_n8n
        await message.answer("🧪 Проверяю n8n system webhook...")
        result = await ping_n8n()
        if result.get("ok"):
            await message.answer(
                "✅ n8n отвечает.\n\n"
                f"HTTP status: {result.get('status')}\n"
                f"Ответ: {result.get('text') or result.get('raw')}",
                reply_markup=prime_checks_menu,
            )
        else:
            await message.answer(
                "❌ n8n не ответил как надо.\n\n"
                f"Ошибка: {result.get('error')}\n"
                f"Детали: {result.get('message') or result.get('raw') or result.get('data')}",
                reply_markup=prime_checks_menu,
            )
        return

    if message.text == "🧪 Проверить Telegram Bot":
        me = await message.bot.get_me()
        await message.answer(
            "✅ Telegram Bot отвечает.\n\n"
            f"@{me.username}\n"
            f"ID: {me.id}",
            reply_markup=prime_checks_menu,
        )
        return

    if message.text in {"🧪 Проверить OpenRouter", "🧪 Проверить IG Pipeline", "🧪 Проверить Image Generator", "🧪 Проверить Video Generator"}:
        from services.n8n_client import call_n8n
        action_map = {
            "🧪 Проверить OpenRouter": "check_openrouter",
            "🧪 Проверить IG Pipeline": "check_instagram_pipeline",
            "🧪 Проверить Image Generator": "check_image_generator",
            "🧪 Проверить Video Generator": "check_video_generator",
        }
        await message.answer(f"🧪 Отправляю тест: {message.text}...")
        result = await call_n8n({
            "action": action_map[message.text],
            "source": "telegram_bot",
            "platform": "instagram" if "IG" in message.text else "telegram",
            "message": "PrimeOnix integration diagnostic test",
        }, timeout=45)
        if result.get("ok"):
            await message.answer(
                "✅ Проверка прошла.\n\n"
                f"HTTP status: {result.get('status')}\n"
                f"Ответ: {result.get('text') or result.get('raw')}",
                reply_markup=prime_checks_menu,
            )
        else:
            await message.answer(
                "❌ Проверка не прошла.\n\n"
                f"Ошибка: {result.get('error')}\n"
                f"Детали: {result.get('message') or result.get('raw') or result.get('data')}",
                reply_markup=prime_checks_menu,
            )
        return

    if message.text == "🔗 Webhooks n8n":
        from services.n8n_client import n8n_config_status
        ok, missing, cfg = n8n_config_status({"action": "ping"})
        lines = ["🔗 <b>Webhooks n8n</b>", "", f"Статус: {'✅ настроено' if ok else '⚠️ не хватает ' + ', '.join(missing)}", ""]
        for key, value in cfg.items():
            lines.append(f"• {key}: {'✅' if value else '❌'}")
        await message.answer("\n".join(lines), reply_markup=prime_checks_menu, parse_mode="HTML")
        return

    section_keyboard = prime_panel_menu
    text_info = ADMIN_ACTION_TEXTS[message.text]
    if message.text in {"👥 Статистика пользователей", "⚡ Статистика генераций", "💎 Статистика подписок", "📈 Статистика лимитов", "🎯 Статистика воронок", "📲 Статистика Instagram", "📢 Статистика Telegram", "🚨 Ошибки n8n"}:
        section_keyboard = prime_stats_menu
    elif message.text in {"🧪 Проверить n8n", "🧪 Проверить OpenRouter", "🧪 Проверить Telegram Bot", "🧪 Проверить IG Pipeline", "🧪 Проверить Image Generator", "🧪 Проверить Video Generator", "🔗 Webhooks n8n", "📜 Логи"}:
        section_keyboard = prime_checks_menu
    elif message.text in {"🕒 Запланированные", "📜 История рассылок"}:
        section_keyboard = prime_broadcast_menu
    elif "Telegram" in text_info or "TG" in text_info:
        section_keyboard = prime_telegram_hub_menu
    elif "Instagram" in text_info or "IG" in text_info:
        section_keyboard = prime_instagram_hub_menu
    elif "Funnel" in text_info or "funnel" in text_info or "ворон" in text_info.lower():
        section_keyboard = prime_funnel_hub_menu
    elif "Broadcast" in text_info or "рассыл" in text_info.lower():
        section_keyboard = prime_broadcast_menu
    elif "лимит" in text_info.lower() or "PRO" in message.text:
        section_keyboard = prime_limits_menu

    await message.answer(
        f"✅ <b>{message.text}</b>\n\n"
        f"{text_info}\n\n"
        "Раздел открыт. Если это действие должно запускать n8n — выбери нужную кнопку и отправь тему/задачу.",
        reply_markup=section_keyboard,
        parse_mode="HTML",
    )


@router.message(AdminPrimeN8NState.waiting_task_prompt)
async def admin_prime_run_n8n_task(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        await state.clear()
        return

    text = (message.text or "").strip()

    # If admin presses another admin task while waiting, switch mode instead of treating the button as prompt.
    if text in N8N_ADMIN_TASKS:
        task = N8N_ADMIN_TASKS[text]
        await state.update_data(admin_n8n_task=task)
        await state.set_state(AdminPrimeN8NState.waiting_task_prompt)
        await message.answer(
            f"{task['title']}\n\n"
            "Режим переключён. Напиши тему, нишу, продукт или задачу 👇",
            reply_markup=_keyboard_by_key(task.get('keyboard', '')),
        )
        return

    # Navigation buttons should work normally from this waiting state.
    if text in HUBS:
        await state.clear()
        hub_text, hub_keyboard = HUBS[text]
        await message.answer(hub_text, reply_markup=hub_keyboard, parse_mode="HTML")
        return
    if text in {"⬅️ Назад в админку", "⬅️ Назад в PRIME PANEL", "❌ Отмена"}:
        await state.clear()
        await message.answer(PRIME_PANEL_TEXT, reply_markup=prime_panel_menu, parse_mode="HTML")
        return

    if not text:
        await message.answer("Напиши тему или задачу текстом.")
        return

    data = await state.get_data()
    task = data.get("admin_n8n_task") or {}
    if not task:
        await state.clear()
        await message.answer("⚠️ Режим потерян. Выбери действие заново.", reply_markup=prime_panel_menu)
        return

    from services.n8n_client import call_n8n

    await message.answer(f"🚀 Отправляю в n8n: {task.get('title', 'задача')}...")
    result = await call_n8n({
        "action": task.get("action"),
        "workflow": task.get("workflow"),
        "platform": task.get("platform"),
        "content_type": task.get("content_type"),
        "source": "telegram_bot_admin",
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "topic": text,
        "prompt": text,
        "message": text,
        "expected_response": {"text": "Human-readable generated package for Telegram"},
    }, timeout=120)

    await state.clear()
    section_keyboard = _keyboard_by_key(task.get("keyboard", ""))
    if result.get("ok"):
        answer = result.get("text") or result.get("raw") or "n8n принял задачу и вернул пустой ответ."
        data_payload = result.get("data") if isinstance(result.get("data"), dict) else {}
        image_url = (
            data_payload.get("image_url")
            or data_payload.get("media_url")
            or data_payload.get("cover_url")
        )

        # Сохраняем последний материал, чтобы после генерации работали кнопки:
        # улучшить, усилить хук, сохранить в очередь, подготовить к публикации.
        LAST_PRIME_RESULT[message.from_user.id] = {
            "tool": task.get("title", "PRIME"),
            "topic": text,
            "content": answer,
            "platform": task.get("platform"),
            "content_type": task.get("content_type"),
            "workflow": task.get("workflow"),
            "action": task.get("action"),
            "keyboard": task.get("keyboard"),
            "source": "n8n",
            "image_url": image_url,
            "media_url": image_url,
            "raw": data_payload,
        }

        # Для обычного поста отправляем только текст.
        # Для TG пост + картинка дополнительно отправляем изображение из n8n.
        if task.get("content_type") == "post_image" and image_url:
            try:
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=image_url,
                    caption="🖼 Картинка к Telegram-посту",
                )
            except Exception:
                await message.answer(f"🖼 Картинка сгенерирована, но Telegram не смог загрузить её как фото:\n{image_url}")

        await message.answer(
            f"✅ {task.get('title', 'Задача')} готово.\n\n"
            f"HTTP status: {result.get('status')}\n\n"
            f"{answer}",
            reply_markup=prime_after_generation_menu,
        )
        await message.answer(
            "Что делаем дальше? 👇",
            reply_markup=prime_after_generation_menu,
        )
    else:
        await message.answer(
            f"❌ n8n не обработал: {task.get('title', 'задача')}\n\n"
            f"Ошибка: {result.get('error')}\n"
            f"Детали: {result.get('message') or result.get('raw') or result.get('data')}",
            reply_markup=section_keyboard,
        )


# =========================
# AFTER GENERATION ACTIONS — publish/transform/queue/edit/regenerate
# =========================

def _last_material(user_id: int):
    return LAST_PRIME_RESULT.get(user_id)


def _short_caption(text: str, limit: int = 1024) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


async def _require_last_material(message: Message):
    last = _last_material(message.from_user.id)
    if not last:
        await message.answer(
            "⚠️ Сначала сгенерируй материал: пост, пост с картинкой, карусель или Reels.",
            reply_markup=prime_panel_menu,
        )
        return None
    return last


@router.message(F.text == "📤 Опубликовать в Telegram")
async def publish_last_to_telegram_channel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    last = await _require_last_material(message)
    if not last:
        return
    if not settings.CHANNEL_ID:
        await message.answer(
            "⚠️ CHANNEL_ID не указан в Railway/.env. Добавь CHANNEL_ID канала и сделай redeploy бота.",
            reply_markup=prime_after_generation_menu,
        )
        return

    content = last.get("content") or ""
    image_url = last.get("image_url") or last.get("media_url")
    try:
        if image_url:
            await message.bot.send_photo(
                chat_id=settings.CHANNEL_ID,
                photo=image_url,
                caption=_short_caption(content),
            )
            if len(content) > 1024:
                await message.bot.send_message(chat_id=settings.CHANNEL_ID, text=content)
        else:
            await message.bot.send_message(chat_id=settings.CHANNEL_ID, text=content)
        await message.answer("✅ Опубликовано в Telegram-канал.", reply_markup=prime_after_generation_menu)
    except Exception as exc:
        await message.answer(
            f"❌ Не удалось опубликовать в Telegram.\n\nОшибка: {exc}\n\nПроверь, что бот добавлен админом в канал и CHANNEL_ID указан правильно.",
            reply_markup=prime_after_generation_menu,
        )


@router.message(F.text == "📲 Опубликовать в Instagram")
async def publish_last_to_instagram(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    last = await _require_last_material(message)
    if not last:
        return

    # Пока Meta/Instagram API не подключены полностью, безопасно готовим пакет через n8n.
    from services.n8n_client import call_n8n
    await message.answer("📲 Готовлю Instagram-пакет через n8n...")
    result = await call_n8n({
        "action": "publish_instagram_prepare",
        "workflow": "instagram",
        "platform": "instagram",
        "content_type": last.get("content_type") or "post",
        "source": "telegram_bot_admin",
        "user_id": message.from_user.id,
        "topic": last.get("topic"),
        "content": last.get("content"),
        "media_url": last.get("image_url") or last.get("media_url"),
        "expected_response": {"text": "Instagram package ready for publishing"},
    }, timeout=120)
    if result.get("ok"):
        await message.answer(
            "✅ Instagram-пакет подготовлен.\n\n"
            "Автопубликацию включим после полного подключения Meta/Metricool.\n\n"
            f"{result.get('text') or result.get('raw') or ''}",
            reply_markup=prime_after_generation_menu,
        )
    else:
        await message.answer(
            f"❌ Instagram-пакет не подготовлен.\nОшибка: {result.get('error')}\nДетали: {result.get('message') or result.get('raw') or result.get('data')}",
            reply_markup=prime_after_generation_menu,
        )


@router.message(F.text == "🖼 Сгенерировать картинку")
async def generate_image_for_last(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    last = await _require_last_material(message)
    if not last:
        return
    from services.n8n_client import call_n8n
    await message.answer("🖼 Генерирую картинку по смыслу последнего материала...")
    result = await call_n8n({
        "action": "telegram_post_image",
        "workflow": "telegram",
        "platform": "telegram",
        "content_type": "post_image",
        "source": "telegram_bot_admin",
        "user_id": message.from_user.id,
        "topic": last.get("topic"),
        "prompt": last.get("topic"),
        "content": last.get("content"),
        "expected_response": {"image_url": "generated image URL", "text": "caption"},
    }, timeout=120)
    if result.get("ok"):
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        image_url = data.get("image_url") or data.get("media_url") or data.get("cover_url")
        text = result.get("text") or result.get("raw") or last.get("content") or ""
        if image_url:
            LAST_PRIME_RESULT[message.from_user.id].update({"image_url": image_url, "media_url": image_url, "content": text})
            try:
                await message.bot.send_photo(message.chat.id, image_url, caption="🖼 Картинка готова")
            except Exception:
                await message.answer(f"🖼 Картинка готова, но Telegram не загрузил фото:\n{image_url}")
        await message.answer(f"✅ Картинка добавлена к материалу.\n\n{text}", reply_markup=prime_after_generation_menu)
    else:
        await message.answer(f"❌ Картинка не сгенерировалась: {result.get('error')}", reply_markup=prime_after_generation_menu)


@router.message(F.text == "🎬 Сгенерировать Reels")
async def generate_reels_from_last(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    last = await _require_last_material(message)
    if not last:
        return
    from services.n8n_client import call_n8n
    await message.answer("🎬 Делаю Reels-сценарий из смысла последнего материала...")
    result = await call_n8n({
        "action": "reels_from_existing_content",
        "workflow": "reels",
        "platform": "instagram",
        "content_type": "reels",
        "source": "telegram_bot_admin",
        "user_id": message.from_user.id,
        "topic": last.get("topic"),
        "prompt": last.get("topic"),
        "source_content": last.get("content"),
        "media_url": last.get("image_url") or last.get("media_url"),
        "expected_response": {"text": "Reels script based on existing content"},
    }, timeout=120)
    if result.get("ok"):
        answer = result.get("text") or result.get("raw") or "Reels готов."
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        LAST_PRIME_RESULT[message.from_user.id] = {
            "tool": "🎬 Reels из материала",
            "topic": last.get("topic"),
            "content": answer,
            "platform": "instagram",
            "content_type": "reels",
            "workflow": "reels",
            "source": "n8n",
            "image_url": data.get("cover_url") or data.get("media_url"),
            "raw": data,
        }
        await message.answer(f"✅ Reels готов.\n\n{answer}", reply_markup=prime_after_generation_menu)
    else:
        await message.answer(f"❌ Reels не сгенерировался: {result.get('error')}", reply_markup=prime_after_generation_menu)


@router.message(F.text == "📅 В очередь контента")
async def save_last_to_content_queue(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    last = await _require_last_material(message)
    if not last:
        return
    from services.content_queue import add_prime_content, STATUS_READY
    item = add_prime_content(
        user_id=message.from_user.id,
        tool=last.get("tool", "PRIME"),
        topic=last.get("topic", "Без темы"),
        content=last.get("content", ""),
        status=STATUS_READY,
        platform=last.get("platform") or "telegram",
        content_type=last.get("content_type"),
        caption=last.get("content"),
        media_url=last.get("image_url") or last.get("media_url"),
        meta={"source": last.get("source", "telegram_bot"), "raw": last.get("raw", {})},
    )
    await message.answer(
        f"✅ Материал сохранён в очередь контента.\n\nID: {item['id']}\nСтатус: {item['status']}",
        reply_markup=prime_after_generation_menu,
    )


@router.message(F.text == "✏️ Редактировать")
async def edit_last_material_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    last = await _require_last_material(message)
    if not last:
        return
    await state.set_state(AdminPrimeN8NState.waiting_edit_prompt)
    await message.answer(
        "✏️ Напиши, что изменить в последнем материале.\n\n"
        "Например: сделай короче, добавь больше конкретики, убери продажность, сделай стиль спокойнее.",
        reply_markup=prime_after_generation_menu,
    )


@router.message(AdminPrimeN8NState.waiting_edit_prompt)
async def edit_last_material_apply(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    instruction = (message.text or "").strip()
    if instruction in {"⬅️ Назад в админку", "❌ Отмена"}:
        await state.clear()
        await message.answer(PRIME_PANEL_TEXT, reply_markup=prime_panel_menu, parse_mode="HTML")
        return
    last = await _require_last_material(message)
    if not last:
        await state.clear()
        return
    from services.n8n_client import call_n8n
    await message.answer("✏️ Редактирую через n8n...")
    result = await call_n8n({
        "action": "edit_existing_content",
        "workflow": last.get("workflow") or "telegram",
        "platform": last.get("platform") or "telegram",
        "content_type": last.get("content_type") or "post",
        "source": "telegram_bot_admin",
        "user_id": message.from_user.id,
        "topic": last.get("topic"),
        "content": last.get("content"),
        "edit_instruction": instruction,
        "prompt": f"Отредактируй материал по инструкции: {instruction}",
    }, timeout=120)
    await state.clear()
    if result.get("ok"):
        answer = result.get("text") or result.get("raw") or "Материал отредактирован."
        LAST_PRIME_RESULT[message.from_user.id].update({"content": answer, "source": "n8n_edit"})
        await message.answer(f"✅ Отредактировано.\n\n{answer}", reply_markup=prime_after_generation_menu)
    else:
        await message.answer(f"❌ Не получилось отредактировать: {result.get('error')}", reply_markup=prime_after_generation_menu)


@router.message(F.text == "🔁 Перегенерировать")
async def regenerate_last_material(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    last = await _require_last_material(message)
    if not last:
        return
    from services.n8n_client import call_n8n
    await message.answer("🔁 Перегенерирую заново с проверкой качества...")
    result = await call_n8n({
        "action": last.get("action") or "regenerate_content",
        "workflow": last.get("workflow") or "telegram",
        "platform": last.get("platform") or "telegram",
        "content_type": last.get("content_type") or "post",
        "source": "telegram_bot_admin",
        "user_id": message.from_user.id,
        "topic": last.get("topic"),
        "prompt": last.get("topic"),
        "regenerate": True,
        "previous_content": last.get("content"),
    }, timeout=120)
    if result.get("ok"):
        answer = result.get("text") or result.get("raw") or "Материал перегенерирован."
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        image_url = data.get("image_url") or data.get("media_url") or data.get("cover_url") or last.get("image_url")
        LAST_PRIME_RESULT[message.from_user.id].update({"content": answer, "image_url": image_url, "media_url": image_url, "raw": data, "source": "n8n_regenerate"})
        await message.answer(f"✅ Перегенерировано.\n\n{answer}", reply_markup=prime_after_generation_menu)
    else:
        await message.answer(f"❌ Не получилось перегенерировать: {result.get('error')}", reply_markup=prime_after_generation_menu)


@router.message(F.text == "⬅️ Назад в админку")
async def back_to_admin_from_prime(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer("👑 Админ-панель", reply_markup=admin_menu)
