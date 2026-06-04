from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.ai import ask_ai
from services.state_switcher import cancel_if_global_button
from services.memory import build_profile_block
from services.prompt_engine import (
    build_lead_magnet_prompt
)


router = Router()


class LeadMagnetState(StatesGroup):
    waiting_topic = State()


@router.message(F.text == "🎁 Лид-магнит")
async def lead_magnet_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(LeadMagnetState.waiting_topic)

    await message.answer(
        "🎁 Лид-магнит\n\n"
        "Напиши нишу, продукт или тему.\n\n"
        "Пример:\n"
        "чеклист для предпринимателей по внедрению AI"
    )


@router.message(LeadMagnetState.waiting_topic)
async def generate_lead_magnet(message: Message, state: FSMContext):
    if await cancel_if_global_button(message, state):
        return

    topic = message.text.strip()
    await state.clear()

    await message.answer("🧠 Создаю лид-магнит...")

    profile_block = await build_profile_block(message.from_user.id)

    result = await ask_ai(
        build_lead_magnet_prompt(
            topic=topic,
            profile_block=profile_block
        )
    )

    if len(result) <= 4000:
        from services.sender import send_long

        await send_long(message, result)
    else:
        for i in range(0, len(result), 3900):
            await message.answer(result[i:i + 3900])