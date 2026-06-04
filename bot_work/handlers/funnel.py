from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.ai import ask_ai
from services.prompt_engine import build_funnel_prompt
from services.state_switcher import cancel_if_global_button
from services.memory import build_profile_block


router = Router()


class FunnelState(StatesGroup):
    waiting_topic = State()


@router.message(F.text == "🎯 Воронка продаж")
async def funnel_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(FunnelState.waiting_topic)

    await message.answer(
        "🎯 Воронка продаж\n\n"
        "Напиши продукт, нишу или услугу.\n\n"
        "Пример:\n"
        "онлайн-курс по нейросетям для предпринимателей"
    )


@router.message(FunnelState.waiting_topic)
async def generate_funnel(message: Message, state: FSMContext):
    if await cancel_if_global_button(message, state):
        return

    topic = message.text.strip()
    await state.clear()

    if len(topic) < 5:
        await message.answer("❌ Напиши тему подробнее.")
        return

    await message.answer("🧠 Собираю сильную продающую воронку...")

    profile_block = await build_profile_block(message.from_user.id)

    result = await ask_ai(
        build_funnel_prompt(
            topic=topic,
            profile_block=profile_block
        )
    )