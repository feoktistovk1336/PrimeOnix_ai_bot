from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database.db import save_user_memory_profile

from database.db import (
    register_user,
    save_user_profile_field,
    save_user_style
)

from keyboards import profile_menu


router = Router()


class SetupState(StatesGroup):
    niche = State()
    audience = State()
    offer = State()
    cta = State()
    style = State()


@router.message(F.text == "⚙️ Быстрая настройка")
async def setup_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(SetupState.niche)

    await message.answer(
        "⚙️ Быстрая настройка AI-профиля\n\n"
        "Ответь на 5 вопросов, и бот начнёт писать под тебя.\n\n"
        "1/5\n"
        "Какая у тебя ниша?\n\n"
        "Пример:\n"
        "премиум детейлинг авто в Москве"
    )


@router.message(SetupState.niche)
async def setup_niche(message: Message, state: FSMContext):
    await state.update_data(niche=message.text)
    await state.set_state(SetupState.audience)

    await message.answer(
        "2/5\n"
        "Кто твоя аудитория?\n\n"
        "Пример:\n"
        "владельцы дорогих авто, предприниматели, мужчины 25-45"
    )


@router.message(SetupState.audience)
async def setup_audience(message: Message, state: FSMContext):
    await state.update_data(audience=message.text)
    await state.set_state(SetupState.offer)

    await message.answer(
        "3/5\n"
        "Какой у тебя главный оффер?\n\n"
        "Пример:\n"
        "комплексная защита кузова с гарантией результата"
    )


@router.message(SetupState.offer)
async def setup_offer(message: Message, state: FSMContext):
    await state.update_data(offer=message.text)
    await state.set_state(SetupState.cta)

    await message.answer(
        "4/5\n"
        "Какой CTA использовать?\n\n"
        "Пример:\n"
        "Напиши в личку слово ДЕТЕЙЛИНГ"
    )


@router.message(SetupState.cta)
async def setup_cta(message: Message, state: FSMContext):
    await state.update_data(cta=message.text)
    await state.set_state(SetupState.style)

    await message.answer(
        "5/5\n"
        "Какой стиль текста нужен?\n\n"
        "Пример:\n"
        "коротко, дорого, уверенно, без воды, с лёгкой дерзостью"
    )


@router.message(SetupState.style)
async def setup_style(message: Message, state: FSMContext):
    user_id = message.from_user.id

    data = await state.get_data()

    await register_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    await save_user_profile_field(user_id, "niche", data["niche"])
    await save_user_profile_field(user_id, "audience", data["audience"])
    await save_user_profile_field(user_id, "offer", data["offer"])
    await save_user_profile_field(user_id, "cta", data["cta"])
    await save_user_style(user_id, message.text)

    await save_user_memory_profile(
    user_id=user_id,
    niche=data["niche"],
    audience=data["audience"],
    offer=data["offer"],
    cta=data["cta"],
    tone=message.text,
    product=data["offer"]
    )
    
    await state.clear()

    await message.answer(
        "✅ AI-профиль настроен\n\n"
        "Теперь бот будет учитывать:\n"
        "🏢 нишу\n"
        "🎯 аудиторию\n"
        "💎 оффер\n"
        "📢 CTA\n"
        "🎭 стиль текста\n\n"
        "Можешь сразу идти в «📦 Создать» и делать пост.",
        reply_markup=profile_menu
    )