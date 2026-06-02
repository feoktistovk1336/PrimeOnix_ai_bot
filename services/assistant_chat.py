from __future__ import annotations

from openai import AsyncOpenAI
from config import settings


def _client_and_model() -> tuple[AsyncOpenAI | None, str | None]:
    if getattr(settings, "OPENROUTER_API_KEY", None):
        return AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://primeonix.ai",
                "X-Title": "PrimeOnix AI Bot",
            },
        ), "openrouter/auto"
    if getattr(settings, "GROQ_API_KEY", None):
        return AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        ), "llama-3.3-70b-versatile"
    if getattr(settings, "OPENAI_API_KEY", None):
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), "gpt-4o-mini"
    return None, None


async def ask_primeonix_assistant(question: str, profile_block: str = "", style_block: str = "") -> str:
    client, model = _client_and_model()
    if not client or not model:
        return (
            "⚠️ AI-чат пока не подключён.\n\n"
            "Добавь в Railway переменную OPENROUTER_API_KEY или GROQ_API_KEY, "
            "и я смогу отвечать на вопросы прямо в боте."
        )

    system = (
        "Ты PrimeOnix AI — личный AI-помощник Кирилла по контенту, Telegram-ботам, n8n, "
        "нейросетям, SMM, воронкам и автоматизации. Отвечай по-русски, понятно, практично, "
        "без воды. Если вопрос про проект PrimeOnix — давай конкретные шаги. "
        "Обычный контент не должен содержать лид-магнитных CTA, если пользователь не просит воронку."
    )
    context = f"{profile_block}\n\n{style_block}".strip()
    user = f"Контекст пользователя:\n{context or 'профиль не заполнен'}\n\nВопрос:\n{question}"

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.55,
        max_tokens=2200,
    )
    return (response.choices[0].message.content or "").strip()
