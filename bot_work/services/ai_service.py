"""Compatibility AI helpers.

Most of the project uses `services.ai.ask_ai`. These helpers are left for
legacy modules and tests so imports do not break.
"""

from services.ai import ask_ai


async def generate_post(prompt: str | None = None) -> str:
    prompt = prompt or "Создай короткий полезный Telegram-пост для AI-SMM бота."
    return await ask_ai(prompt)


async def generate_content_factory(prompt: str) -> str:
    return await ask_ai(prompt)
