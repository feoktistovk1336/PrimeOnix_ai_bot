from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

from config import settings


client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def ask_ai(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты сильный SMM-стратег, маркетолог и копирайтер. "
                    "Пиши живо, конкретно, без воды, без markdown и без звёздочек."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.85,
        max_tokens=3500
    )

    return response.choices[0].message.content.strip()