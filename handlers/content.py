from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database.db import save_user_memory, get_user_memory
from database.db import (
    can_use_feature,
    track_usage,
    register_user,
    get_user_plan,
    save_user_style,
    get_user_style,
    reset_user_style, save_style_sample, get_style_samples,
    save_user_profile_field,
    get_user_profile,
    reset_user_profile
)

from services.ai import ask_ai
from services.queue import add_to_queue
from services.image_service import generate_quality_image
from services.carousel_service import create_carousel_images
from services.ready_post_service import generate_ready_post
from services.brand_brain import build_brand_brain
from services.ready_carousel_service import generate_ready_carousel
from services.memory import build_memory_profile_block
from services.sender import send_long
from services.prompt_engine import (
    build_post_prompt,
    build_reels_prompt,
    build_carousel_prompt,
    build_ideas_prompt,
    build_plan_prompt
)

from keyboards import (
    create_menu,
    content_menu,
    profile_menu,
    style_menu,
    image_style_menu,
    carousel_style_menu,
    after_generation_menu,
    goal_menu
)


router = Router()


def ai_profile_text() -> str:
    return (
        "🧠 AI Профиль\n\n"
        "Настрой профиль один раз — и AI будет создавать контент точнее под тебя.\n\n"
        "Что заполнить:\n\n"
        "⚙️ Быстрая настройка\n"
        "Заполни основные данные одним коротким сообщением.\n\n"
        "🎭 Стиль автора\n"
        "Как должен писать AI: экспертно, живо, дерзко, premium, мягко или по-дружески.\n\n"
        "🏢 Ниша\n"
        "О чём твой контент. Например: AI, маркетинг, бьюти, фитнес, бизнес, обучение, недвижимость.\n\n"
        "🎯 Аудитория\n"
        "Для кого создаётся контент. Например: предприниматели, блогеры, эксперты, владельцы бизнеса.\n\n"
        "💎 Оффер\n"
        "Что ты продаёшь или предлагаешь людям.\n\n"
        "📢 CTA\n"
        "Как AI должен звать к действию: написать в ЛС, перейти в бот, подписаться, оставить заявку.\n\n"
        "📋 Мой профиль\n"
        "Показывает всё, что уже сохранено.\n\n"
        "👇 Выбери раздел ниже"
    )


def style_description_prompt() -> str:
    return (
        "✍️ Опиши стиль автора\n\n"
        "Напиши, как AI должен писать твои тексты.\n\n"
        "Можно так:\n"
        "«Пиши современно, уверенно и premium. Короткими абзацами, с сильным хуком, без воды. "
        "Тон экспертный, но простой. Эмодзи умеренно. Стиль: dark neon, AI, black-purple, luxury tech.»\n\n"
        "После этого AI будет использовать этот стиль в постах, Reels, каруселях и контент-паках."
    )



def is_priority_plan(plan: str) -> bool:
    return (plan or "free").lower() in [
        "start_premium",
        "plus",
        "vip",
        "premium",
        "pro",
    ]


USER_MENU_BUTTONS = [
    "📦 Создать",
    "📚 Контент",
    "🎬 Reels → Telegram",
    "🎠 Карусель → Telegram",
    "🎁 Лид-магнит → Telegram",
    "🧠 AI Профиль",
    "💎 Подписка",
    "📊 Кабинет",
    "⬅️ Главное меню",

    "✍️ Пост",
    "🖼 Пост с картинкой",
    "🖼 Пост + картинка",
    "🎠 Карусель",
    "🎬 Reels",
    "🚀 Контент-пак",

    "💡 Идеи контента",
    "💡 Идеи",
    "📅 Контент-план",
    "🔎 Анализ поста",
    "🎯 Viral Hooks",
    "🎯 Воронка продаж",
    "📅 Серия постов",
    "🚀 AI CTA",
    "🎁 Лид-магнит",
    "✍️ Rewrite",
    "🎭 Brand Voice",

    "🎭 Стиль",
    "🎭 Стиль текста",
    "🎨 Стиль визуала",
    "🎯 Цель контента",
    "✍️ Опиши стиль",
    "🎭 Мой стиль",
    "♻️ Сбросить стиль",
    "❌ Сбросить стиль",
    "⚙️ Быстрая настройка",
    "🏢 Ниша",
    "🎯 Аудитория",
    "💎 Оффер",
    "📍 Город",
    "📢 CTA",
    "📋 Мой профиль",
    "❌ Сбросить профиль",

    "⬅️ Назад в создание",
    "⬅️ Назад в профиль",
]


GOAL_BUTTONS = [
    "🔥 Продать",
    "🧠 Экспертность",
    "💬 Вовлечь",
    "🚀 Прогреть",
]


async def cancel_user_state_if_button(message: Message, state: FSMContext):
    if message.text not in USER_MENU_BUTTONS:
        return False

    await state.clear()

    if message.text == "📦 Создать":
        await message.answer("📦 Создание контента\n\nВыбери формат:", reply_markup=create_menu)
        return True

    if message.text == "📚 Контент":
        await message.answer("📚 Контент-инструменты\n\nВыбери инструмент:", reply_markup=content_menu)
        return True

    if message.text == "🧠 AI Профиль":
        await message.answer(
            ai_profile_text(),
            reply_markup=profile_menu
        )
        return True

    if message.text in {"🖼 Пост с картинкой", "🖼 Пост + картинка"}:
        await state.update_data(action="image_post")
        await state.set_state(ContentState.waiting_prompt)
        await message.answer(
            "🖼 <b>Пост + картинка</b>\n\n"
            "Напиши тему или промпт. Цель контента и визуальный стиль берутся из AI Профиля.",
            parse_mode="HTML",
        )
        return True

    if message.text == "🎠 Карусель":
        await state.update_data(action="carousel")
        await state.set_state(ContentState.waiting_prompt)
        await message.answer(
            "🎠 <b>Карусель</b>\n\n"
            "Напиши тему или промпт. Цель контента и визуальный стиль берутся из AI Профиля.",
            parse_mode="HTML",
        )
        return True


    if message.text == "🎨 Стиль визуала":
        await state.set_state(ContentState.waiting_image_style)
        await message.answer(
            "🎨 <b>Стиль визуала</b>\n\n"
            "Выбери общий визуальный стиль профиля. Он будет применяться к постам с картинкой, каруселям и обложкам Reels.",
            reply_markup=image_style_menu,
            parse_mode="HTML",
        )
        return True

    if message.text == "🎯 Цель контента":
        await message.answer(
            "🎯 <b>Цель контента</b>\n\n"
            "Эти цели больше не дублируются внутри каждого меню. Выбирай цель при создании материала: продажа, экспертность, вовлечение или прогрев.",
            reply_markup=goal_menu,
            parse_mode="HTML",
        )
        return True

    if message.text in {"🎭 Стиль", "🎭 Стиль текста"}:
        await message.answer(
            "🎭 Стиль автора\n\n"
            "Здесь можно быстро описать стиль или обучить AI на твоих постах.\n\n"
            "✍️ Опиши стиль — коротко объясни, как писать.\n"
            "🧠 Обучить стилю — отправь 3–10 своих постов.\n"
            "🎭 Мой стиль — посмотреть сохранённый стиль.\n"
            "♻️ Сбросить стиль — начать заново.",
            reply_markup=style_menu
        )
        return True

    if message.text == "✍️ Опиши стиль":
        await state.set_state(ContentState.waiting_style_description)
        await message.answer(style_description_prompt(), reply_markup=style_menu)
        return True

    if message.text == "🎭 Мой стиль":
        style = await get_user_style(message.from_user.id)

        if not style:
            await message.answer(
                "🎭 Мой стиль\n\n"
                "Стиль пока не настроен.\n\n"
                "Нажми «✍️ Опиши стиль» или «🧠 Обучить стилю».",
                reply_markup=style_menu
            )
            return True

        await message.answer(
            "🎭 Твой сохранённый стиль:\n\n"
            f"{style[:2500]}",
            reply_markup=style_menu
        )
        return True

    if message.text in ["♻️ Сбросить стиль", "❌ Сбросить стиль"]:
        await reset_user_style, save_style_sample, get_style_samples(message.from_user.id)
        await message.answer(
            "✅ Стиль сброшен.\n\n"
            "Теперь AI снова будет писать в стандартном стиле.",
            reply_markup=style_menu
        )
        return True

    action_map = {
        "✍️ Пост": "post",
        "🎬 Reels": "reels",
        "🚀 Контент-пак": "content_pack",
        "💡 Идеи контента": "ideas",
        "💡 Идеи": "ideas",
        "📅 Контент-план": "plan",
    }

    if message.text in action_map:
        await state.update_data(action=action_map[message.text])
        await state.set_state(ContentState.waiting_goal)
        await message.answer("🎯 Какая цель контента?", reply_markup=goal_menu)
        return True

    if message.text == "⬅️ Назад в создание":
        await message.answer("📦 Создание контента\n\nВыбери формат:", reply_markup=create_menu)
        return True

    if message.text == "⬅️ Главное меню":
        from keyboards import main_menu
        await message.answer("Главное меню 👇", reply_markup=main_menu)
        return True

    await message.answer("Ок, предыдущее действие отменено. Выбери нужный раздел.")
    return True


@router.message(F.text.in_({"📦 Создать", "🚀 Создать", "🚀 Создать контент"}))
async def open_create(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "📦 Создание контента\n\n"
        "Выбери, что нужно создать:\n\n"
        "✍️ Пост — готовый текст\n"
        "🖼 Пост с картинкой — текст + визуал\n"
        "🎠 Карусель — 5 слайдов\n"
        "🎬 Reels — сценарий короткого видео\n"
        "🚀 Контент-пак — сразу несколько форматов",
        reply_markup=create_menu
    )


@router.message(F.text.in_({"📚 Контент", "🛠 AI-инструменты", "🛠 Инструменты"}))
async def open_content(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "📚 Контент-инструменты\n\n"
        "Выбери инструмент:\n\n"
        "💡 Идеи — темы для контента\n"
        "📅 План — контент на месяц\n"
        "🔎 Анализ — разбор поста\n"
        "🎯 Воронка — прогрев к продаже\n"
        "📅 Серия — 7 постов\n"
        "🚀 CTA — призывы к действию",
        reply_markup=content_menu
    )


@router.message(F.text == "🧠 AI Профиль")
async def open_profile(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        ai_profile_text(),
        reply_markup=profile_menu
    )

@router.message(F.text == "⬅️ Назад в создание")
async def back_to_create(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "📦 Создание контента\n\n"
        "Выбери формат:",
        reply_markup=create_menu
    )


@router.message(F.text == "⬅️ Назад в профиль")
async def back_to_profile(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        ai_profile_text(),
        reply_markup=profile_menu
    )

class ContentState(StatesGroup):
    waiting_prompt = State()
    waiting_goal = State()
    waiting_style_sample = State()
    waiting_style_description = State()
    waiting_profile_value = State()
    waiting_image_style = State()
    waiting_carousel_style = State()


def menu_text():
    return (
        "📦 Контент\n\n"
        "Выбери, что создать:\n\n"
        "✍️ Пост\n"
        "🖼 Пост с картинкой\n"
        "🎠 Карусель\n"
        "🎬 Reels\n"
        "💡 Идеи\n"
        "📅 Контент-план\n\n"
        "🧠 Можно обучить бота твоему стилю."
    )


async def build_style_block(user_id: int):
    style = await get_user_style(user_id)

    if not style:
        return (
            "Стиль пользователя не задан. "
            "Пиши красиво, уверенно, современно, с эмодзи."
        )

    return f"""
Пиши в стиле пользователя.

Вот пример его стиля:
{style}

Сохраняй:
- ритм
- тон
- длину фраз
- эмоциональность
- подачу
- манеру писать

Но не копируй текст дословно.
"""


async def build_profile_block(user_id: int):
    profile = await get_user_profile(user_id)

    if not any(profile.values()):
        return "AI Профиль пользователя не заполнен."

    return f"""
AI Профиль пользователя:

Ниша:
{profile['niche'] or 'не указано'}

Аудитория:
{profile['audience'] or 'не указано'}

Оффер:
{profile['offer'] or 'не указано'}

Город:
{profile['city'] or 'не указано'}

CTA:
{profile['cta'] or 'не указано'}

Учитывай эти данные в тексте.
"""


@router.message(F.text == "📦 Контент")
async def content_menu_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        menu_text(),
        reply_markup=content_menu
    )


@router.message(F.text == "🎭 Стиль")
async def style_menu_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "🎭 Стиль автора\n\n"
        "Настрой, как AI должен писать твои тексты.\n\n"
        "✍️ Опиши стиль — быстрое описание словами.\n"
        "🧠 Обучить стилю — анализ 3–10 твоих постов.\n"
        "🎭 Мой стиль — посмотреть сохранённый стиль.\n"
        "♻️ Сбросить стиль — начать заново.\n\n"
        "Выбери действие:",
        reply_markup=style_menu
    )

@router.message(F.text == "🧠 AI Профиль")
async def ai_profile_menu(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        ai_profile_text(),
        reply_markup=profile_menu
    )

@router.message(F.text.in_([
    "🏢 Ниша",
    "🎯 Аудитория",
    "💎 Оффер",
    "📍 Город",
    "📢 CTA"
]))
async def profile_choose_field(message: Message, state: FSMContext):
    mapping = {
        "🏢 Ниша": "niche",
        "🎯 Аудитория": "audience",
        "💎 Оффер": "offer",
        "📍 Город": "city",
        "📢 CTA": "cta"
    }

    labels = {
        "niche": "нишу",
        "audience": "аудиторию",
        "offer": "оффер",
        "city": "город",
        "cta": "CTA"
    }

    field = mapping[message.text]

    await state.clear()
    await state.update_data(profile_field=field)
    await state.set_state(ContentState.waiting_profile_value)

    examples = {
        "niche": "AI-контент, нейросети, Telegram-боты и автоматизация для бизнеса",
        "audience": "предприниматели, блогеры, эксперты и владельцы Telegram-каналов",
        "offer": "помогаю создавать контент быстрее с помощью AI: посты, картинки, карусели и Reels",
        "city": "Москва / онлайн / вся Россия",
        "cta": "Напиши в бот и создай первый контент за пару минут"
    }

    await message.answer(
        f"Напиши {labels[field]}.\n\n"
        f"Пример:\n{examples[field]}"
    )


@router.message(ContentState.waiting_profile_value)
async def profile_save_field(message: Message, state: FSMContext):
    user_id = message.from_user.id
    value = message.text.strip()

    if value in [
        "⬅️ Назад в контент",
        "⬅️ Главное меню",
        "📦 Контент",
        "💎 Подписка",
        "👑 Админ"
    ]:
        await state.clear()
        await message.answer(
            "Настройка профиля отменена.",
            reply_markup=profile_menu
        )
        return

    if len(value) < 2:
        await message.answer("❌ Слишком коротко. Напиши подробнее.")
        return

    data = await state.get_data()
    field = data["profile_field"]

    await save_user_profile_field(user_id, field, value)
    await state.clear()

    await message.answer(
        "✅ Сохранено в AI Профиль\n\n"
        "Теперь бот будет учитывать это при генерации контента.",
        reply_markup=profile_menu
    )


@router.message(F.text == "📋 Мой профиль")
async def my_profile(message: Message):
    profile = await get_user_profile(message.from_user.id)

    await message.answer(
        "📋 Мой AI Профиль\n\n"
        f"🏢 Ниша: {profile['niche'] or 'не указано'}\n"
        f"🎯 Аудитория: {profile['audience'] or 'не указано'}\n"
        f"💎 Оффер: {profile['offer'] or 'не указано'}\n"
        f"📍 Город: {profile['city'] or 'не указано'}\n"
        f"📢 CTA: {profile['cta'] or 'не указано'}"
    )


@router.message(F.text.in_({"🗑 Сбросить профиль", "❌ Сбросить профиль"}))
async def reset_profile(message: Message, state: FSMContext):
    await state.clear()

    await reset_user_profile(message.from_user.id)

    await message.answer(
        "✅ AI Профиль сброшен.",
        reply_markup=profile_menu
    )


@router.message(F.text == "⬅️ Назад в контент")
async def back_to_content(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        menu_text(),
        reply_markup=content_menu
    )


@router.message(F.text == "✍️ Опиши стиль")
async def describe_style_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ContentState.waiting_style_description)

    await message.answer(
        style_description_prompt(),
        reply_markup=style_menu
    )


@router.message(ContentState.waiting_style_description)
async def save_style_description(message: Message, state: FSMContext):

    if await cancel_user_state_if_button(message, state):
        return

    user_id = message.from_user.id
    style_text = message.text.strip()

    if len(style_text) < 20:
        await message.answer(
            "❌ Слишком коротко.\n\n"
            "Опиши стиль чуть подробнее: тон, длина текста, эмоции, эмодзи, что нельзя делать."
        )
        return

    saved_style = f"""
Стиль автора описан вручную:

{style_text}

Правила:
- сохраняй этот тон во всех генерациях
- не копируй чужие тексты
- пиши понятно, структурно и без воды
"""

    await save_user_style(user_id, saved_style.strip())
    await state.clear()

    await message.answer(
        "✅ Стиль сохранён\n\n"
        "Теперь AI будет учитывать это при генерации контента.",
        reply_markup=style_menu
    )


@router.message(F.text == "🧠 Обучить стилю")
async def learn_style_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ContentState.waiting_style_sample)

    await message.answer(
        "🧠 Обучение стилю\n\n"
        "Отправь пример своего текста или поста.\n\n"
        "Можно вставить:\n"
        "— пост из Telegram\n"
        "— продающий текст\n"
        "— описание услуги\n"
        "— несколько своих сообщений\n\n"
        "Чтобы выйти — нажми «⬅️ Назад в профиль»."
    )


@router.message(ContentState.waiting_style_sample)
async def save_style_sample_handler(message: Message, state: FSMContext):
    if await cancel_user_state_if_button(message, state):
        return

    user_id = message.from_user.id
    sample = (message.text or "").strip()

    if len(sample) < 120:
        await message.answer(
            "❌ Слишком мало текста.\n\n"
            "Отправь хотя бы один нормальный пост или несколько абзацев. Лучше — 3–10 постов одним сообщением.",
            reply_markup=style_menu,
        )
        return

    await message.answer("🧠 Анализирую стиль и добавляю в AI-профиль...")

    previous = await get_style_samples(user_id, limit=5)
    previous_block = "\n\n".join([row[1] or row[0][:800] for row in previous]) if previous else ""

    prompt = f"""
Ты анализатор Brand Voice для PrimeOnix AI.
Нужно извлечь стиль автора из примеров и сделать практичный профиль для будущей генерации постов, каруселей и Reels.

Прошлые выводы по стилю, если есть:
{previous_block or 'нет'}

Новые примеры пользователя:
{sample}

Верни структурированный анализ на русском:
1. Тон и настроение
2. Длина и ритм фраз
3. Структура постов
4. Эмодзи и визуальные маркеры
5. Что обязательно повторять
6. Что запрещено
7. Формула поста автора
8. Формула карусели автора
9. Формула Reels автора

Не копируй тексты дословно. Это профиль стиля, а не новый пост.
"""
    try:
        brand_brain = await ask_ai(prompt)
    except Exception:
        brand_brain = (
            "Профиль стиля обновлён вручную по присланным примерам.\n"
            "Пиши структурно, живо, с короткими абзацами, сильными заголовками, без воды.\n\n"
            f"Примеры пользователя:\n{sample[:2500]}"
        )

    combined_style = f"""
Накопительный Brand Voice пользователя PrimeOnix.

Последний анализ:
{brand_brain}

Свежие примеры, на которых обучались:
{sample[:3000]}

Правила использования:
- используй стиль как ориентир, не копируй дословно;
- обычные посты/карусели/Reels делай без лид-магнитного CTA;
- CTA используй только если пользователь явно выбрал воронку/лид-магнит;
- сохраняй структуру, темп, подачу и визуальную манеру.
""".strip()

    await save_user_style(user_id, combined_style)
    await save_style_sample(user_id, sample, brand_brain)
    await state.clear()

    await message.answer(
        "✅ Стиль обновлён и сохранён\n\n"
        "Можно обучать ещё: снова нажми «🧠 Обучить стилю» и отправь новые посты. "
        "Профиль будет уточняться.",
        reply_markup=style_menu,
    )
    await message.answer(f"🧠 Краткий анализ:\n\n{brand_brain[:3000]}", reply_markup=style_menu)


@router.message(F.text == "🎭 Мой стиль")
async def my_style(message: Message):
    style = await get_user_style(message.from_user.id)

    if not style:
        await message.answer(
            "🎭 Мой стиль\n\n"
            "Стиль пока не обучен.\n\n"
            "Нажми «🧠 Обучить стилю» и отправь пример своего текста."
        )
        return

    await message.answer(
        "🎭 Твой сохранённый стиль:\n\n"
        f"{style[:1500]}"
    )


@router.message(F.text.in_(["♻️ Сбросить стиль", "❌ Сбросить стиль"]))
async def reset_style(message: Message, state: FSMContext):
    await state.clear()

    await reset_user_style, save_style_sample, get_style_samples(message.from_user.id)

    await message.answer(
        "✅ Стиль сброшен.\n\n"
        "Теперь бот снова будет писать в стандартном стиле.",
        reply_markup=style_menu
    )


@router.message(F.text.in_([
    "✍️ Пост",
    "🖼 Пост с картинкой",
    "🖼 Пост + картинка",
    "🎠 Карусель",
    "🎬 Reels",
    "🚀 Контент-пак",
    "💡 Идеи контента",
    "💡 Идеи",
    "📅 Контент-план"
]))
async def choose_content_type(message: Message, state: FSMContext):

    await state.clear()

    action_map = {
        "✍️ Пост": "post",
        "🖼 Пост с картинкой": "image_post",
        "🖼 Пост + картинка": "image_post",
        "🎠 Карусель": "carousel",
        "🎬 Reels": "reels",
        "🚀 Контент-пак": "content_pack",
        "💡 Идеи контента": "ideas",
        "💡 Идеи": "ideas",
        "📅 Контент-план": "plan",
    }

    if message.text in action_map:
        await state.update_data(action=action_map[message.text])
        await state.set_state(ContentState.waiting_prompt)
        await message.answer(
            "Напиши тему или промпт 👇\n\n"
            "Цель контента и визуальный стиль берутся из AI Профиля."
        )
        return
    if message.text in {"🎭 Стиль", "🎭 Стиль текста"}:
        await message.answer(
            "🎭 Стиль автора\n\n"
            "Здесь можно быстро описать стиль или обучить AI на твоих постах.\n\n"
            "✍️ Опиши стиль — коротко объясни, как писать.\n"
            "🧠 Обучить стилю — отправь 3–10 своих постов.\n"
            "🎭 Мой стиль — посмотреть сохранённый стиль.\n"
            "♻️ Сбросить стиль — начать заново.",
            reply_markup=style_menu
        )
        return True

    if message.text == "✍️ Опиши стиль":
        await state.set_state(ContentState.waiting_style_description)
        await message.answer(style_description_prompt(), reply_markup=style_menu)
        return True

    if message.text == "🎭 Мой стиль":
        style = await get_user_style(message.from_user.id)

        if not style:
            await message.answer(
                "🎭 Мой стиль\n\n"
                "Стиль пока не настроен.\n\n"
                "Нажми «✍️ Опиши стиль» или «🧠 Обучить стилю».",
                reply_markup=style_menu
            )
            return True

        await message.answer(
            "🎭 Твой сохранённый стиль:\n\n"
            f"{style[:2500]}",
            reply_markup=style_menu
        )
        return True

    if message.text in ["♻️ Сбросить стиль", "❌ Сбросить стиль"]:
        await reset_user_style, save_style_sample, get_style_samples(message.from_user.id)
        await message.answer(
            "✅ Стиль сброшен.\n\n"
            "Теперь AI снова будет писать в стандартном стиле.",
            reply_markup=style_menu
        )
        return True

    action_map = {
        "✍️ Пост": "post",
        "🎬 Reels": "reels",
        "🚀 Контент-пак": "content_pack",
        "💡 Идеи контента": "ideas",
        "💡 Идеи": "ideas",
        "📅 Контент-план": "plan"
    }

    await state.clear()
    await state.update_data(action=action_map[message.text])
    await state.set_state(ContentState.waiting_goal)

    await message.answer(
        "🎯 Какая цель контента?",
        reply_markup=goal_menu
    )


@router.message(ContentState.waiting_goal)
async def choose_content_goal(message: Message, state: FSMContext):

    if await cancel_user_state_if_button(message, state):
        return

    goal_map = {
        "🔥 Продать": "продать продукт или услугу",
        "🧠 Экспертность": "показать экспертность и доверие",
        "💬 Вовлечь": "вызвать комментарии и реакции",
        "🚀 Прогреть": "прогреть аудиторию к покупке"
    }

    if message.text in {"⬅️ Назад в создание", "⬅️ Назад в профиль"}:
        await state.clear()
        await message.answer(
            "🧠 AI Профиль",
            reply_markup=profile_menu
        )
        return

    if message.text not in goal_map:
        await message.answer(
            "Выбери цель кнопкой 👇",
            reply_markup=goal_menu
        )
        return

    await state.update_data(content_goal=goal_map[message.text])
    await state.set_state(ContentState.waiting_prompt)

    data = await state.get_data()
    action = data.get("action")

    examples = {
        "post": "Например:\nпродай консультацию по нейросетям для бизнеса",
        "image_post": "Например:\nпост о премиум детейлинге авто с дорогим визуалом",
        "carousel": "Например:\n5 ошибок предпринимателей при ведении контента",
        "reels": "Например:\nсценарий Reels про то, почему бизнесу нужен AI",
        "content_pack": "Например:\nконтент-пак для салона красоты на тему привлечения клиентов",
        "ideas": "Например:\nидеи контента для эксперта по инвестициям",
        "plan": "Например:\nконтент-план на месяц для онлайн-школы"
    }

    await message.answer(
        "Отлично. Теперь напиши тему или промпт 👇\n\n"
        f"{examples.get(action, '')}"
    )


@router.message(ContentState.waiting_image_style)
async def choose_image_style(message: Message, state: FSMContext):

    if await cancel_user_state_if_button(message, state):
        return

    style_map = {
        "💎 Luxury": "luxury",
        "⚡ Neon": "neon",
        "🖤 Dark": "dark",
        "🍏 Apple": "apple",
        "🏢 Business": "business",
        "🎨 Creative": "creative"
    }

    if message.text in {"⬅️ Назад в создание", "⬅️ Назад в профиль"}:
        await state.clear()
        await message.answer(
            "🧠 AI Профиль",
            reply_markup=profile_menu
        )
        return

    if message.text not in style_map:
        await message.answer(
            "Выбери стиль кнопкой 👇",
            reply_markup=image_style_menu
        )
        return

    await state.update_data(
        visual_style=style_map[message.text],
        visual_style_title=message.text
    )
    await state.clear()

    await message.answer(
        f"✅ Визуальный стиль выбран: {message.text}\n\n"
        "Теперь он вынесен в AI Профиль и не дублируется внутри каруселей/постов.",
        reply_markup=profile_menu
    )


@router.message(ContentState.waiting_carousel_style)
async def choose_carousel_style(message: Message, state: FSMContext):

    if await cancel_user_state_if_button(message, state):
        return

    style_map = {
        "💎 Luxury": "luxury",
        "⚡ Neon": "neon",
        "🖤 Dark": "dark",
        "🍏 Apple": "apple",
        "🏢 Business": "business",
        "🎨 Creative": "creative"
    }

    if message.text in {"⬅️ Назад в создание", "⬅️ Назад в профиль"}:
        await state.clear()
        await message.answer(
            "🧠 AI Профиль",
            reply_markup=profile_menu
        )
        return

    if message.text not in style_map:
        await message.answer(
            "Выбери стиль кнопкой 👇",
            reply_markup=carousel_style_menu
        )
        return

    await state.update_data(
        visual_style=style_map[message.text],
        visual_style_title=message.text
    )
    await state.clear()

    await message.answer(
        f"✅ Визуальный стиль выбран: {message.text}\n\n"
        "Теперь он вынесен в AI Профиль и не дублируется внутри каруселей/постов.",
        reply_markup=profile_menu
    )


@router.message(ContentState.waiting_prompt)
async def process_content_prompt(message: Message, state: FSMContext):

    if await cancel_user_state_if_button(message, state):
        return

    if message.text in GOAL_BUTTONS:
        await message.answer(
            "Цель уже выбрана ✅\n\n"
            "Теперь напиши тему или промпт текстом.\n"
            "Например: продай консультацию по нейросетям для бизнеса"
        )
        return

    user_id = message.from_user.id
    prompt = message.text.strip()

    data = await state.get_data()

    action = data.get("action")

    if not action:
        await message.answer(
            "Не понял, что нужно создать. Выбери формат заново 👇",
            reply_markup=create_menu
        )
        return

    visual_style = data.get("visual_style", "luxury")
    visual_style_title = data.get("visual_style_title", "💎 Luxury")
    content_goal = data.get("content_goal", "сделать сильный полезный контент")

    await state.clear()

    await register_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    style_block = await build_style_block(user_id)
    profile_block = await build_profile_block(user_id)

    memory = await get_user_memory(user_id)

    memory_block = f"""
    Предпочтения пользователя:

    Любимые темы:
    {memory.get("favorite_topics")}

    Любимый стиль:
    {memory.get("favorite_style")}

    Любимый CTA:
    {memory.get("preferred_cta")}

    Tone of voice:
    {memory.get("preferred_tone")}
    """

    memory_profile_block = await build_memory_profile_block(user_id)

    # =========================================
    # CONTENT PACK
    # =========================================

    if action == "content_pack":

        if not await can_use_feature(user_id, "content_pack"):
            await message.answer(
                "❌ Лимит FREE на контент-пак закончился."
            )
            return

        async def generate_content_pack_task():

            await message.answer(
                "🚀 Создаю контент-пак...\n\n"
                "Сейчас подготовлю пост, картинку, карусель, Reels и идеи."
            )

            # 1. Пост
            post_text = await ask_ai(
                build_post_prompt(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )
            )

            await send_long(message, "✍️ Пост\n\n" + post_text)

            # 2. Пост с картинкой
            try:
                image_post_text, image_prompt = await generate_ready_post(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )

                plan = await get_user_plan(user_id)

                image = await generate_quality_image(
                    image_prompt,
                    is_pro=(plan in ["vip", "premium", "pro"]),
                    visual_style=visual_style,
                    user_plan=plan
                )

                await message.answer_photo(
                    photo=BufferedInputFile(
                        image.getvalue(),
                        filename="content_pack_image.jpg"
                    ),
                    caption="🖼 Картинка для поста"
                )

                await send_long(message, "🖼 Пост с картинкой\n\n" + image_post_text)

            except Exception as e:
                print(f"CONTENT PACK IMAGE ERROR: {e}")
                await message.answer(
                    "⚠️ Картинку не удалось создать, но остальные материалы готовы."
                )

            # 3. Карусель
            carousel_text = await generate_ready_carousel(
                topic=prompt,
                style_block=style_block,
                profile_block=profile_block,
                memory_block=memory_block + memory_profile_block,
                content_goal=content_goal
            )

            try:
                plan_for_carousel = await get_user_plan(user_id)
                images = create_carousel_images(
                    carousel_text,
                    style=visual_style,
                    show_brand=not is_priority_plan(plan_for_carousel)
                )

                media = []

                for index, img in enumerate(images):
                    photo = BufferedInputFile(
                        img.getvalue(),
                        filename=f"pack_slide_{index + 1}.jpg"
                    )

                    if index == 0:
                        media.append(
                            InputMediaPhoto(
                                media=photo,
                                caption="🎠 Карусель"
                            )
                        )
                    else:
                        media.append(
                            InputMediaPhoto(media=photo)
                        )

                await message.answer_media_group(media)

            except Exception as e:
                print(f"CONTENT PACK CAROUSEL ERROR: {e}")

            await send_long(message, "🎠 Текст карусели\n\n" + carousel_text)

            # 4. Reels
            reels_text = await ask_ai(
                build_reels_prompt(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )
            )

            await send_long(message, "🎬 Reels-сценарий\n\n" + reels_text)

            # 5. Идеи
            ideas_text = await ask_ai(
                build_ideas_prompt(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )
            )

            await send_long(message, "💡 Дополнительные идеи\n\n" + ideas_text)

            await save_user_memory(
                user_id=user_id,
                favorite_topics=prompt,
                favorite_style=visual_style,
                preferred_cta="Подписывайся и пиши в ЛС",
                preferred_tone="живой, уверенный, современный"
            )

            await track_usage(user_id, "content_pack")

            await message.answer(
                "✅ Контент-пак готов\n\n"
                "Что можно сделать дальше?",
                reply_markup=after_generation_menu
            )

        plan_type = await get_user_plan(user_id)

        queue_position = await add_to_queue(
            user_id=user_id,
            task_name="content_pack_generation",
            task_func=generate_content_pack_task,
            is_pro=is_priority_plan(plan_type)
        )

        await message.answer(
            "🚀 Контент-пак добавлен в очередь\n\n"
            f"Позиция: {queue_position}"
        )

        return

    # =========================================
    # POST
    # =========================================

    if action == "post":

        async def generate_post_task():

            result = await ask_ai(
                build_post_prompt(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )
            )

            await save_user_memory(
                user_id=user_id,
                favorite_topics=prompt,
                favorite_style=visual_style,
                preferred_cta="Подписывайся и пиши в ЛС",
                preferred_tone="живой, уверенный, современный"
            )

            await track_usage(user_id, "content_factory")

            await send_long(message, result)

            await message.answer(
                "Готово ✅\n\n"
                "Что можно сделать дальше?",
                reply_markup=after_generation_menu
            )

        plan_type = await get_user_plan(user_id)

        queue_position = await add_to_queue(
            user_id=user_id,
            task_name="post_generation",
            task_func=generate_post_task,
            is_pro=is_priority_plan(plan_type)
        )

        await message.answer(
            "✍️ Пост добавлен в очередь\n\n"
            f"Позиция: {queue_position}"
        )

        return

    # =========================
    # IMAGE POST
    # =========================

    if action == "image_post":

        if not await can_use_feature(user_id, "post_image"):
            await message.answer(
                "❌ Лимит FREE на картинки закончился. Оформи PRO."
            )
            return

        async def generate_image_post_task():

            try:

                await message.answer(
                    "🧠 Пишу пост и создаю изображение..."
                )

                plan = await get_user_plan(user_id)

                post_text, image_prompt = await generate_ready_post(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )

                image_bytes = await generate_quality_image(
                    image_prompt,
                    is_pro=(plan in ["vip", "premium", "pro"]),
                    visual_style=visual_style,
                    user_plan=plan
                )

                photo = BufferedInputFile(
                    image_bytes.getvalue(),
                    filename="ready_post.jpg"
                )

                await message.answer("✨ Готовый пост создан")

                await message.answer_photo(photo=photo)

                await send_long(message, post_text)

                await message.answer(
                    "Готово ✅\n\n"
                    "Что можно сделать дальше?",
                    reply_markup=after_generation_menu
                )

                await track_usage(
                    user_id,
                    "post_image"
                )

            except Exception as e:

                print(f"IMAGE POST ERROR: {e}")

                await message.answer(
                    "❌ Ошибка генерации изображения"
                )

        plan = await get_user_plan(user_id)

        queue_position = await add_to_queue(
            user_id=user_id,
            task_name="image_post_generation",
            task_func=generate_image_post_task,
            is_pro=is_priority_plan(plan)
        )

        await message.answer(
            f"🖼 Пост с картинкой добавлен в очередь\n\n"
            f"Позиция: {queue_position}"
        )

        return

    # =========================
    # CAROUSEL
    # =========================

    if action == "carousel":

        async def generate_carousel_task():

            carousel_text = await generate_ready_carousel(
                topic=prompt,
                style_block=style_block,
                profile_block=profile_block,
                memory_block=memory_block + memory_profile_block,
                content_goal=content_goal
            )


            plan_for_carousel = await get_user_plan(user_id)
            images = create_carousel_images(
                carousel_text,
                style=visual_style,
                show_brand=not is_priority_plan(plan_for_carousel)
            )

            media = []

            for index, img in enumerate(images):

                photo = BufferedInputFile(
                    img.getvalue(),
                    filename=f"slide_{index + 1}.jpg"
                )

                if index == 0:

                    media.append(
                        InputMediaPhoto(
                            media=photo,
                            caption="🎠 Карусель готова"
                        )
                    )

                else:

                    media.append(
                        InputMediaPhoto(media=photo)
                    )

            await message.answer_media_group(media)

            await message.answer(
                "📝 Текст карусели:\n\n"
                f"{carousel_text}"
            )

            await track_usage(
                user_id,
                "content_factory"
            )

            await message.answer(
                "🎠 Карусель готова ✅\n\n"
                "Что можно сделать дальше?",
                reply_markup=after_generation_menu
            )

        plan = await get_user_plan(user_id)

        queue_position = await add_to_queue(
            user_id=user_id,
            task_name="carousel_generation",
            task_func=generate_carousel_task,
            is_pro=is_priority_plan(plan)
        )

        await message.answer(
            "🎠 Карусель добавлена в очередь\n\n"
            f"Позиция: {queue_position}"
        )

        return

        # =========================
    # REELS
    # =========================

    if action == "reels":

        async def generate_reels_task():

            result = await ask_ai(
                build_reels_prompt(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )
            )
    

            await send_long(message, result)

            await track_usage(
                user_id,
                "content_factory"
            )

            await message.answer(
                "🎬 Reels-сценарий готов ✅\n\n"
                "Что можно сделать дальше?",
                reply_markup=after_generation_menu
            )

        plan = await get_user_plan(user_id)

        queue_position = await add_to_queue(
            user_id=user_id,
            task_name="reels_generation",
            task_func=generate_reels_task,
            is_pro=is_priority_plan(plan)
        )

        await message.answer(
            "🎬 Reels добавлен в очередь\n\n"
            f"Позиция: {queue_position}"
        )

        return

    # =========================
    # IDEAS
    # =========================

    if action == "ideas":

        async def generate_ideas_task():

            result = await ask_ai(
                build_ideas_prompt(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )
            )


            await send_long(message, result)

            await message.answer(
                "💡 Идеи готовы ✅\n\n"
                "Что можно сделать дальше?",
                reply_markup=after_generation_menu
            )

        plan = await get_user_plan(user_id)

        queue_position = await add_to_queue(
            user_id=user_id,
            task_name="ideas_generation",
            task_func=generate_ideas_task,
            is_pro=is_priority_plan(plan)
        )

        await message.answer(
            "💡 Идеи добавлены в очередь\n\n"
            f"Позиция: {queue_position}"
        )

        return

    # =========================
    # PLAN
    # =========================

    if action == "plan":

        async def generate_plan_task():

            result = await ask_ai(
                build_plan_prompt(
                    topic=prompt,
                    style_block=style_block,
                    profile_block=profile_block,
                    memory_block=memory_block + memory_profile_block,
                    content_goal=content_goal
                )
            )

            await send_long(message, result)

            await message.answer(
                "📅 Контент-план готов ✅\n\n"
                "Что можно сделать дальше?",
                reply_markup=after_generation_menu
            )

        plan = await get_user_plan(user_id)

        queue_position = await add_to_queue(
            user_id=user_id,
            task_name="plan_generation",
            task_func=generate_plan_task,
            is_pro=is_priority_plan(plan)
        )

        await message.answer(
            "📅 Контент-план добавлен в очередь\n\n"
            f"Позиция: {queue_position}"
        )

        return
