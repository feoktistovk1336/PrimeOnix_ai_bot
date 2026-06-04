from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext


from database.db import (
    register_user,
    add_referral,
    activate_tariff,
    get_user_plan,
    has_used_trial,
    mark_trial_used,
    get_subscription_info
)
from keyboards import main_menu, admin_main_menu
from config import settings


router = Router()


@router.message(F.text.startswith("/start"))
async def start(message: Message, state: FSMContext):

    await state.clear()

    BASE_DIR = Path(__file__).resolve().parent.parent

    photo = FSInputFile(
        BASE_DIR / "media" / "welcome.png"
    )

    await message.answer_photo(
        photo=photo,
        caption=
        "👋 Добро пожаловать в PrimeOnix AI\n\n"

        "🧠 Бот адаптируется под твой стиль,\n"
        "запоминает предпочтения и помогает\n"
        "создавать контент быстрее.\n\n"

        "🎁 Новым пользователям доступен Start Premium на 5 дней.\n\n"

        "Нажми нужный раздел ниже 👇"
    )

    features_file = FSInputFile("media/primeonix_features.pdf")

    guide_file = FSInputFile("media/primeonix_user_guide.pdf")


    await message.answer_document(
        features_file,
        caption="🚀 Полный обзор возможностей PrimeOnix AI"
    )

    await message.answer_document(
        guide_file,
        caption="📘 Инструкция по настройке и работе с ботом"
    )

    user_id = message.from_user.id

    await register_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    if message.text and message.text.startswith("/start ref_"):

        try:

            inviter_id = int(
                message.text.replace("/start ref_", "").strip()
            )

            added = await add_referral(
                inviter_id=inviter_id,
                invited_id=user_id
            )

            if added:

                await activate_tariff(
                    user_id=inviter_id,
                    tariff="start_premium",
                    days=3
                )

                await message.bot.send_message(
                    inviter_id,
                    "🎁 По твоей ссылке пришёл новый пользователь!\n\n"
                    "Тебе начислено +3 дня Start Premium."
                )

        except Exception as e:
            print(f"REFERRAL ERROR: {e}")

    plan = await get_user_plan(user_id)
    trial_used = await has_used_trial(user_id)

    trial_text = ""

    if plan == "free" and not trial_used:

        await activate_tariff(
            user_id=user_id,
            tariff="start_premium",
            days=5
        )

        await mark_trial_used(user_id)

        trial_text = "🎁 Тебе открыт Start Premium на 5 дней.\n\n"

    info = await get_subscription_info(user_id)

    await message.answer(
        "🚀 Бот запущен\n\n"
        f"{trial_text}"
        f"💎 Тариф: {await get_user_plan(user_id)}\n"
        f"⏳ Осталось дней: {info['days_left']}\n\n"
        "Выбери нужный раздел:",
        reply_markup=admin_main_menu if user_id == settings.ADMIN_ID else main_menu
    )


@router.message(F.text == "⬅️ Главное меню")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Главное меню 👇",
        reply_markup=admin_main_menu if message.from_user.id == settings.ADMIN_ID else main_menu
    )
