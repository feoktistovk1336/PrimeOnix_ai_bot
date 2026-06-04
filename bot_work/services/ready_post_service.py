from services.ai import ask_ai


async def generate_ready_post(
    topic: str,
    style_block: str = "",
    profile_block: str = "",
    memory_block: str = "",
    content_goal: str = ""
):
    result = await ask_ai(f"""
{style_block}

{profile_block}

{memory_block}

Ты — premium SMM-стратег, копирайтер и арт-директор.

Создай готовый Telegram-пост с картинкой.

Тема:
{topic}

Цель:
{content_goal}

Ответ дай строго в таком формате:

POST_TEXT:
готовый пост для Telegram

IMAGE_PROMPT:
подробный промпт для генерации картинки на английском языке

Правила для POST_TEXT:
- сильный хук
- короткие абзацы
- живой стиль
- эмоция
- понятный CTA
- без markdown
- без звёздочек

Правила для IMAGE_PROMPT:
- premium advertising image
- cinematic
- realistic
- high quality
- no text
- no letters
- no logo
- no watermark
- vertical 4:5
""")

    post_text = result
    image_prompt = topic

    if "IMAGE_PROMPT:" in result:
        parts = result.split("IMAGE_PROMPT:", 1)
        post_text = parts[0].replace("POST_TEXT:", "").strip()
        image_prompt = parts[1].strip()

    return post_text, image_prompt