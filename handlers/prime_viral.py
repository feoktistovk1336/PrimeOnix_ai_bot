from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database.db import register_user, get_user_memory, get_user_plan
from services.ai import ask_ai
from services.queue import add_to_queue
from services.content_queue import add_prime_content, list_prime_content, mark_prime_content, delete_prime_content, STATUS_READY
from services.sender import send_long
from services.memory import build_memory_profile_block
from services.prompt_engine import (
    build_prime_viral_reels_prompt,
    build_prime_viral_carousel_prompt,
    build_prime_hook_bank_prompt,
    build_prime_lead_magnet_lab_prompt,
    build_prime_ai_agents_prompt,
)
from handlers.content import build_style_block, build_profile_block, is_priority_plan
from handlers.admin import is_admin
from keyboards import prime_panel_menu, prime_tool_menu, prime_topic_menu, prime_after_generation_menu, prime_queue_menu


router = Router()

LAST_PRIME_RESULT = {}


class PrimeViralState(StatesGroup):
    waiting_topic = State()
    waiting_custom_topic = State()


TOOL_SETTINGS = {
    "🎬 Viral Reels": {
        "key": "viral_reels",
        "title": "🎬 Viral Reels Engine",
        "intro": (
            "🎬 <b>Viral Reels Engine</b>\n\n"
            "Создаёт Reels под охваты и переходы в Telegram.\n\n"
            "На выходе получишь:\n"
            "• сильный hook\n"
            "• сценарий по кадрам\n"
            "• текст на экране\n"
            "• CTA в Direct / Telegram\n"
            "• продолжение для TG\n"
            "• viral score\n\n"
            "Выбери готовую тему или нажми «✍️ Своя тема»."
        ),
        "loading": "🎬 Собираю viral Reels: hook, retention, CTA, TG-продолжение и viral score...",
    },
    "🎠 Viral Carousels": {
        "key": "viral_carousel",
        "title": "🎠 Viral Carousel Engine",
        "intro": (
            "🎠 <b>Viral Carousel Engine</b>\n\n"
            "Создаёт карусели, которые хочется сохранить и досмотреть.\n\n"
            "На выходе получишь:\n"
            "• идею карусели\n"
            "• структуру слайдов\n"
            "• текст каждого слайда\n"
            "• CTA\n"
            "• Telegram-продолжение\n"
            "• оценку силы связки\n\n"
            "Выбери готовую тему или нажми «✍️ Своя тема»."
        ),
        "loading": "🎠 Собираю карусель: слайды, удержание, сохранения, CTA и TG-продолжение...",
    },
    "🎯 Hook Generator": {
        "key": "hook_bank",
        "title": "🎯 Hook Generator",
        "intro": (
            "🎯 <b>Hook Generator</b>\n\n"
            "Генерирует банк хуков для Reels, каруселей, постов и Direct.\n\n"
            "На выходе получишь хуки по углам:\n"
            "• боль\n"
            "• выгода\n"
            "• интрига\n"
            "• конфликт\n"
            "• страх ошибки\n"
            "• быстрый результат\n\n"
            "Выбери готовую тему или нажми «✍️ Своя тема»."
        ),
        "loading": "🎯 Генерирую сильные hooks по разным углам: боль, выгода, интрига, конфликт...",
    },
    "🎁 Lead Magnet Lab": {
        "key": "lead_magnet_lab",
        "title": "🎁 Lead Magnet Lab",
        "intro": (
            "🎁 <b>Lead Magnet Lab</b>\n\n"
            "Создаёт бонус, ради которого люди переходят из Instagram в Telegram.\n\n"
            "На выходе получишь:\n"
            "• идею лид-магнита\n"
            "• название\n"
            "• структуру файла/поста\n"
            "• CTA для Reels\n"
            "• DM-ответ\n"
            "• Telegram-выдачу\n\n"
            "Выбери готовую тему или нажми «✍️ Своя тема»."
        ),
        "loading": "🎁 Собираю лид-магнит: оффер, структура, посты, CTA и Telegram-выдача...",
    },
    "🤖 AI Agents": {
        "key": "ai_agents",
        "title": "🤖 AI Agents Campaign",
        "intro": (
            "🤖 <b>AI Agents</b>\n\n"
            "Запускает команду AI-агентов для одной контент-задачи.\n\n"
            "Команда собирает:\n"
            "• стратегию\n"
            "• Reels\n"
            "• карусель\n"
            "• CTA\n"
            "• Telegram-продолжение\n"
            "• план действий\n\n"
            "Выбери готовую задачу или нажми «✍️ Своя тема»."
        ),
        "loading": "🤖 Запускаю команду агентов: strategist, reels AI, CTA AI, funnel AI, analyzer...",
    },
}

PRESET_TOPICS = {
    "🔥 AI-контент": "AI-контент: как создавать посты, Reels и карусели быстрее конкурентов и вести людей из Instagram в Telegram",
    "💸 Продажи": "продажи через контент: как прогреть человека от Reels до Telegram и довести до покупки/подписки",
    "🎬 Reels/охваты": "viral Reels: как делать ролики с сильным хуком, удержанием и переходом в Telegram",
    "🎁 Лид-магнит": "лид-магнит: файл с 10 бесплатными нейронками, промптами и порядком создания контента",
    "🧲 Трафик IG→TG": "трафик Instagram в Telegram: Reels, кодовое слово, DM-ответ, Telegram-пост и прогрев",
    "🧠 Экспертность": "экспертность через AI-контент: как показать пользу, доверие и привести аудиторию в Telegram",
}

INFO_TEXTS = {
    "📤 Instagram AutoPost": (
        "📤 <b>Instagram AutoPost</b>\n\n"
        "Раздел для автопубликации Reels и каруселей в Instagram.\n\n"
        "Логика работы:\n"
        "• PRIME PANEL создаёт контент\n"
        "• ты одобряешь материал\n"
        "• задача уходит в n8n/сервер\n"
        "• публикация выходит в Instagram\n\n"
        "Для подключения нужны: Instagram Business/Creator, Facebook Page, Meta App, access token и webhook."
    ),
    "📤 Telegram AutoPost": (
        "📤 <b>Telegram AutoPost</b>\n\n"
        "Раздел для постов, которые продолжают тему Instagram.\n\n"
        "Схема:\n"
        "• Instagram цепляет\n"
        "• человек переходит в Telegram\n"
        "• Telegram даёт продолжение\n"
        "• дальше идёт прогрев, бонус или продажа"
    ),
    "📈 Analytics": (
        "📈 <b>Analytics</b>\n\n"
        "Раздел для анализа роста и связок IG → TG.\n\n"
        "Что отслеживаем:\n"
        "• темы\n"
        "• хуки\n"
        "• CTA\n"
        "• переходы в Telegram\n"
        "• лучшие Reels\n"
        "• лид-магниты"
    ),
    "⚙️ Система": (
        "⚙️ <b>Система</b>\n\n"
        "Технический центр PRIME-системы.\n\n"
        "Здесь удобно держать контроль над:\n"
        "• Instagram API\n"
        "• n8n webhooks\n"
        "• Telegram автопостингом\n"
        "• генерацией изображений\n"
        "• лимитами API\n"
        "• ошибками публикаций"
    ),
}


def _memory_block(memory: dict, memory_profile_block: str) -> str:
    return f"""
Предпочтения пользователя:

Любимые темы:
{memory.get('favorite_topics')}

Любимый стиль:
{memory.get('favorite_style')}

Любимый CTA:
{memory.get('preferred_cta')}

Tone of voice:
{memory.get('preferred_tone')}

{memory_profile_block}
"""


def _prime_home_text() -> str:
    return (
        "🚀 <b>PRIME PANEL</b>\n\n"
        "Центр управления AI-контентом и автоворонками.\n\n"
        "Выбери инструмент ниже 👇"
    )


@router.message(F.text.in_(TOOL_SETTINGS.keys()))
async def open_prime_tool(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    tool = TOOL_SETTINGS[message.text]
    await state.clear()
    await state.update_data(tool_key=tool["key"], tool_title=tool["title"])
    await state.set_state(PrimeViralState.waiting_topic)
    await message.answer(tool["intro"], reply_markup=prime_topic_menu, parse_mode="HTML")


@router.message(F.text.in_(INFO_TEXTS.keys()))
async def open_prime_info(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.clear()
    await message.answer(INFO_TEXTS[message.text], reply_markup=prime_panel_menu, parse_mode="HTML")


@router.message(PrimeViralState.waiting_topic)
async def choose_prime_topic(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    text = (message.text or "").strip()

    if text in ["⬅️ Назад в PRIME PANEL", "❌ Отмена"]:
        await state.clear()
        await message.answer(_prime_home_text(), reply_markup=prime_panel_menu, parse_mode="HTML")
        return

    if text == "✍️ Своя тема":
        await state.set_state(PrimeViralState.waiting_custom_topic)
        await message.answer(
            "✍️ <b>Своя тема</b>\n\n"
            "Напиши тему или задачу одним сообщением.\n\n"
            "Пример:\n"
            "Сделай воронку Reels → Telegram на тему 10 бесплатных нейронок для контента",
            reply_markup=prime_tool_menu,
            parse_mode="HTML",
        )
        return

    topic = PRESET_TOPICS.get(text, text)
    await _start_prime_generation(message, state, topic)


@router.message(PrimeViralState.waiting_custom_topic)
async def custom_prime_topic(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    text = (message.text or "").strip()

    if text in ["⬅️ Назад в PRIME PANEL", "❌ Отмена"]:
        await state.clear()
        await message.answer(_prime_home_text(), reply_markup=prime_panel_menu, parse_mode="HTML")
        return

    if len(text) < 6:
        await message.answer("Напиши тему чуть подробнее, чтобы AI собрал сильную систему.")
        return

    await _start_prime_generation(message, state, text)


async def _start_prime_generation(message: Message, state: FSMContext, topic: str):
    data = await state.get_data()
    tool_key = data.get("tool_key")
    tool_title = data.get("tool_title", "PRIME")
    await state.clear()

    user_id = message.from_user.id
    await register_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    style_block = await build_style_block(user_id)
    profile_block = await build_profile_block(user_id)
    memory = await get_user_memory(user_id)
    memory_profile_block = await build_memory_profile_block(user_id)
    mem = _memory_block(memory, memory_profile_block)

    builders = {
        "viral_reels": build_prime_viral_reels_prompt,
        "viral_carousel": build_prime_viral_carousel_prompt,
        "hook_bank": build_prime_hook_bank_prompt,
        "lead_magnet_lab": build_prime_lead_magnet_lab_prompt,
        "ai_agents": build_prime_ai_agents_prompt,
    }
    builder = builders.get(tool_key, build_prime_viral_reels_prompt)
    loading = next((v["loading"] for v in TOOL_SETTINGS.values() if v["key"] == tool_key), "🚀 Собираю PRIME-систему...")

    async def generate_task():
        await message.answer(loading)
        result = await ask_ai(
            builder(
                topic=topic,
                style_block=style_block,
                profile_block=profile_block,
                memory_block=mem,
            )
        )
        full_result = f"{tool_title}\n\nТема: {topic}\n\n{result}"
        LAST_PRIME_RESULT[user_id] = {
            "tool": tool_title,
            "topic": topic,
            "content": full_result,
        }
        await send_long(message, full_result)
        await message.answer(
            "✅ <b>Готово.</b>\n\n"
            "Теперь управляй материалом кнопками ниже 👇\n\n"
            "🔁 Улучшить — переписать сильнее\n"
            "🔥 Усилить хук — сделать первый экран мощнее\n"
            "🧲 Усилить CTA — усилить переход в Direct/TG\n"
            "🔗 TG-продолжение — сделать Telegram-продолжение\n"
            "📌 Сохранить в очередь — положить в контент-очередь\n"
            "📤 Подготовить к публикации — собрать caption/DM/TG/checklist\n"
            "🚀 Отправить в n8n — отправить готовый материал в workflow",
            reply_markup=prime_after_generation_menu,
            parse_mode="HTML",
        )

    plan = await get_user_plan(user_id)
    queue_position = await add_to_queue(
        user_id=user_id,
        task_name=f"prime_{tool_key}",
        task_func=generate_task,
        is_pro=is_priority_plan(plan),
    )

    await message.answer(
        "🚀 PRIME-задача добавлена в очередь\n\n"
        f"Позиция: {queue_position}"
    )



def _get_last(user_id: int):
    return LAST_PRIME_RESULT.get(user_id)


async def _require_last(message: Message):
    last = _get_last(message.from_user.id)
    if not last:
        await message.answer(
            "Сначала сгенерируй материал в PRIME PANEL, а потом дорабатывай его кнопками.",
            reply_markup=prime_panel_menu,
        )
        return None
    return last


def _improve_prompt(last: dict, mode: str) -> str:
    instructions = {
        "🔁 Улучшить": "улучши весь материал: сделай сильнее хук, понятнее структуру, меньше воды, больше конкретики и пользы",
        "🔥 Усилить хук": "перепиши только блоки hook/первый экран/первые 2 секунды. Дай 15 более сильных вариантов и выбери лучший",
        "🧲 Усилить CTA": "усиль CTA: дай варианты для Direct, Telegram, комментариев, сохранений и перехода в Telegram. Выбери лучший",
        "🔗 TG-продолжение": "сделай сильное Telegram-продолжение: готовый пост, промпт, чек-лист, лид-магнит и следующий шаг",
        "📤 Подготовить к публикации": "подготовь материал к публикации: caption, кодовое слово, DM-ответ, TG-пост, чек-лист файлов, порядок публикации и что проверить перед запуском",
    }
    task = instructions.get(mode, instructions["🔁 Улучшить"])
    return f"""
Ты — senior viral strategist и редактор PRIME PANEL.

Задача: {task}.

Исходная тема:
{last.get('topic')}

Исходный материал:
{last.get('content')}

Правила:
- не используй markdown-таблицы
- без звёздочек
- без воды
- пиши на русском
- сохраняй связку Instagram → Telegram
- результат должен быть сразу пригоден к использованию
"""


@router.message(F.text.in_({"🔁 Улучшить", "🔥 Усилить хук", "🧲 Усилить CTA", "🔗 TG-продолжение", "📤 Подготовить к публикации"}))
async def prime_improve_generated(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    last = await _require_last(message)
    if not last:
        return

    await message.answer("🧠 Дорабатываю материал...")
    result = await ask_ai(_improve_prompt(last, message.text))
    full_result = f"{message.text}\n\nТема: {last.get('topic')}\n\n{result}"
    LAST_PRIME_RESULT[message.from_user.id] = {
        "tool": message.text,
        "topic": last.get("topic", "PRIME"),
        "content": full_result,
    }
    await send_long(message, full_result)
    await message.answer("✅ Материал готов.", reply_markup=prime_after_generation_menu)


@router.message(F.text == "📌 Сохранить в очередь")
async def prime_save_to_queue(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    last = await _require_last(message)
    if not last:
        return

    item = add_prime_content(
        user_id=message.from_user.id,
        tool=last.get("tool", "PRIME"),
        topic=last.get("topic", "Без темы"),
        content=last.get("content", ""),
        status="draft",
        platform="all",
        content_type=last.get("tool", "PRIME"),
        meta={"source": last.get("source", "telegram_bot"), "ready_for": "ig_tg_pipeline"},
    )
    await message.answer(
        f"📌 Сохранено в контент-очередь.\n\nID: {item['id']}\nСтатус: draft\nТема: {item['topic']}",
        reply_markup=prime_queue_menu,
    )


@router.message(F.text.in_({"📌 Контент-очередь", "🕒 Посмотреть очередь"}))
async def prime_show_queue(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    items = list_prime_content(message.from_user.id, limit=10)
    if not items:
        await message.answer(
            "📌 Контент-очередь пока пустая.\n\nСгенерируй материал в PRIME PANEL и нажми «📌 Сохранить в очередь».",
            reply_markup=prime_panel_menu,
        )
        return

    lines = ["📌 <b>Контент-очередь</b>\n"]
    for item in items:
        topic = item.get("topic", "Без темы")
        if len(topic) > 80:
            topic = topic[:77] + "..."
        lines.append(
            f"ID: {item.get('id')}\n"
            f"Статус: {item.get('status')}\n"
            f"Платформа: {item.get('platform') or 'all'}\n"
            f"Публикация: {item.get('scheduled_at') or '—'}\n"
            f"Инструмент: {item.get('tool')}\n"
            f"Тема: {topic}\n"
            f"Дата: {item.get('created_at')}\n"
        )
    await message.answer("\n".join(lines), reply_markup=prime_queue_menu, parse_mode="HTML")


@router.message(F.text == "✅ Отметить готово")
async def prime_mark_ready_hint(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    await message.answer(
        "Напиши ID материала, который нужно отметить готовым, в формате:\n\nготово 3",
        reply_markup=prime_queue_menu,
    )


@router.message(F.text.regexp(r"^готово\s+\d+$"))
async def prime_mark_ready(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    item_id = int(message.text.split()[-1])
    ok = mark_prime_content(item_id, STATUS_READY)
    await message.answer("✅ Отмечено как ready." if ok else "Не нашёл материал с таким ID.", reply_markup=prime_queue_menu)


@router.message(F.text == "🗑 Удалить из очереди")
async def prime_delete_hint(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    await message.answer(
        "Напиши ID материала, который нужно удалить, в формате:\n\nудалить 3",
        reply_markup=prime_queue_menu,
    )


@router.message(F.text.regexp(r"^удалить\s+\d+$"))
async def prime_delete_item(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    item_id = int(message.text.split()[-1])
    ok = delete_prime_content(item_id)
    await message.answer("🗑 Удалено из очереди." if ok else "Не нашёл материал с таким ID.", reply_markup=prime_queue_menu)
