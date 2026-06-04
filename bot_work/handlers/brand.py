from aiogram import Router, F
from aiogram.types import Message

from database.db import can_use_feature, track_usage
from services.memory import save_brand_voice, get_brand_voice
from services.brand_voice import build_brand_prompt
from services.queue import add_to_queue
from services.ai import ask_ai


router = Router()


@router.message(F.text.startswith("/voice"))
async def set_voice(message: Message):
    tone = message.text.replace("/voice", "", 1).strip()

    if not tone:
        await message.answer(
            "Напиши стиль после команды.\n\n"
            "Пример:\n"
            "/voice Пиши агрессивно, коротко и уверенно"
        )
        return

    await save_brand_voice(message.from_user.id, tone=tone)
    await track_usage(message.from_user.id, "brand_voice_set")

    await message.answer("🧠 Brand Voice сохранён. Теперь я буду писать в этом стиле.")


@router.message(F.text.startswith("/learn"))
async def learn_style(message: Message):
    sample = message.text.replace("/learn", "", 1).strip()

    if not sample:
        await message.answer(
            "Отправь пример своего текста после команды.\n\n"
            "Пример:\n"
            "/learn Я не верю в слабый контент. Либо ты цепляешь внимание, либо тебя не существует."
        )
        return

    await save_brand_voice(message.from_user.id, sample=sample)
    await track_usage(message.from_user.id, "style_learned")

    await message.answer("✅ Я изучил стиль. Теперь могу писать ближе к твоему tone of voice.")


@router.message(F.text.startswith("/persona"))
async def set_persona(message: Message):
    persona = message.text.replace("/persona", "", 1).strip().lower()

    allowed = ["creator", "business", "luxury", "aggressive", "friendly"]

    if persona not in allowed:
        await message.answer(
            "Выбери persona:\n\n"
            "/persona creator\n"
            "/persona business\n"
            "/persona luxury\n"
            "/persona aggressive\n"
            "/persona friendly"
        )
        return

    await save_brand_voice(message.from_user.id, persona=persona)
    await track_usage(message.from_user.id, "persona_set")

    await message.answer(f"🎭 Persona сохранена: {persona}")


@router.message(F.text == "/brand")
async def show_brand(message: Message):
    memory = await get_brand_voice(message.from_user.id)

    await message.answer(
        "🧠 Твой Brand Voice:\n\n"
        f"Tone: {memory.get('tone') or 'не задан'}\n"
        f"Persona: {memory.get('persona') or 'не задана'}\n"
        f"Style sample: {memory.get('style_sample') or 'не загружен'}"
    )


@router.message(F.text.startswith("/brand_rewrite"))
async def brand_rewrite(message: Message):
    user_id = message.from_user.id
    text = message.text.replace("/brand_rewrite", "", 1).strip()

    if not text:
        await message.answer(
            "Отправь текст после команды.\n\n"
            "Пример:\n"
            "/brand_rewrite Сделай пост про AI для бизнеса"
        )
        return

    if not await can_use_feature(user_id, "brand_rewrite"):
        await message.answer(
            "Лимит на сегодня закончился.\n\n"
            "На FREE доступно 3 Brand Rewrite в день.\n"
            "Оформи PRO, чтобы пользоваться без ограничений."
        )
        return

    await message.answer("⏳ Задача добавлена в очередь...")

    async def task():
        prompt = await build_brand_prompt(
            user_id=user_id,
            task="Перепиши текст в brand voice пользователя.",
            user_text=text
        )

        result = await ask_ai(prompt)

        await message.answer(result)
        await track_usage(user_id, "brand_rewrite")

    await add_to_queue(user_id, "brand_rewrite", task)