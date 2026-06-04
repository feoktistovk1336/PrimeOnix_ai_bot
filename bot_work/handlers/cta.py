from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.ai import ask_ai
from services.state_switcher import cancel_if_global_button
from services.memory import build_profile_block


router = Router()


class CTAState(StatesGroup):
    waiting_topic = State()


@router.message(F.text == "🚀 AI CTA")
async def cta_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CTAState.waiting_topic)

    await message.answer(
        "🚀 AI CTA\n\n"
        "Напиши продукт, услугу или тему.\n\n"
        "Пример:\n"
        "консультация по нейросетям для бизнеса"
    )


@router.message(CTAState.waiting_topic)
async def generate_cta(message: Message, state: FSMContext):
    if await cancel_if_global_button(message, state):
        return

    topic = message.text.strip()
    await state.clear()

    await message.answer("🧠 Генерирую CTA...")

    result = await ask_ai(f"""
Ты — сильный direct-response копирайтер.

Сгенерируй 30 CTA на тему:
{topic}

Раздели на блоки:

🚀 Мягкие CTA
Для тех, кто не любит агрессивные продажи.

🔥 Продающие CTA
Чтобы человек написал, купил или оставил заявку.

💬 CTA в комментарии
Чтобы получить реакции и обсуждение.

🎬 CTA для Reels
Короткие фразы в конце видео.

📌 CTA для Telegram
Для постов и каналов.

Требования:
- коротко
- живо
- современно
- без воды
- без markdown
- без звёздочек
""")

    await message.answer(result[:4000])