import os
from uuid import uuid4
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database.db import add_scheduled_post, get_admin_analytics

from config import settings
from database.db import (
    get_stats,
    get_all_limits,
    set_setting,
    activate_pro,
    get_all_user_ids,
    add_scheduled_post,
    get_scheduled_posts,
    get_scheduled_post_by_id,
    delete_scheduled_post,
    publish_scheduled_post_now,
    mark_post_published
)
from keyboards import admin_menu, limits_menu, autopost_menu, week_confirm_menu, post_action_buttons
from services.ai import ask_ai
from services.image_service import generate_quality_image
from services.week_service import generate_week_content, parse_week_posts, parse_times
from services.cleanup import cleanup_generated_posts


router = Router()


ADMIN_MENU_BUTTONS = [
    "👑 Админ",
    "📣 Автопостинг",
    "🤖 Сгенерировать пост",
    "✍️ Добавить свой пост",
    "📅 AI-неделя",
    "🕒 Очередь постов",
    "👁 Посмотреть пост",
    "📤 Опубликовать из очереди",
    "🗑 Удалить пост",
    "🧹 Очистить файлы",
    "💎 Выдать PRO",
    "⚙️ Лимиты",
    "📊 Статистика",
    "📢 Рассылка",
    "📊 Аналитика",
    "🚀 PRIME PANEL",
    "🔗 IG→TG Воронка",
    "🎬 Viral Reels",
    "🎠 Viral Carousels",
    "🎯 Hook Generator",
    "🎁 Lead Magnet Lab",
    "📌 Контент-очередь",
    "📤 AutoPost Center",
    "🤖 AI Agents",
    "📈 Analytics",
    "⬅️ Назад в PRIME PANEL",
    "⬅️ Назад в админку",

    # PrimeOnix V2 unified admin buttons
    "📣 Контент Центр", "🎯 Воронки IG→TG", "📬 Рассылки", "👥 Пользователи",
    "💎 Подписки и лимиты", "📈 Статистика", "📦 Очередь", "🧪 Проверка системы", "🧭 Карта системы",
    "📢 Telegram пост", "🖼 TG пост + картинка", "📚 Серия постов", "🎁 Лид-магниты TG", "🚀 Прогрев TG", "🚀 Автопостинг TG", "📊 Статистика Telegram",
    "📷 Instagram пост", "🎠 Instagram карусель", "🎬 Instagram Reels", "📅 Контент-план", "🚀 Автопостинг IG", "📊 Статистика Instagram",
    "🎬 Reels → Telegram", "🎠 Карусель → Telegram", "📷 Пост → Telegram", "🎁 Лид-магнит → Telegram", "📨 DM Funnel", "🧭 Все funnel_id",
    "📬 Новая рассылка", "📣 Рассылка всем", "💎 Рассылка PRO", "🆓 Рассылка FREE", "🎯 Рассылка по сегменту", "🕒 Запланированные", "📜 История рассылок",
    "👥 Список пользователей", "🔎 Найти пользователя", "🚫 Забрать PRO", "➕ Выдать бонусы", "🔄 Сбросить лимиты", "⛔ Заблокировать", "📜 История пользователя",
    "⚙️ Лимиты FREE", "⚙️ Лимиты PRO", "📊 Проверить подписку",
    "👥 Статистика пользователей", "⚡ Статистика генераций", "💎 Статистика подписок", "📈 Статистика лимитов", "🎯 Статистика воронок", "📲 Статистика Instagram", "📢 Статистика Telegram", "🚨 Ошибки n8n",
    "🧪 Проверить Image Generator", "🧪 Проверить Video Generator",
    "📜 Логи", "🔗 Webhooks n8n", "🧪 Проверить OpenRouter", "🧪 Проверить Telegram Bot",
    "⬅️ Главное меню",
]


async def cancel_admin_state_if_button(message: Message, state: FSMContext):
    if message.text not in ADMIN_MENU_BUTTONS:
        return False

    await state.clear()

    # PrimeOnix V2: если админ нажал кнопку меню во время ввода — переключаем раздел, а не отправляем текст как рассылку.
    if message.text in {"📣 Контент Центр", "🎯 Воронки IG→TG", "📬 Рассылки", "👥 Пользователи", "💎 Подписки и лимиты", "📈 Статистика", "📦 Очередь", "🧪 Проверка системы", "🧭 Карта системы"}:
        from handlers.admin_prime import HUBS
        text, keyboard = HUBS[message.text]
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        return True

    if message.text in {"📬 Новая рассылка", "📣 Рассылка всем", "💎 Рассылка PRO", "🆓 Рассылка FREE", "🎯 Рассылка по сегменту"}:
        await state.set_state(AdminState.waiting_broadcast_text)
        await state.update_data(broadcast_segment=message.text)
        await message.answer(
            f"📬 <b>{message.text}</b>\n\n"
            "Отправь текст рассылки. Кнопки меню теперь будут переключать разделы, а не отправляться как текст.",
            parse_mode="HTML"
        )
        return True

    if message.text == "🚀 PRIME PANEL":
        from keyboards import prime_panel_menu
        await message.answer("🚀 PRIME PANEL", reply_markup=prime_panel_menu)
        return True

    if message.text == "📣 Автопостинг":
        await message.answer("📣 Автопостинг", reply_markup=autopost_menu)
        return True

    if message.text == "🤖 Сгенерировать пост":
        await state.set_state(AdminState.waiting_autopost_topic)
        await message.answer("🤖 Напиши тему поста для канала.")
        return True

    if message.text == "✍️ Добавить свой пост":
        await state.set_state(AdminState.waiting_custom_post)
        await message.answer("✍️ Отправь текст поста.")
        return True

    if message.text == "📅 AI-неделя":
        await state.set_state(AdminState.waiting_week_topic)
        await message.answer("📅 Напиши тему для AI-недели.")
        return True

    if message.text == "👁 Посмотреть пост":
        await state.set_state(AdminState.waiting_view_post_id)
        await message.answer("👁 Отправь ID поста.")
        return True

    if message.text == "🗑 Удалить пост":
        await state.set_state(AdminState.waiting_delete_post_id)
        await message.answer("🗑 Отправь ID поста.")
        return True

    if message.text == "📤 Опубликовать из очереди":
        await state.set_state(AdminState.waiting_publish_post_id)
        await message.answer("📤 Отправь ID поста.")
        return True

    if message.text == "💎 Выдать PRO":
        await state.set_state(AdminState.waiting_pro_user_id)
        await message.answer("💎 Выдать PRO\n\nОтправь user_id пользователя.")
        return True

    if message.text == "⚙️ Лимиты":
        limits = await get_all_limits()
        await message.answer(
            "⚙️ Лимиты FREE в день\n\n"
            f"✍️ Посты: {limits['content_factory']}\n"
            f"🧠 Rewrite: {limits['rewrite']}\n"
            f"🎭 Brand Voice: {limits['brand_rewrite']}\n"
            f"🖼 Картинки: {limits['post_image']}\n"
            f"🚀 Контент-пак: {limits['content_pack']}\n\n"
            "Выбери лимит:",
            reply_markup=limits_menu
        )
        return True

    if message.text == "📊 Статистика":
        data = await get_stats()
        await message.answer(
            "📊 Статистика\n\n"
            f"👥 Пользователей: {data['total_users']}\n"
            f"💎 PRO: {data['total_pro']}\n"
            f"⚡ Генераций: {data['total_generations']}",
            reply_markup=admin_menu
        )
        return True

    if message.text == "📊 Аналитика":
        data = await get_admin_analytics()
        usage_text = ""
        for feature, count in data["usage"]:
            usage_text += f"• {feature}: {count}\n"
        if not usage_text:
            usage_text = "Пока нет данных."
        await message.answer(
            "📊 Аналитика бота\n\n"
            f"👥 Пользователей: {data['total_users']}\n"
            f"💎 Платных пользователей: {data['paid_users']}\n"
            f"🕒 Постов в очереди: {data['pending_posts']}\n\n"
            "🔥 Использование функций:\n"
            f"{usage_text}",
            reply_markup=admin_menu
        )
        return True

    if message.text == "📢 Рассылка":
        await state.set_state(AdminState.waiting_broadcast_text)
        await message.answer("📢 Рассылка\n\nОтправь текст рассылки.")
        return True

    if message.text == "⬅️ Назад в админку":
        await message.answer("👑 Админ-панель", reply_markup=admin_menu)
        return True

    if message.text == "⬅️ Главное меню":
        from keyboards import main_menu
        await message.answer("Главное меню 👇", reply_markup=main_menu)
        return True

    await message.answer("Ок, переключаю действие.", reply_markup=autopost_menu)
    return True


class AdminState(StatesGroup):
    waiting_pro_user_id = State()
    waiting_pro_days = State()
    waiting_limit_value = State()
    waiting_broadcast_text = State()

    waiting_autopost_topic = State()
    waiting_custom_post = State()
    waiting_schedule_time = State()

    waiting_view_post_id = State()
    waiting_delete_post_id = State()
    waiting_publish_post_id = State()
    waiting_week_topic = State()
    waiting_week_times = State()
    waiting_week_confirm = State()


def is_admin(user_id: int) -> bool:
    return settings.ADMIN_ID is not None and user_id == settings.ADMIN_ID


def parse_publish_time(text: str):
    text = text.lower().strip()
    now = datetime.utcnow()

    if text == "сейчас":
        return now

    if text.startswith("через") and "мин" in text:
        digits = "".join(ch for ch in text if ch.isdigit())
        minutes = int(digits) if digits else 10
        return now + timedelta(minutes=minutes)

    if ":" in text:
        hour, minute = text.split(":", 1)

        if hour.isdigit() and minute.isdigit():
            publish_time = datetime.utcnow().replace(
                hour=int(hour),
                minute=int(minute),
                second=0,
                microsecond=0
            )

            if publish_time < now:
                publish_time += timedelta(days=1)

            return publish_time

    return None


async def save_image_file(image_bytes):
    os.makedirs("generated_posts", exist_ok=True)

    path = f"generated_posts/{uuid4().hex}.jpg"

    with open(path, "wb") as file:
        file.write(image_bytes.getvalue())

    return path


def normalize_post_text(text):
    if text is None:
        return ""

    text = str(text).strip()
    return text


async def publish_post_to_channel(bot, text, image_path=None):
    text = normalize_post_text(text)

    if not text:
        raise ValueError("Пост пустой. Нечего публиковать.")

    if not settings.CHANNEL_ID:
        raise ValueError("CHANNEL_ID не указан в .env")

    if image_path and os.path.exists(image_path):
        await bot.send_photo(
            chat_id=settings.CHANNEL_ID,
            photo=FSInputFile(image_path),
            caption=text[:1024],
            reply_markup=post_action_buttons()
        )

        if len(text) > 1024:
            await bot.send_message(
                chat_id=settings.CHANNEL_ID,
                text=text,
                reply_markup=post_action_buttons()
            )
    else:
        await bot.send_message(
            chat_id=settings.CHANNEL_ID,
            text=text,
            reply_markup=post_action_buttons()
        )


@router.message(F.text == "👑 Админ")
async def admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.clear()
    await message.answer("👑 Админ-панель\n\nВыбери действие:", reply_markup=admin_menu)


@router.message(F.text == "⬅️ Назад в админку")
async def back_to_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer("👑 Админ-панель", reply_markup=admin_menu)


@router.message(F.text == "📣 Автопостинг")
async def autopost_menu_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer(
        "📣 Автопостинг\n\n"
        "Можно сгенерировать пост с картинкой, добавить свой пост, "
        "запланировать время, посмотреть очередь, удалить или опубликовать сразу.",
        reply_markup=autopost_menu
    )


@router.message(F.text == "🤖 Сгенерировать пост")
async def generate_channel_post_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AdminState.waiting_autopost_topic)

    await message.answer("🤖 Напиши тему поста для канала.")


@router.message(AdminState.waiting_autopost_topic)
async def generate_channel_post(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    topic = message.text.strip()

    await message.answer("🧠 Генерирую текст и картинку...")

    post = await ask_ai(f"""
Напиши красивый Telegram-пост для канала на тему:
{topic}

Стиль:
живой, уверенный, современный, с эмодзи.

Формат:
сильный хук
3-5 коротких абзацев
понятная мысль
CTA в конце

Без markdown.
Без звёздочек.
Без таблиц.
""")

    post = normalize_post_text(post)

    if not post:
        await state.clear()
        await message.answer(
            "❌ AI не вернул текст поста. Попробуй другую тему.",
            reply_markup=autopost_menu
        )
        return

    image_bytes = await generate_quality_image(
        topic,
        is_pro=True,
        visual_style="business"
    )

    image_path = await save_image_file(image_bytes)

    await state.update_data(
        post_text=post,
        image_path=image_path
    )

    await state.set_state(AdminState.waiting_schedule_time)

    await message.answer_photo(
        photo=FSInputFile(image_path),
        caption=post[:1024]
    )

    if len(post) > 1024:
        await message.answer(post)

    await message.answer(
        "Теперь отправь время публикации:\n\n"
        "сейчас\n"
        "через 10 минут\n"
        "18:30"
    )


@router.message(F.text == "🧹 Очистить файлы")
async def cleanup_files(message: Message):
    if not is_admin(message.from_user.id):
        return

    deleted = cleanup_generated_posts(days=7)

    await message.answer(
        "🧹 Очистка завершена\n\n"
        f"Удалено файлов: {deleted}"
    )


@router.message(F.text == "📅 AI-неделя")
async def ai_week_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AdminState.waiting_week_topic)

    await message.answer(
        "📅 AI-неделя\n\n"
        "Напиши тему, и я создам 7 постов с картинками для автопостинга."
    )


@router.message(AdminState.waiting_week_topic)
async def ai_week_topic(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    await state.update_data(week_topic=message.text.strip())
    await state.set_state(AdminState.waiting_week_times)

    await message.answer(
        "🕒 Теперь отправь времена публикаций.\n\n"
        "Пример:\n"
        "10:00, 13:00, 18:00\n\n"
        "Если времен меньше 7, я буду повторять их по кругу."
    )


@router.message(AdminState.waiting_week_times)
async def ai_week_generate(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    times = parse_times(message.text)

    if not times:
        await message.answer(
            "❌ Не понял время.\n\n"
            "Пример:\n"
            "10:00, 13:00, 18:00"
        )
        return

    data = await state.get_data()
    topic = data["week_topic"]

    await message.answer("🧠 Генерирую неделю контента с картинками...")

    result = await generate_week_content(topic)
    posts = parse_week_posts(result)

    if not posts:
        await state.clear()

        await message.answer(
            "❌ Не удалось разобрать посты.\n\n"
            f"{result[:3500]}",
            reply_markup=autopost_menu
        )
        return

    await state.update_data(
        week_topic=topic,
        week_times=times,
        week_posts=posts
    )

    await state.set_state(AdminState.waiting_week_confirm)

    preview = "📅 AI-неделя готова\n\n"

    for item in posts[:7]:
        publish_time = times[(item["day"] - 1) % len(times)]

        preview += (
            f"День {item['day']} — {publish_time}\n"
            f"{item['text'][:180].replace(chr(10), ' ')}...\n\n"
        )

    await message.answer(
        preview[:3500] + "\nЧто сделать?",
        reply_markup=week_confirm_menu
    )



@router.message(AdminState.waiting_week_confirm)
async def ai_week_confirm(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    allowed_actions = [
        "✅ Добавить",
        "🔁 Перегенерировать",
        "❌ Отмена"
    ]

    if message.text in ADMIN_MENU_BUTTONS and message.text not in allowed_actions:
        await state.clear()

        await message.answer(
            "Ок, предыдущее действие отменено.",
            reply_markup=autopost_menu
        )
        return

    data = await state.get_data()

    topic = data.get("week_topic")
    times = data.get("week_times")
    posts = data.get("week_posts")

    if message.text == "❌ Отмена":
        await state.clear()

        await message.answer(
            "Отменено.",
            reply_markup=autopost_menu
        )
        return

    if message.text == "🔁 Перегенерировать":
        await state.clear()
        await state.update_data(week_topic=topic)
        await state.set_state(AdminState.waiting_week_times)

        await message.answer(
            "🔁 Хорошо, перегенерируем.\n\n"
            "Отправь времена публикаций ещё раз:\n"
            "10:00, 13:00, 18:00"
        )
        return

    if message.text != "✅ Добавить":
        await message.answer(
            "Выбери действие кнопкой 👇",
            reply_markup=week_confirm_menu
        )
        return

    os.makedirs("generated_posts", exist_ok=True)

    now = datetime.utcnow()
    added = 0

    for item in posts:
        publish_time_text = times[(item["day"] - 1) % len(times)]
        hour, minute = publish_time_text.split(":")

        publish_time = now + timedelta(days=item["day"] - 1)
        publish_time = publish_time.replace(
            hour=int(hour),
            minute=int(minute),
            second=0,
            microsecond=0
        )

        image_path = None

        try:
            image_bytes = await generate_quality_image(
                item.get("image_prompt", topic),
                is_pro=True,
                visual_style="business",
                user_plan="premium"
            )

            image_path = f"generated_posts/week_{uuid4().hex}.jpg"

            with open(image_path, "wb") as file:
                file.write(image_bytes.getvalue())

        except Exception as e:
            print(f"AI WEEK IMAGE ERROR: {e}")

        await add_scheduled_post(
            text=item["text"],
            publish_at=publish_time.isoformat(),
            image_path=image_path
        )

        added += 1

    await state.clear()

    await message.answer(
        "✅ AI-неделя добавлена в автопостинг\n\n"
        f"Постов запланировано: {added}\n"
        "Картинки добавлены.\n\n"
        "Проверь через: 🕒 Очередь постов",
        reply_markup=autopost_menu
    )    


@router.message(F.text == "✍️ Добавить свой пост")
async def custom_post_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AdminState.waiting_custom_post)

    await message.answer(
        "✍️ Добавить свой пост\n\n"
        "Отправь текст поста.\n\n"
        "После этого я спрошу время публикации."
    )


@router.message(AdminState.waiting_custom_post)
async def custom_post_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    post_text = message.text or message.caption
    image_path = None

    if not post_text or not post_text.strip():
        await message.answer(
            "❌ Пост пустой.\n\n"
            "Отправь текст поста или фото с подписью."
        )
        return

    if message.photo:
        os.makedirs("generated_posts", exist_ok=True)

        photo = message.photo[-1]
        image_path = f"generated_posts/custom_{uuid4().hex}.jpg"

        await message.bot.download(
            photo,
            destination=image_path
        )

    await state.update_data(
        post_text=post_text.strip(),
        image_path=image_path
    )

    await state.set_state(AdminState.waiting_schedule_time)

    await message.answer(
        "✅ Пост принят.\n\n"
        "Теперь отправь время публикации:\n\n"
        "сейчас\n"
        "через 10 минут\n"
        "18:30"
    )


@router.message(AdminState.waiting_schedule_time)
async def schedule_post(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    data = await state.get_data()

    post_text = normalize_post_text(data.get("post_text"))
    image_path = data.get("image_path")

    if not post_text:
        await state.clear()
        await message.answer(
            "❌ Пост не найден или пустой. Начни заново: «✍️ Добавить свой пост» или «🤖 Сгенерировать пост».",
            reply_markup=autopost_menu
        )
        return

    publish_time = parse_publish_time(message.text)

    if publish_time is None:
        await message.answer(
            "❌ Не понял время.\n\n"
            "Напиши:\n"
            "сейчас\n"
            "через 10 минут\n"
            "18:30"
        )
        return

    if message.text.lower().strip() == "сейчас":
        try:
            await publish_post_to_channel(
                bot=message.bot,
                text=post_text,
                image_path=image_path
            )

            await state.clear()

            await message.answer(
                "✅ Пост опубликован в канал",
                reply_markup=autopost_menu
            )

        except Exception as e:
            await message.answer(
                f"❌ Ошибка публикации:\n{e}",
                reply_markup=autopost_menu
            )

        return

    await add_scheduled_post(
        text=post_text,
        image_path=image_path,
        publish_at=publish_time.isoformat()
    )

    await state.clear()

    await message.answer(
        "✅ Пост запланирован\n\n"
        f"Время публикации: {publish_time.strftime('%H:%M %d.%m.%Y')}",
        reply_markup=autopost_menu
    )


@router.message(F.text == "🕒 Очередь постов")
async def scheduled_posts(message: Message):
    if not is_admin(message.from_user.id):
        return

    posts = await get_scheduled_posts()

    if not posts:
        await message.answer("🕒 Очередь постов пустая")
        return

    text = "🕒 Запланированные посты:\n\n"

    for post_id, post_text, image_path, publish_at, status in posts:
        safe_text = normalize_post_text(post_text)
        preview = safe_text[:100].replace("\n", " ") if safe_text else "[пустой пост]"
        has_image = "🖼 да" if image_path else "нет"
        text += f"ID: {post_id}\nВремя: {publish_at}\nКартинка: {has_image}\n{preview}...\n\n"

    await message.answer(text)


@router.message(F.text == "👁 Посмотреть пост")
async def view_post_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AdminState.waiting_view_post_id)

    await message.answer(
        "👁 Отправь ID поста из очереди.\n\n"
        "Если передумал — нажми любую кнопку меню."
    )


@router.message(AdminState.waiting_view_post_id)
async def view_post(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    if not message.text.isdigit():
        await message.answer("❌ ID должен быть числом.")
        return

    post = await get_scheduled_post_by_id(int(message.text))
    await state.clear()

    if not post:
        await message.answer("❌ Пост не найден", reply_markup=autopost_menu)
        return

    post_id, text, image_path, publish_at, status = post
    text = normalize_post_text(text)

    if not text:
        await message.answer("❌ Пост пустой или повреждён.", reply_markup=autopost_menu)
        return

    if image_path and os.path.exists(image_path):
        await message.answer_photo(
            photo=FSInputFile(image_path),
            caption=text[:1024],
            reply_markup=post_action_buttons()
        )

        if len(text) > 1024:
            await message.answer(text)
    else:
        await message.answer(text)

    await message.answer(
        f"👁 Пост #{post_id}\n\n"
        f"Статус: {status}\n"
        f"Время: {publish_at}",
        reply_markup=autopost_menu
    )


@router.message(F.text == "🗑 Удалить пост")
async def delete_post_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AdminState.waiting_delete_post_id)

    await message.answer(
        "🗑 Отправь ID поста, который нужно удалить.\n\n"
        "Если передумал — нажми любую кнопку меню."
    )


@router.message(AdminState.waiting_delete_post_id)
async def delete_post(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    if not message.text.isdigit():
        await message.answer("❌ ID должен быть числом.")
        return

    await delete_scheduled_post(int(message.text))
    await state.clear()

    await message.answer(
        "✅ Пост удалён из очереди",
        reply_markup=autopost_menu
    )


@router.message(F.text == "📤 Опубликовать из очереди")
async def publish_from_queue_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AdminState.waiting_publish_post_id)

    await message.answer(
        "📤 Отправь ID поста, который нужно опубликовать сейчас.\n\n"
        "Если передумал — нажми любую кнопку меню."
    )


@router.message(AdminState.waiting_publish_post_id)
async def publish_from_queue(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    if not message.text.isdigit():
        await message.answer("❌ ID должен быть числом.")
        return

    if not settings.CHANNEL_ID:
        await state.clear()
        await message.answer("❌ CHANNEL_ID не указан в .env", reply_markup=autopost_menu)
        return

    post = await publish_scheduled_post_now(int(message.text))
    await state.clear()

    if not post:
        await message.answer(
            "❌ Пост не найден или уже опубликован",
            reply_markup=autopost_menu
        )
        return

    post_id, text, image_path, publish_at = post
    text = normalize_post_text(text)

    try:
        await publish_post_to_channel(
            bot=message.bot,
            text=text,
            image_path=image_path
        )

        await mark_post_published(post_id)

        await message.answer(
            "✅ Пост опубликован сейчас",
            reply_markup=autopost_menu
        )

    except Exception as e:
        await message.answer(
            f"❌ Ошибка публикации:\n{e}",
            reply_markup=autopost_menu
        )


@router.message(F.text == "📊 Статистика")
async def stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    data = await get_stats()

    await message.answer(
        "📊 Статистика\n\n"
        f"👥 Пользователей: {data['total_users']}\n"
        f"💎 PRO: {data['total_pro']}\n"
        f"⚡ Генераций: {data['total_generations']}"
    )


@router.message(F.text == "📊 Аналитика")
async def admin_analytics(message: Message):
    if not is_admin(message.from_user.id):
        return

    data = await get_admin_analytics()

    usage_text = ""
    for feature, count in data["usage"]:
        usage_text += f"• {feature}: {count}\n"

    if not usage_text:
        usage_text = "Пока нет данных."

    await message.answer(
        "📊 Аналитика бота\n\n"
        f"👥 Пользователей: {data['total_users']}\n"
        f"💎 Платных пользователей: {data['paid_users']}\n"
        f"🕒 Постов в очереди: {data['pending_posts']}\n\n"
        "🔥 Использование функций:\n"
        f"{usage_text}",
        reply_markup=admin_menu
    )


@router.message(F.text == "💎 Выдать PRO")
async def give_pro_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AdminState.waiting_pro_user_id)
    await message.answer("💎 Выдать PRO\n\nОтправь user_id пользователя.")


@router.message(AdminState.waiting_pro_user_id)
async def give_pro_user_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    if not message.text.isdigit():
        await message.answer("❌ user_id должен быть числом.")
        return

    await state.update_data(pro_user_id=int(message.text))
    await state.set_state(AdminState.waiting_pro_days)
    await message.answer("Теперь отправь количество дней PRO.\n\nНапример: 30")


@router.message(AdminState.waiting_pro_days)
async def give_pro_days(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    if not message.text.isdigit():
        await message.answer("❌ Количество дней должно быть числом.")
        return

    data = await state.get_data()
    user_id = data["pro_user_id"]
    days = int(message.text)

    await activate_pro(user_id, days)
    await state.clear()

    await message.answer(
        "✅ PRO выдан\n\n"
        f"Пользователь: {user_id}\n"
        f"Срок: {days} дней",
        reply_markup=admin_menu
    )


@router.message(F.text == "⚙️ Лимиты")
async def limits_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    limits = await get_all_limits()

    await message.answer(
        "⚙️ Лимиты FREE в день\n\n"
        f"✍️ Посты: {limits['content_factory']}\n"
        f"🧠 Rewrite: {limits['rewrite']}\n"
        f"🎭 Brand Voice: {limits['brand_rewrite']}\n"
        f"🖼 Картинки: {limits['post_image']}\n"
        f"🚀 Контент-пак: {limits['content_pack']}\n\n"
        "Выбери лимит:",
        reply_markup=limits_menu
    )


@router.message(F.text.in_([
    "Лимит: посты",
    "Лимит: rewrite",
    "Лимит: brand voice",
    "Лимит: картинки",
    "Лимит: контент-пак"
]))
async def choose_limit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    mapping = {
        "Лимит: посты": "content_factory",
        "Лимит: rewrite": "rewrite",
        "Лимит: brand voice": "brand_rewrite",
        "Лимит: картинки": "post_image",
        "Лимит: контент-пак": "content_pack"
    }

    await state.clear()
    await state.update_data(limit_feature=mapping[message.text])
    await state.set_state(AdminState.waiting_limit_value)
    await message.answer("Отправь новый лимит числом.")


@router.message(AdminState.waiting_limit_value)
async def set_limit_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    if not message.text.isdigit():
        await message.answer("❌ Лимит должен быть числом.")
        return

    data = await state.get_data()
    feature = data["limit_feature"]
    value = int(message.text)

    await set_setting(f"limit_{feature}", value)
    await state.clear()

    await message.answer(
        "✅ Лимит обновлён\n\n"
        f"Функция: {feature}\n"
        f"Новый лимит: {value} в день",
        reply_markup=admin_menu
    )


@router.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AdminState.waiting_broadcast_text)
    await message.answer("📢 Рассылка\n\nОтправь текст рассылки.")


@router.message(AdminState.waiting_broadcast_text)
async def broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if await cancel_admin_state_if_button(message, state):
        return

    users = await get_all_user_ids()

    sent = 0
    failed = 0

    for user_id in users:
        try:
            await message.bot.send_message(chat_id=user_id, text=message.text)
            sent += 1
        except Exception:
            failed += 1

    await state.clear()

    await message.answer(
        "✅ Рассылка завершена\n\n"
        f"Отправлено: {sent}\n"
        f"Ошибок: {failed}",
        reply_markup=admin_menu
    )
