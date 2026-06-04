from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.ai import ask_ai
from services.analyze_engine import build_analyze_prompt
from services.sender import send_long
from services.state_switcher import cancel_if_global_button


router = Router()


class AnalyzeState(StatesGroup):
    waiting_post = State()


@router.message(F.text == "🔎 Анализ поста")
async def analyze_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AnalyzeState.waiting_post)

    await message.answer(
        "🔎 Анализ поста\n\n"
        "Отправь текст поста, а я:\n"
        "• оценю хук\n"
        "• найду слабые места\n"
        "• усилю CTA\n"
        "• перепишу пост сильнее\n"
        "• дам оценку от 1 до 10"
    )


@router.message(AnalyzeState.waiting_post)
async def analyze_post(message: Message, state: FSMContext):
    if await cancel_if_global_button(message, state):
        return

    post_text = message.text.strip()

    if len(post_text) < 20:
        await message.answer("❌ Пост слишком короткий. Отправь нормальный текст.")
        return

    await state.clear()

    await message.answer("🧠 Анализирую пост...")

    result = await ask_ai(
        build_analyze_prompt(post_text)
    )

    await send_long(message, result)
    