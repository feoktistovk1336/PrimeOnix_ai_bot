from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards import (
    create_menu,
    content_menu,
    profile_menu,
    goal_menu,
    image_style_menu,
    after_generation_menu,
    main_menu,
    admin_main_menu,
)
from database.db import (
    register_user,
    get_user_plan,
    get_user_profile,
    save_user_profile_field,
    get_referral_stats,
    get_tariff_info,
    get_subscription_info,
    get_feature_limit,
    get_daily_usage,
    can_use_feature,
    track_usage,
    get_user_style,
    get_user_memory,
)
from services.ai import ask_ai
from services.sender import send_long
from services.image_service import generate_quality_image
from services.ready_post_service import generate_ready_post
from services.ready_carousel_service import generate_ready_carousel
from services.carousel_service import create_carousel_images
from services.memory import build_memory_profile_block
from services.prompt_engine import build_post_prompt, build_reels_prompt, build_ideas_prompt, build_plan_prompt

router = Router()


class V2State(StatesGroup):
    waiting_content_prompt = State()
    waiting_profile_goal = State()
    waiting_visual_style = State()


def _home(user_id: int):
    return admin_main_menu if settings.ADMIN_ID and user_id == settings.ADMIN_ID else main_menu


def _is_priority(plan: str) -> bool:
    return (plan or "free").lower() in {"start_premium", "plus", "vip", "premium", "pro"}


GOAL_MAP = {
    "🔥 Продать": "продать продукт или услугу",
    "🧠 Экспертность": "показать экспертность и доверие",
    "💬 Вовлечь": "вызвать комментарии и реакции",
    "🚀 Прогреть": "прогреть аудиторию к покупке",
}

STYLE_MAP = {
    "💎 Luxury": "luxury",
    "⚡ Neon": "neon",
    "🖤 Dark": "dark",
    "🍏 Apple": "apple",
    "🏢 Business": "business",
    "🎨 Creative": "creative",
}

ACTION_MAP = {
    "✍️ Пост": "post",
    "🖼 Пост с картинкой": "image_post",
    "🖼 Пост + картинка": "image_post",
    "🎠 Карусель": "carousel",
    "🎬 Reels": "reels",
    "🚀 Контент-пак": "content_pack",
    "💡 Идеи": "ideas",
    "💡 Идеи контента": "ideas",
    "📅 Контент-план": "plan",
    "✍️ Rewrite": "rewrite",
    "🎭 Brand Voice": "brand_voice",
    "🎯 Viral Hooks": "hooks",
}

ACTION_TITLES = {
    "post": "✍️ Пост",
    "image_post": "🖼 Пост + картинка",
    "carousel": "🎠 Карусель",
    "reels": "🎬 Reels",
    "content_pack": "🚀 Контент-пак",
    "ideas": "💡 Идеи",
    "plan": "📅 Контент-план",
    "rewrite": "✍️ Rewrite",
    "brand_voice": "🎭 Brand Voice",
    "hooks": "🎯 Viral Hooks",
}


async def _style_block(user_id: int) -> str:
    style = await get_user_style(user_id)
    if not style:
        return "Пиши красиво, уверенно, современно, без воды, с сильным хуком."
    return f"Стиль пользователя:\n{style}\nСохраняй тон, ритм и манеру, но не копируй дословно."


async def _profile_block(user_id: int) -> str:
    profile = await get_user_profile(user_id)
    return f"""
AI Профиль пользователя:
Ниша: {profile.get('niche') or 'не указано'}
Аудитория: {profile.get('audience') or 'не указано'}
Оффер: {profile.get('offer') or 'не указано'}
Город: {profile.get('city') or 'не указано'}
CTA: {profile.get('cta') or 'не указано'}
Цель контента: {profile.get('content_goal') or 'сделать сильный полезный контент'}
Визуальный стиль: {profile.get('visual_style_title') or 'не указан'}
"""


async def _memory_block(user_id: int) -> str:
    memory = await get_user_memory(user_id)
    memory_profile = await build_memory_profile_block(user_id)
    return f"""
Предпочтения пользователя:
Любимые темы: {memory.get('favorite_topics')}
Любимый стиль: {memory.get('favorite_style')}
Любимый CTA: {memory.get('preferred_cta')}
Tone of voice: {memory.get('preferred_tone')}
{memory_profile}
"""


@router.message(F.text == "📊 Кабинет")
async def v2_cabinet(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    await register_user(user_id, message.from_user.username, message.from_user.first_name)

    tariff = await get_tariff_info(user_id)
    sub = await get_subscription_info(user_id)
    ref_stats = await get_referral_stats(user_id)
    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

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
    limits = []
    for feature, title in features:
        used = await get_daily_usage(user_id, feature)
        limit = await get_feature_limit(user_id, feature)
        limits.append(f"{title}: {used}/{limit}")

    await message.answer(
        "📊 <b>Личный кабинет</b>\n\n"
        f"💎 <b>Тариф:</b> {tariff['title']}\n"
        f"⏳ <b>Осталось дней:</b> {sub['days_left']}\n"
        f"📅 <b>Дата окончания:</b> {sub['pro_until'] or 'нет'}\n\n"
        f"🎁 <b>Приглашено друзей:</b> {ref_stats['total_referrals']}\n"
        f"🎁 <b>Бонусных дней:</b> {ref_stats['premium_days']}\n\n"
        "📈 <b>Лимиты на сегодня:</b>\n" + "\n".join(limits) + "\n\n"
        "🔗 <b>Твоя реферальная ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        "Нажми на ссылку выше и скопируй её.",
        reply_markup=_home(user_id),
        parse_mode="HTML",
    )


@router.message(F.text == "🚀 Создать")
async def v2_create(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🚀 <b>Создать</b>\n\n"
        "Выбери формат. Стили и цели больше не дублируются внутри каруселей и картинок — они задаются в AI Профиле.",
        reply_markup=create_menu,
        parse_mode="HTML",
    )


@router.message(F.text == "🛠 Инструменты")
async def v2_tools(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🛠 <b>Инструменты</b>\n\n"
        "Идеи, хуки, лид-магнит, rewrite, CTA, серия постов и анализ.",
        reply_markup=content_menu,
        parse_mode="HTML",
    )


@router.message(F.text == "🎯 Цель контента")
async def v2_profile_goal(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(V2State.waiting_profile_goal)
    await message.answer(
        "🎯 <b>Цель контента</b>\n\n"
        "Выбери один раз. Эта цель будет применяться ко всем форматам: постам, картинкам, каруселям, Reels и контент-пакам.",
        reply_markup=goal_menu,
        parse_mode="HTML",
    )


@router.message(V2State.waiting_profile_goal)
async def v2_save_goal(message: Message, state: FSMContext):
    if message.text not in GOAL_MAP:
        await message.answer("Выбери цель кнопкой 👇", reply_markup=goal_menu)
        return
    await save_user_profile_field(message.from_user.id, "content_goal", GOAL_MAP[message.text])
    await save_user_profile_field(message.from_user.id, "content_goal_title", message.text)
    await state.clear()
    await message.answer(
        f"✅ Цель сохранена: {message.text}\n\nТеперь она будет применяться автоматически.",
        reply_markup=profile_menu,
    )


@router.message(F.text == "🎨 Стиль визуала")
async def v2_visual_style(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(V2State.waiting_visual_style)
    await message.answer(
        "🎨 <b>Стиль визуала</b>\n\n"
        "Выбери один раз. Этот стиль будет применяться к картинкам, каруселям и обложкам Reels.",
        reply_markup=image_style_menu,
        parse_mode="HTML",
    )


@router.message(V2State.waiting_visual_style)
async def v2_save_visual_style(message: Message, state: FSMContext):
    if message.text not in STYLE_MAP:
        await message.answer("Выбери стиль кнопкой 👇", reply_markup=image_style_menu)
        return
    await save_user_profile_field(message.from_user.id, "visual_style", STYLE_MAP[message.text])
    await save_user_profile_field(message.from_user.id, "visual_style_title", message.text)
    await state.clear()
    await message.answer(
        f"✅ Визуальный стиль сохранён: {message.text}\n\nТеперь он будет применяться автоматически.",
        reply_markup=profile_menu,
    )


@router.message(F.text.in_(ACTION_MAP.keys()))
async def v2_choose_content(message: Message, state: FSMContext):
    await state.clear()
    action = ACTION_MAP[message.text]
    await state.update_data(action=action)
    await state.set_state(V2State.waiting_content_prompt)
    await message.answer(
        f"{ACTION_TITLES[action]}\n\n"
        "Напиши тему или промпт 👇\n\n"
        "Цель контента и визуальный стиль берутся из AI Профиля."
    )


@router.message(V2State.waiting_content_prompt)
async def v2_generate_content(message: Message, state: FSMContext):
    user_id = message.from_user.id
    prompt = (message.text or "").strip()

    # If user presses another tool/format while a prompt is expected, switch mode instead of treating the button as input.
    if prompt in ACTION_MAP:
        action = ACTION_MAP[prompt]
        await state.update_data(action=action)
        await state.set_state(V2State.waiting_content_prompt)
        await message.answer(
            f"{ACTION_TITLES.get(action, prompt)}\n\n"
            "Режим переключён. Напиши тему, текст или промпт 👇\n\n"
            "Цель контента и визуальный стиль берутся из AI Профиля."
        )
        return

    data = await state.get_data()
    action = data.get("action")

    if not prompt:
        await message.answer("Напиши тему или промпт текстом.")
        return

    await state.clear()
    await register_user(user_id, message.from_user.username, message.from_user.first_name)

    profile = await get_user_profile(user_id)
    plan = await get_user_plan(user_id)
    content_goal = profile.get("content_goal") or "сделать сильный полезный контент"
    visual_style = profile.get("visual_style") or "business"
    style_block = await _style_block(user_id)
    profile_block = await _profile_block(user_id)
    memory_block = await _memory_block(user_id)

    if action == "image_post":
        if not await can_use_feature(user_id, "post_image"):
            await message.answer("❌ Лимит на картинки закончился. Оформи PRO.")
            return
        await message.answer("🧠 Пишу пост и создаю изображение...")
        try:
            post_text, image_prompt = await generate_ready_post(
                topic=prompt,
                style_block=style_block,
                profile_block=profile_block,
                memory_block=memory_block,
                content_goal=content_goal,
            )
            image_bytes = await generate_quality_image(
                image_prompt,
                is_pro=(plan in ["vip", "premium", "pro"]),
                visual_style=visual_style,
                user_plan=plan,
            )
            await message.answer("✨ Готовый пост создан")
            await message.answer_photo(
                BufferedInputFile(image_bytes.getvalue(), filename="ready_post.jpg"),
                caption=post_text[:1024],
            )
            # Для поста с картинкой не дублируем полный текст вторым сообщением.
            # Если текст длиннее лимита подписи, он остается доступен в режиме редактирования/перегенерации.
            await track_usage(user_id, "post_image")
        except Exception as exc:
            await message.answer(f"❌ Ошибка генерации поста с картинкой: {exc}")
            return

    elif action == "carousel":
        if not await can_use_feature(user_id, "carousel"):
            await message.answer("❌ Лимит на карусели на сегодня закончился. Оформи тариф выше.")
            return
        await message.answer("🎠 Создаю карусель...")
        carousel_text = await generate_ready_carousel(prompt, style_block, profile_block, memory_block, content_goal)
        try:
            images = create_carousel_images(carousel_text, style=visual_style, show_brand=not _is_priority(plan))
            media = []
            for index, img in enumerate(images):
                photo = BufferedInputFile(img.getvalue(), filename=f"slide_{index+1}.jpg")
                media.append(InputMediaPhoto(media=photo, caption="🎠 Карусель готова" if index == 0 else None))
            await message.answer_media_group(media)
        except Exception:
            pass
        await send_long(message, "📝 Текст карусели:\n\n" + carousel_text)
        await track_usage(user_id, "carousel")

    elif action == "reels":
        if not await can_use_feature(user_id, "reels"):
            await message.answer("❌ Лимит Reels на сегодня закончился. Оформи тариф выше.")
            return
        await message.answer("🎬 Создаю Reels-пакет...")
        result = await ask_ai(build_reels_prompt(prompt, style_block, profile_block, memory_block, content_goal))
        await send_long(message, result)
        await track_usage(user_id, "reels")

    elif action == "ideas":
        await message.answer("💡 Генерирую идеи...")
        result = await ask_ai(build_ideas_prompt(prompt, style_block, profile_block, memory_block, content_goal))
        await send_long(message, result)

    elif action == "plan":
        await message.answer("📅 Создаю контент-план...")
        result = await ask_ai(build_plan_prompt(prompt, style_block, profile_block, memory_block, content_goal))
        await send_long(message, result)


    elif action == "rewrite":
        await message.answer("✍️ Переписываю сильнее...")
        result = await ask_ai(f"""
Перепиши текст для Telegram/Instagram.

Исходный текст или тема:
{prompt}

Сделай:
- сильный хук
- короткие абзацы
- живой человеческий стиль
- без воды
- понятный CTA

Учитывай цель контента:
{content_goal}

{profile_block}
{style_block}
""")
        await send_long(message, result)
        await track_usage(user_id, "rewrite")

    elif action == "brand_voice":
        await message.answer("🎭 Переписываю в Brand Voice...")
        result = await ask_ai(f"""
Ты — Brand Voice редактор. Перепиши текст/тему в фирменной манере пользователя.

Материал:
{prompt}

Требования:
- сохранить смысл
- сделать стиль узнаваемым
- без лишней воды
- сильный хук
- CTA в конце

{profile_block}
{memory_block}
{style_block}
""")
        await send_long(message, result)
        await track_usage(user_id, "brand_rewrite")

    elif action == "hooks":
        await message.answer("🎯 Генерирую хуки...")
        result = await ask_ai(f"""
Сгенерируй 20 сильных хуков для темы:
{prompt}

Формат:
1. хук
2. хук

Сделай разные типы: боль, интрига, выгода, ошибка, провокация, быстрый результат.
Цель контента: {content_goal}
{profile_block}
""")
        await send_long(message, result)

    elif action == "content_pack":
        await message.answer("🚀 Создаю контент-пак...")
        post = await ask_ai(build_post_prompt(prompt, style_block, profile_block, memory_block, content_goal))
        reels = await ask_ai(build_reels_prompt(prompt, style_block, profile_block, memory_block, content_goal))
        ideas = await ask_ai(build_ideas_prompt(prompt, style_block, profile_block, memory_block, content_goal))
        await send_long(message, "✍️ Пост\n\n" + post)
        await send_long(message, "🎬 Reels\n\n" + reels)
        await send_long(message, "💡 Идеи\n\n" + ideas)
        await track_usage(user_id, "content_pack")

    else:
        if not await can_use_feature(user_id, "content_factory"):
            await message.answer("❌ Лимит постов на сегодня закончился. Оформи тариф выше.")
            return
        await message.answer("✍️ Пишу пост...")
        result = await ask_ai(build_post_prompt(prompt, style_block, profile_block, memory_block, content_goal))
        await send_long(message, result)
        await track_usage(user_id, "content_factory")

    await message.answer("✅ Материал готов.", reply_markup=after_generation_menu)
