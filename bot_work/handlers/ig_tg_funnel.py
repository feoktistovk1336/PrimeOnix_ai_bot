from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database.db import register_user, get_user_memory, get_user_plan
from services.ai import ask_ai
from services.queue import add_to_queue
from services.memory import build_memory_profile_block
from services.sender import send_long
from services.prompt_engine import build_ig_tg_funnel_prompt
from services.n8n_client import call_n8n, n8n_config_status
from handlers.prime_viral import LAST_PRIME_RESULT
from handlers.content import build_style_block, build_profile_block, is_priority_plan
from handlers.admin import is_admin
from keyboards import ig_tg_funnel_menu, prime_after_generation_menu, publish_plan_menu


router = Router()


class IgTgFunnelState(StatesGroup):
    waiting_type = State()
    waiting_topic = State()


FUNNEL_TYPES = {
    "🎬 Reels → Telegram": "reels",
    "🎠 Карусель → Telegram": "carousel",
    "🎁 Лид-магнит → Telegram": "lead_magnet",
}


IG_TG_INTRO_TEXT = (
    "🔗 <b>IG → TG Funnel</b>\n\n"
    "Инструмент создаёт одну связанную цепочку:\n"
    "Instagram цепляет → человек пишет кодовое слово → получает переход → "
    "в Telegram видит продолжение той же темы.\n\n"
    "На выходе ты получишь:\n"
    "• идею связки\n"
    "• hook для Instagram\n"
    "• сценарий Reels или структуру карусели\n"
    "• caption\n"
    "• кодовое слово для Direct\n"
    "• готовый DM-ответ\n"
    "• Telegram-пост\n"
    "• лид-магнит\n"
    "• чек-лист публикации\n\n"
    "Выбери формат входа из Instagram 👇"
)


TOPIC_HELP_TEXT = (
    "Теперь напиши тему связки 👇\n\n"
    "Лучше писать не одним словом, а как идею для трафика.\n\n"
    "Примеры:\n"
    "• 10 бесплатных нейронок для создания Reels и каруселей\n"
    "• промпт, который превращает идею в продающую карусель\n"
    "• как за 15 минут собрать контент-план через AI\n"
    "• как делать тату-эскизы из фото через нейросети"
)


@router.message(F.text == "🔗 IG→TG Воронка")
async def open_ig_tg_funnel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.clear()
    await state.set_state(IgTgFunnelState.waiting_type)
    await message.answer(IG_TG_INTRO_TEXT, reply_markup=ig_tg_funnel_menu, parse_mode="HTML")


@router.message(IgTgFunnelState.waiting_type)
async def choose_ig_tg_type(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    if message.text in {"⬅️ Назад в PRIME PANEL", "⬅️ Назад в публикации"}:
        await state.clear()
        await message.answer("📅 <b>План и публикации</b>\n\nВыбери раздел ниже 👇", reply_markup=publish_plan_menu, parse_mode="HTML")
        return

    if message.text not in FUNNEL_TYPES:
        await message.answer("Выбери формат кнопкой ниже 👇", reply_markup=ig_tg_funnel_menu)
        return

    await state.update_data(funnel_type=FUNNEL_TYPES[message.text], funnel_title=message.text)
    await state.set_state(IgTgFunnelState.waiting_topic)
    await message.answer(TOPIC_HELP_TEXT)


@router.message(IgTgFunnelState.waiting_topic)
async def generate_ig_tg_funnel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    if message.text in {"⬅️ Назад в PRIME PANEL", "⬅️ Назад в публикации"}:
        await state.clear()
        await message.answer("📅 <b>План и публикации</b>\n\nВыбери раздел ниже 👇", reply_markup=publish_plan_menu, parse_mode="HTML")
        return

    topic = (message.text or "").strip()
    if len(topic) < 8:
        await message.answer(
            "Напиши тему чуть подробнее, чтобы связка получилась сильнее.\n\n"
            "Например: 10 бесплатных нейронок для создания Reels и каруселей"
        )
        return

    user_id = message.from_user.id
    data = await state.get_data()
    funnel_type = data.get("funnel_type", "reels")
    funnel_title = data.get("funnel_title", "IG→TG")

    await state.clear()

    await register_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    style_block = await build_style_block(user_id)
    profile_block = await build_profile_block(user_id)
    memory = await get_user_memory(user_id)
    memory_profile_block = await build_memory_profile_block(user_id)

    memory_block = f"""
Предпочтения пользователя:

Любимые темы:
{memory.get('favorite_topics')}

Любимый стиль:
{memory.get('favorite_style')}

Любимый CTA:
{memory.get('preferred_cta')}

Tone of voice:
{memory.get('preferred_tone')}
"""

    async def generate_task():
        await message.answer(
            "🔗 Собираю IG → TG воронку...\n\n"
            "Главная логика остаётся такой:\n"
            "Telegram-бот = пульт управления\n"
            "n8n = движок автоматизации\n"
            "Instagram + Telegram = единая связка темы.\n\n"
            "Сейчас подготовлю:\n"
            "• Instagram hook\n"
            "• сценарий / карусель\n"
            "• кодовое слово\n"
            "• DM-ответ\n"
            "• Telegram-пост\n"
            "• лид-магнит\n"
            "• чек-лист публикации"
        )

        prompt = build_ig_tg_funnel_prompt(
            topic=topic,
            funnel_type=funnel_type,
            style_block=style_block,
            profile_block=profile_block,
            memory_block=memory_block + memory_profile_block,
            content_goal="перевести трафик из Instagram в Telegram, удержать человека и прогреть к следующему шагу"
        )

        result_source = "local_ai"
        result = None
        n8n_ok, _, _ = n8n_config_status()

        if n8n_ok:
            await message.answer("⚙️ Отправляю задачу в n8n workflow...")
            n8n_response = await call_n8n({
                "action": "generate_ig_tg_funnel",
                "source": "telegram_bot",
                "telegram_user_id": user_id,
                "username": message.from_user.username,
                "funnel_type": funnel_type,
                "funnel_title": funnel_title,
                "topic": topic,
                "prompt": prompt,
                "expected_response": {
                    "text": "Полная IG→TG воронка текстом",
                    "format": "json"
                }
            })

            if n8n_response.get("ok") and n8n_response.get("text"):
                result = n8n_response["text"]
                result_source = "n8n"
            elif n8n_response.get("ok"):
                await message.answer(
                    "⚠️ n8n принял задачу, но не вернул готовый текст.\n"
                    "Сейчас сгенерирую воронку внутри Telegram-бота, чтобы ты не ждал.\n\n"
                    "Позже в n8n нужно добавить финальный узел Respond to Webhook, который возвращает поле text."
                )
            else:
                await message.answer(
                    "⚠️ n8n webhook пока не ответил как надо.\n"
                    f"Ошибка: {n8n_response.get('error')}\n"
                    "Сейчас сделаю генерацию внутри Telegram-бота."
                )

        if not result:
            result = await ask_ai(prompt)

        full_result = f"🔗 <b>{funnel_title}</b>\n\nИсточник: {'n8n workflow' if result_source == 'n8n' else 'Telegram bot AI'}\nТема: {topic}\n\n{result}"

        LAST_PRIME_RESULT[user_id] = {
            "tool": funnel_title,
            "topic": topic,
            "content": full_result,
            "source": result_source,
        }

        await send_long(message, full_result)
        await message.answer(
            "✅ <b>Воронка готова.</b>\n\n"
            "Теперь управляй материалом кнопками ниже 👇\n\n"
            "🔁 Улучшить — переписать сильнее\n"
            "🔥 Усилить хук — сделать первый экран мощнее\n"
            "🧲 Усилить CTA — усилить переход в Direct/TG\n"
            "🔗 TG-продолжение — сделать пост-продолжение\n"
            "📌 Сохранить в очередь — положить в контент-очередь\n"
            "📤 Подготовить к публикации — собрать caption/DM/TG/checklist\n"
            "🚀 Отправить в n8n — отправить готовый материал в workflow",
            reply_markup=prime_after_generation_menu,
            parse_mode="HTML",
        )

    plan = await get_user_plan(user_id)
    queue_position = await add_to_queue(
        user_id=user_id,
        task_name="ig_tg_funnel_generation",
        task_func=generate_task,
        is_pro=is_priority_plan(plan)
    )

    await message.answer(
        "🔗 IG → TG воронка добавлена в очередь\n\n"
        f"Позиция: {queue_position}"
    )
