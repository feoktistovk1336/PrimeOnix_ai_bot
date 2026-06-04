from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.ai import ask_ai
from services.state_switcher import cancel_if_global_button


router = Router()


class HooksState(StatesGroup):
    waiting_topic = State()


@router.message(F.text == "🎯 Viral Hooks")
async def hooks_start(message: Message, state: FSMContext):

    await state.clear()

    await state.set_state(HooksState.waiting_topic)

    await message.answer(
        "🎯 Генератор Viral Hooks\n\n"
        "Напиши тему или нишу.\n\n"
        "Например:\n"
        "• заработок\n"
        "• AI\n"
        "• крипта\n"
        "• фитнес\n"
        "• бизнес"
    )


@router.message(HooksState.waiting_topic)
async def generate_hooks(message: Message, state: FSMContext):

    if await cancel_if_global_button(message, state):
        return

    topic = message.text.strip()

    await state.clear()

    await message.answer(
        "🧠 Генерирую hooks..."
    )

    result = await ask_ai(f"""
Ты — топовый viral copywriter.

Придумай 20 мощных viral hooks на тему:

{topic}

Требования:
- цепляют внимание
- вызывают эмоции
- хочется дочитать
- современный стиль
- как у топовых блогеров
- короткие
- без воды

Добавь:
- hooks для reels
- hooks для Telegram
- hooks для продаж

Без markdown.
""")

    await message.answer(
        f"🎯 Viral Hooks\n\n{result[:4000]}"
    )