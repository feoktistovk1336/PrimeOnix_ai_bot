from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.ai import ask_ai
from services.prompt_engine import build_series_prompt
from services.sender import send_long
from services.state_switcher import cancel_if_global_button
from services.memory import build_profile_block


router = Router()


class SeriesState(StatesGroup):
    waiting_topic = State()


@router.message(F.text == "📅 Серия постов")
async def series_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(SeriesState.waiting_topic)

    await message.answer(
        "📅 Серия постов\n\n"
        "Напиши тему, продукт или нишу.\n\n"
        "Пример:\n"
        "прогрев на онлайн-курс по нейросетям"
    )


@router.message(SeriesState.waiting_topic)
async def generate_series(message: Message, state: FSMContext):
    if await cancel_if_global_button(message, state):
        return

    topic = message.text.strip()
    await state.clear()

    await message.answer("🧠 Создаю серию постов...")

    profile_block = await build_profile_block(message.from_user.id)

    result = await ask_ai(
        build_series_prompt(
            topic=topic,
            profile_block=profile_block
        )
    )

    if len(result) <= 4000:
        from services.sender import send_long

        await send_long(message, result)
        return

    for i in range(0, len(result), 3900):
        await send_long(message, result)    