from __future__ import annotations

from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards import (
    main_menu,
    admin_main_menu,
    create_menu,
    content_menu,
    profile_menu,
    style_menu,
    subscription_menu,
    admin_menu,
    prime_panel_menu,
    ig_tg_funnel_menu,
    prime_instagram_hub_menu,
    publish_plan_menu,
    prime_topic_menu,
    image_style_menu,
    carousel_style_menu,
    goal_menu,
    prime_broadcast_menu,
    prime_users_menu,
    prime_limits_menu,
    prime_publish_hub_menu,
)


def is_owner(user_id: int | None) -> bool:
    return bool(user_id and settings.ADMIN_ID is not None and user_id == settings.ADMIN_ID)


def home_menu(user_id: int | None):
    return admin_main_menu if is_owner(user_id) else main_menu


MAIN_BUTTONS = {
    "🚀 Создать", "🚀 Создать контент", "📦 Создать", "🛠 Инструменты", "🛠 AI-инструменты", "📚 Контент",
    "📲 Публикации", "📅 План и публикации", "🧠 AI Профиль", "📊 Кабинет", "💎 PRO", "💎 Подписка",
    "👑 Админ", "⬅️ Главное меню", "⬅️ Назад в создание", "⬅️ Назад в профиль", "⬅️ Назад в публикации",
}

CREATE_BUTTONS = {"✍️ Пост", "🖼 Пост с картинкой", "🖼 Пост + картинка", "🎠 Карусель", "🎬 Reels", "🚀 Контент-пак"}
CONTENT_BUTTONS = {
    "💡 Идеи", "💡 Идеи контента", "📅 Контент-план", "🔎 Анализ поста", "🎯 Viral Hooks", "🎯 Воронка продаж",
    "📅 Серия постов", "🚀 AI CTA", "🎁 Лид-магнит", "✍️ Rewrite", "🎭 Brand Voice",
}
PROFILE_BUTTONS = {
    "⚙️ Быстрая настройка", "🎭 Стиль", "🎭 Стиль текста", "🎨 Стиль визуала", "🎯 Цель контента", "🏢 Ниша", "🎯 Аудитория", "💎 Оффер", "📢 CTA", "📋 Мой профиль",
    "❌ Сбросить профиль", "🗑 Сбросить профиль", "✍️ Опиши стиль", "🧠 Обучить стилю", "🎭 Мой стиль",
    "♻️ Сбросить стиль", "❌ Сбросить стиль",
}
ADMIN_BUTTONS = {
    "📣 Автопостинг", "🚀 PRIME PANEL", "💎 Выдать PRO", "⚙️ Лимиты", "📊 Статистика", "📢 Рассылка",
    "📊 Аналитика", "⬅️ Назад в админку",
}
PRIME_BUTTONS = {
    "🧭 Карта системы", "🔗 Воронки IG→TG", "🧠 Генерация", "🧠 Генерация контента", "📦 Очередь", "📦 Очередь и публикации",
    "📲 Instagram", "📲 Instagram / AutoPost", "⚙️ Система", "⬅️ Назад в PRIME PANEL", "❌ Отмена",
    "🔗 IG→TG Воронка", "🎬 Reels → Telegram", "🎠 Карусель → Telegram", "🎁 Лид-магнит → Telegram",
    "🎬 Viral Reels", "🎠 Viral Carousels", "🎯 Hook Generator", "🎁 Lead Magnet Lab", "📈 Analytics",
    "🔁 Улучшить", "🔥 Усилить хук", "🧲 Усилить CTA", "🔗 TG-продолжение", "📌 Сохранить в очередь",
    "🕒 Посмотреть очередь", "📤 Подготовить к публикации", "🚀 Отправить в n8n",
    "📲 Подключение Instagram", "🧪 Проверить n8n", "🧪 Проверить Instagram API", "🧪 Проверить IG Pipeline",
    "📤 Подготовить Reels к IG", "📲 Instagram пакет", "📣 Telegram пакет", "📲 Отправить в Instagram", "📣 Отправить в Telegram", "🚀 Запустить автопостинг",
    "📨 DM Funnel", "📅 Публикация позже", "📌 Очередь публикаций", "📌 Контент-очередь", "📌 Сохранить как готово к IG",
    "📤 Опубликовать Reels по URL", "📲 Instagram пакет", "📣 Telegram пакет", "📤 AutoPost Center", "⬅️ AutoPost Center",
    "📣 Контент Центр", "📢 Telegram", "🎯 Воронки IG→TG", "📬 Рассылки", "👥 Пользователи", "💎 Подписки и лимиты",
    "📈 Статистика", "📦 Очередь", "🤖 AI Лаборатория", "🧪 Проверки", "🧪 Проверка системы", "🧭 Карта системы",
    "📬 Новая рассылка", "📣 Рассылка всем", "💎 Рассылка PRO", "🆓 Рассылка FREE", "🎯 Рассылка по сегменту",
    "➕ Выдать бонусы", "🚫 Забрать PRO", "🔄 Сбросить лимиты", "📊 Проверить подписку", "⛔ Заблокировать", "📜 История пользователя", "🔎 Найти пользователя", "👥 Список пользователей", "⚙️ Лимиты FREE", "⚙️ Лимиты PRO", "🕒 Запланированные", "📜 История рассылок", "🗑 Удалить из очереди", "✅ Отметить готово", "✏️ Редактировать материал", "🔄 Обновить очередь",
}

ALL_NAV_BUTTONS = MAIN_BUTTONS | CREATE_BUTTONS | CONTENT_BUTTONS | PROFILE_BUTTONS | ADMIN_BUTTONS | PRIME_BUTTONS


class GlobalNavigationMiddleware(BaseMiddleware):
    """Lets menu buttons switch modes even while an FSM state is active."""

    async def __call__(self, handler: Callable[[Message, dict[str, Any]], Awaitable[Any]], event: Message, data: dict[str, Any]) -> Any:
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)

        state: FSMContext | None = data.get("state")
        if state is None:
            return await handler(event, data)

        current_state = await state.get_state()
        text = event.text.strip()

        if current_state is None or text not in ALL_NAV_BUTTONS:
            return await handler(event, data)

        if await self._handle_button(event, state, text):
            return None

        return await handler(event, data)

    async def _handle_button(self, message: Message, state: FSMContext, text: str) -> bool:
        await state.clear()
        uid = message.from_user.id if message.from_user else None
        owner = is_owner(uid)

        if text == "⬅️ Главное меню":
            await message.answer("Главное меню 👇", reply_markup=home_menu(uid))
            return True

        if text == "🧠 Обучить стилю":
            from handlers.content import ContentState
            await state.set_state(ContentState.waiting_style_sample)
            await message.answer(
                "🧠 Обучение стилю\n\n"
                "Отправь 1–10 примеров постов, которые нравятся. Можно текстом, ссылками или пересланными постами.\n\n"
                "Я сохраню стиль накопительно: новые примеры добавляются к старым, профиль становится точнее.",
                reply_markup=style_menu,
            )
            return True

        if text == "✍️ Опиши стиль":
            from handlers.content import ContentState, style_description_prompt
            await state.set_state(ContentState.waiting_style_description)
            await message.answer(style_description_prompt(), reply_markup=style_menu)
            return True

        if text == "🎭 Мой стиль":
            from database.db import get_user_style
            style = await get_user_style(message.from_user.id)
            await message.answer(
                ("🎭 Твой сохранённый стиль:\n\n" + style[:2500]) if style else "🎭 Стиль пока не обучен. Нажми «🧠 Обучить стилю» и отправь примеры.",
                reply_markup=style_menu,
            )
            return True

        if text in {"♻️ Сбросить стиль", "❌ Сбросить стиль"}:
            from database.db import reset_user_style
            await reset_user_style(message.from_user.id)
            await message.answer("✅ Стиль сброшен. Можно обучить заново.", reply_markup=style_menu)
            return True

        if text in {"🚀 Создать", "🚀 Создать контент", "📦 Создать", "⬅️ Назад в создание"}:
            await message.answer("🚀 <b>Создать контент</b>\n\nВыбери формат:", reply_markup=create_menu, parse_mode="HTML")
            return True

        if text in {"🛠 Инструменты", "🛠 AI-инструменты", "📚 Контент"}:
            await message.answer("🛠 <b>AI-инструменты</b>\n\nВыбери инструмент:", reply_markup=content_menu, parse_mode="HTML")
            return True

        if text in {"📲 Публикации", "📅 План и публикации", "⬅️ Назад в публикации"}:
            await message.answer("📅 <b>План и публикации</b>\n\nОчередь, отложенная публикация и IG→TG связки.", reply_markup=publish_plan_menu, parse_mode="HTML")
            return True

        if text in {"💎 PRO", "💎 Подписка"}:
            await message.answer("💎 <b>PRO / подписка</b>\n\nВыбери тариф или посмотри текущую подписку:", reply_markup=subscription_menu, parse_mode="HTML")
            return True

        if text in {"🧠 AI Профиль", "⬅️ Назад в профиль"}:
            from handlers.content import ai_profile_text
            await message.answer(ai_profile_text(), reply_markup=profile_menu)
            return True

        if text in {"🎭 Стиль", "🎭 Стиль текста"}:
            await message.answer("🎭 Стиль автора\n\nВыбери действие:\n\n✍️ Опиши стиль — вручную задать тон.\n🧠 Обучить стилю — прислать примеры постов.\n🎭 Мой стиль — посмотреть, что сохранено.", reply_markup=style_menu)
            return True


        # Админские подменю: при активном FSM не выбрасываем в главное меню, а переключаемся внутри текущего блока.
        if text in {"📣 Рассылка всем", "💎 Рассылка PRO", "🆓 Рассылка FREE", "🎯 Рассылка по сегменту", "📬 Новая рассылка"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.admin_prime import AdminPrimeN8NState
            segment = {"📣 Рассылка всем":"all", "💎 Рассылка PRO":"pro", "🆓 Рассылка FREE":"free", "🎯 Рассылка по сегменту":"segment", "📬 Новая рассылка":"all"}[text]
            await state.update_data(broadcast_segment=segment)
            await state.set_state(AdminPrimeN8NState.waiting_broadcast_text)
            await message.answer(f"📬 Рассылка: {text}\n\nНапиши текст рассылки. Я покажу предпросмотр и оставлю тебя в разделе рассылок.", reply_markup=prime_broadcast_menu)
            return True

        if text in {"🕒 Запланированные", "📜 История рассылок", "❌ Отмена рассылки"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            if text == "🕒 Запланированные":
                await message.answer("🕒 Запланированные рассылки пока пустые. Здесь будут будущие рассылки и расписание.", reply_markup=prime_broadcast_menu)
            elif text == "📜 История рассылок":
                await message.answer("📜 История рассылок пока пустая. После первой рассылки здесь появится дата, сегмент, текст и статус.", reply_markup=prime_broadcast_menu)
            else:
                await message.answer("❌ Рассылка отменена.", reply_markup=prime_broadcast_menu)
            return True

        if text in {"👥 Список пользователей", "🔎 Найти пользователя", "📜 История пользователя", "➕ Выдать бонусы", "🔄 Сбросить лимиты", "⛔ Заблокировать", "🚫 Забрать PRO", "💎 Выдать PRO"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.admin_prime import AdminPrimeN8NState
            if text == "🔎 Найти пользователя":
                await state.set_state(AdminPrimeN8NState.waiting_find_user); await message.answer("🔎 Отправь user_id или username пользователя.", reply_markup=prime_users_menu); return True
            if text == "📜 История пользователя":
                await state.set_state(AdminPrimeN8NState.waiting_user_history); await message.answer("📜 Отправь user_id пользователя для истории.", reply_markup=prime_users_menu); return True
            if text == "➕ Выдать бонусы":
                await state.set_state(AdminPrimeN8NState.waiting_bonus_user); await message.answer("➕ Отправь user_id и количество бонусов.\n\nПример: 916037494 10", reply_markup=prime_users_menu); return True
            if text == "🔄 Сбросить лимиты":
                await state.set_state(AdminPrimeN8NState.waiting_reset_limits_user); await message.answer("🔄 Отправь user_id пользователя для сброса лимитов.", reply_markup=prime_users_menu); return True
            if text == "⛔ Заблокировать":
                await state.set_state(AdminPrimeN8NState.waiting_block_user); await message.answer("⛔ Отправь user_id пользователя для блокировки.", reply_markup=prime_users_menu); return True
            if text == "🚫 Забрать PRO":
                await state.set_state(AdminPrimeN8NState.waiting_remove_pro_user); await message.answer("🚫 Отправь user_id пользователя, у которого нужно забрать PRO.", reply_markup=prime_users_menu); return True
            if text == "💎 Выдать PRO":
                from handlers.admin import AdminState
                await state.set_state(AdminState.waiting_pro_user_id); await message.answer("💎 Выдать PRO\n\nОтправь user_id пользователя.", reply_markup=prime_users_menu); return True
            # список пользователей передаём обычному обработчику, чтобы он прочитал БД
            await message.answer("👥 Открой раздел пользователей и нажми кнопку ещё раз — список будет показан из базы.", reply_markup=prime_users_menu)
            return True

        if text in {"🕒 Посмотреть очередь", "📌 Очередь публикаций", "📤 Подготовить к публикации", "📅 Публикация позже", "✅ Отметить готово", "🗑 Удалить из очереди", "✏️ Редактировать материал", "🔄 Обновить очередь"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.admin_prime import AdminPrimeN8NState
            if text == "🗑 Удалить из очереди":
                await state.set_state(AdminPrimeN8NState.waiting_delete_queue_id); await message.answer("🗑 Отправь ID материала из очереди для удаления.", reply_markup=prime_publish_hub_menu); return True
            if text == "📅 Публикация позже":
                await state.set_state(AdminPrimeN8NState.waiting_schedule_queue); await message.answer("📅 Отправь: ID и время.\n\nПример: 3 завтра 18:00", reply_markup=prime_publish_hub_menu); return True
            await message.answer("📦 Раздел очереди. Выбери действие внутри очереди — создание контента здесь не запускается.", reply_markup=prime_publish_hub_menu)
            return True

        if text == "👑 Админ" or text == "⬅️ Назад в админку":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            await message.answer("👑 Админ-панель\n\nВыбери действие:", reply_markup=admin_menu)
            return True

        if text in {"🚀 PRIME PANEL", "👑 PRIME PANEL", "⬅️ Назад в PRIME PANEL", "⬅️ Назад в админку", "❌ Отмена"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.admin_prime import PRIME_PANEL_TEXT
            await message.answer(PRIME_PANEL_TEXT, reply_markup=prime_panel_menu, parse_mode="HTML")
            return True

        if text in {"🧭 Карта системы", "🎯 Воронки IG→TG", "🔗 Воронки IG→TG", "📣 Контент Центр", "📢 Telegram", "📲 Instagram", "📬 Рассылки", "👥 Пользователи", "💎 Подписки и лимиты", "📈 Статистика", "📦 Очередь", "🤖 AI Лаборатория", "🧪 Проверки", "🧪 Проверка системы", "⚙️ Система"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.admin_prime import HUBS
            hub_key = "🎯 Воронки IG→TG" if text == "🔗 Воронки IG→TG" else ("🧪 Проверка системы" if text in {"🧪 Проверки", "⚙️ Система"} else text)
            hub_text, hub_keyboard = HUBS[hub_key]
            if text in {"🎯 Воронки IG→TG", "🔗 Воронки IG→TG"}:
                from handlers.ig_tg_funnel import IgTgFunnelState
                await state.set_state(IgTgFunnelState.waiting_type)
            await message.answer(hub_text, reply_markup=hub_keyboard, parse_mode="HTML")
            return True

        if text == "⚙️ Лимиты":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from database.db import get_all_limits
            from keyboards import limits_menu
            limits = await get_all_limits()
            await message.answer(
                "⚙️ Лимиты FREE в день\n\n"
                f"✍️ Посты: {limits['content_factory']}\n"
                f"🧠 Rewrite: {limits['rewrite']}\n"
                f"🎭 Brand Voice: {limits['brand_rewrite']}\n"
                f"🖼 Картинки: {limits['post_image']}\n"
                f"🚀 Контент-пак: {limits['content_pack']}\n\n"
                "Выбери лимит:",
                reply_markup=limits_menu,
            )
            return True

        if text == "💎 Выдать PRO":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.admin import AdminState
            await state.set_state(AdminState.waiting_pro_user_id)
            await message.answer("💎 Выдать PRO\n\nОтправь user_id пользователя.")
            return True

        if text == "📊 Статистика":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from database.db import get_stats
            data = await get_stats()
            await message.answer(
                "📊 Статистика\n\n"
                f"👥 Пользователей: {data['total_users']}\n"
                f"💎 PRO: {data['total_pro']}\n"
                f"⚡ Генераций: {data['total_generations']}",
                reply_markup=admin_menu,
            )
            return True

        if text == "📢 Рассылка":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.admin import AdminState
            await state.set_state(AdminState.waiting_broadcast_text)
            await message.answer("📢 Рассылка\n\nОтправь текст рассылки.")
            return True

        if text == "🔗 IG→TG Воронка":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.ig_tg_funnel import IgTgFunnelState, IG_TG_INTRO_TEXT
            await state.set_state(IgTgFunnelState.waiting_type)
            await message.answer(IG_TG_INTRO_TEXT, reply_markup=ig_tg_funnel_menu, parse_mode="HTML")
            return True

        if text in {"🎬 Reels → Telegram", "🎠 Карусель → Telegram", "🎁 Лид-магнит → Telegram"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.ig_tg_funnel import IgTgFunnelState, FUNNEL_TYPES, TOPIC_HELP_TEXT
            await state.update_data(funnel_type=FUNNEL_TYPES[text], funnel_title=text)
            await state.set_state(IgTgFunnelState.waiting_topic)
            await message.answer(TOPIC_HELP_TEXT, reply_markup=ig_tg_funnel_menu)
            return True

        if text in {"🎬 Viral Reels", "🎠 Viral Carousels", "🎯 Hook Generator", "🎁 Lead Magnet Lab"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_viral import PrimeViralState, TOOL_SETTINGS
            tool = TOOL_SETTINGS.get(text)
            if tool:
                await state.update_data(tool_key=tool["key"], tool_title=tool["title"])
                await state.set_state(PrimeViralState.waiting_topic)
                await message.answer(tool["intro"], reply_markup=prime_topic_menu, parse_mode="HTML")
                return True

        if text in {"🔁 Улучшить", "🔥 Усилить хук", "🧲 Усилить CTA", "🔗 TG-продолжение", "📤 Подготовить к публикации"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_viral import prime_improve_generated
            await prime_improve_generated(message)
            return True

        if text == "📌 Сохранить в очередь":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_viral import prime_save_to_queue
            await prime_save_to_queue(message)
            return True

        if text in {"🕒 Посмотреть очередь", "📌 Контент-очередь"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_viral import prime_show_queue
            await prime_show_queue(message)
            return True

        if text == "🚀 Отправить в n8n":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_autopost import send_last_prime_to_n8n
            await send_last_prime_to_n8n(message)
            return True

        if text == "📤 Подготовить Reels к IG":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_autopost import prepare_reels_to_ig
            await prepare_reels_to_ig(message)
            return True

        if text in {"📲 Instagram пакет", "📣 Telegram пакет", "📲 Отправить в Instagram", "📣 Отправить в Telegram", "🚀 Запустить автопостинг", "🧪 Проверить IG Pipeline"}:
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_autopost import route_publish_action
            await route_publish_action(message)
            return True

        if text == "📅 Публикация позже":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_autopost import schedule_publication_start
            await schedule_publication_start(message, state)
            return True

        if text == "📌 Очередь публикаций":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_autopost import publication_queue
            await publication_queue(message)
            return True

        if text == "🧪 Проверить n8n":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_autopost import check_n8n_webhook
            await check_n8n_webhook(message)
            return True

        if text == "📲 Подключение Instagram":
            if not owner:
                await message.answer("❌ Нет доступа")
                return True
            from handlers.prime_autopost import instagram_setup_info
            await instagram_setup_info(message)
            return True

        if text in {"✍️ Пост", "🖼 Пост с картинкой", "🖼 Пост + картинка", "🎠 Карусель", "🎬 Reels", "🚀 Контент-пак", "💡 Идеи", "💡 Идеи контента", "📅 Контент-план", "✍️ Rewrite", "🎭 Brand Voice", "🎯 Viral Hooks"}:
            from handlers.primeonix_v2_clean import V2State, ACTION_MAP, ACTION_TITLES
            action = ACTION_MAP.get(text)
            if action:
                await state.update_data(action=action)
                await state.set_state(V2State.waiting_content_prompt)
                await message.answer(
                    f"{ACTION_TITLES[action]}\n\n"
                    "Напиши тему или промпт 👇\n\n"
                    "Цель контента и визуальный стиль берутся из AI Профиля."
                )
                return True

        if text in {"🎁 Лид-магнит", "🚀 AI CTA", "📅 Серия постов", "🔎 Анализ поста", "🎯 Воронка продаж"}:
            if text == "🎁 Лид-магнит":
                from handlers.lead_magnet import LeadMagnetState
                await state.set_state(LeadMagnetState.waiting_topic)
                await message.answer("🎁 Лид-магнит\n\nНапиши нишу, продукт или тему.")
                return True
            if text == "🚀 AI CTA":
                from handlers.cta import CTAState
                await state.set_state(CTAState.waiting_topic)
                await message.answer("🚀 AI CTA\n\nНапиши тему, продукт или оффер.")
                return True
            if text == "📅 Серия постов":
                from handlers.series import SeriesState
                await state.set_state(SeriesState.waiting_topic)
                await message.answer("📅 Серия постов\n\nНапиши тему, продукт или нишу.")
                return True
            if text == "🔎 Анализ поста":
                from handlers.analyze import AnalyzeState
                await state.set_state(AnalyzeState.waiting_post)
                await message.answer("🔎 Анализ поста\n\nОтправь текст поста для разбора.")
                return True
            if text == "🎯 Viral Hooks":
                from handlers.hooks import HooksState
                await state.set_state(HooksState.waiting_topic)
                await message.answer("🎯 Viral Hooks\n\nНапиши тему или нишу.")
                return True
            if text == "🎯 Воронка продаж":
                from handlers.funnel import FunnelState
                await state.set_state(FunnelState.waiting_topic)
                await message.answer("🎯 Воронка продаж\n\nНапиши продукт, нишу или тему.")
                return True

        await message.answer("Ок, режим переключён. Выбери нужный раздел 👇", reply_markup=home_menu(uid))
        return True
