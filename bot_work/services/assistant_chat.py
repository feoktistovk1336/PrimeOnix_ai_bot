from __future__ import annotations

from openai import AsyncOpenAI
from config import settings


def _client_and_model() -> tuple[AsyncOpenAI | None, str | None]:
    # AI Chat is intentionally routed through Groq first, so normal dialog does not burn OpenRouter balance.
    if getattr(settings, "GROQ_API_KEY", None):
        return AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        ), "llama-3.3-70b-versatile"
    if getattr(settings, "OPENROUTER_API_KEY", None):
        return AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://primeonix.ai",
                "X-Title": "PrimeOnix AI Bot",
            },
        ), "openrouter/auto"
    if getattr(settings, "OPENAI_API_KEY", None):
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), "gpt-4o-mini"
    return None, None


async def ask_primeonix_assistant(question: str, profile_block: str = "", style_block: str = "", mode: str = "общий помощник") -> str:
    client, model = _client_and_model()
    if not client or not model:
        return (
            "⚠️ AI-чат пока не подключён.\n\n"
            "Добавь в Railway переменную GROQ_API_KEY, "
            "и AI-чат будет отвечать через Groq без лишних расходов OpenRouter."
        )

    system = (
        "Ты PrimeOnix AI — AI-консультант внутри Telegram-бота. "
        f"Текущий режим: {mode}. "
        "Отвечай по-русски, понятно, практично, без воды. "
        "Главная задача AI-чата — консультировать: объяснять как сделать, подсказывать шаги, разбирать ошибки, "
        "давать советы по Telegram, Instagram, n8n, SMM, воронкам, бизнесу и нейросетям. "
        "НЕ генерируй полноценные посты, карусели, Reels-сценарии или картинки в AI-чате. "
        "Если пользователь просит сгенерировать контент, объясни, какую кнопку нажать: 🚀 Создать или 📣 Контент Центр. "
        "AI-чат должен экономить бюджет и работать через Groq, без расхода OpenRouter на обычное общение."
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
