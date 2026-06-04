import re
from services.ai import ask_ai


async def generate_week_content(topic: str):
    result = await ask_ai(f"""
Ты — premium SMM-стратег и копирайтер.

Создай 7 готовых Telegram-постов на неделю.

Тема:
{topic}

Формат строго:

ДЕНЬ 1
Время: 10:00
Пост:
готовый красивый пост
Картинка:
prompt на английском для генерации картинки без текста

ДЕНЬ 2
Время: 12:00
Пост:
готовый красивый пост
Картинка:
prompt на английском для генерации картинки без текста

И так до ДЕНЬ 7.

Требования к постам:
- сильный хук
- эмодзи
- короткие абзацы
- разбивка блоками
- живой стиль
- экспертность
- CTA в конце
- без markdown
- без звёздочек
- без таблиц

Требования к картинке:
- English prompt
- premium advertising image
- cinematic
- realistic
- vertical 4:5
- no text
- no letters
- no logo
- no watermark
""")

    return result


def parse_week_posts(text: str):
    posts = []

    pattern = (
        r"ДЕНЬ\s*(\d+).*?"
        r"Время:\s*(\d{1,2}:\d{2}).*?"
        r"Пост:\s*(.*?)"
        r"Картинка:\s*(.*?)"
        r"(?=ДЕНЬ\s*\d+|$)"
    )

    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)

    for day, time, post, image_prompt in matches:
        posts.append({
            "day": int(day),
            "time": time.strip(),
            "text": post.strip(),
            "image_prompt": image_prompt.strip()
        })

    return posts


def parse_times(text: str):
    times = []

    for part in text.replace(";", ",").split(","):
        part = part.strip()

        if ":" not in part:
            continue

        hour, minute = part.split(":", 1)

        if hour.isdigit() and minute.isdigit():
            hour = int(hour)
            minute = int(minute)

            if 0 <= hour <= 23 and 0 <= minute <= 59:
                times.append(f"{hour:02d}:{minute:02d}")

    return times