from io import BytesIO
import random
import math

from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from database.db import can_use_feature, track_usage, register_user
from services.ai import ask_ai


router = Router()


def wrap_text(text: str, max_chars: int = 16):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + " " + word if current else word
        if len(test) <= max_chars:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines[:5]


def create_gradient_background(width: int, height: int):
    palettes = [
        ((20, 20, 35), (80, 30, 120), (255, 120, 80)),
        ((10, 25, 50), (30, 120, 180), (180, 240, 255)),
        ((25, 15, 35), (140, 60, 120), (255, 190, 120)),
        ((15, 30, 25), (40, 140, 100), (220, 255, 180)),
        ((25, 25, 30), (90, 90, 160), (255, 255, 255)),
    ]

    c1, c2, c3 = random.choice(palettes)

    img = Image.new("RGB", (width, height), c1)
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            dx = x / width
            dy = y / height

            r = int(c1[0] * (1 - dy) + c2[0] * dy)
            g = int(c1[1] * (1 - dy) + c2[1] * dy)
            b = int(c1[2] * (1 - dy) + c2[2] * dy)

            glow = math.sin(dx * math.pi) * math.sin(dy * math.pi)
            r = min(255, int(r + c3[0] * glow * 0.35))
            g = min(255, int(g + c3[1] * glow * 0.35))
            b = min(255, int(b + c3[2] * glow * 0.35))

            pixels[x, y] = (r, g, b)

    return img


def create_beautiful_poster(title: str) -> BytesIO:
    width, height = 1080, 1350

    image = create_gradient_background(width, height).convert("RGBA")
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for _ in range(18):
        x = random.randint(-150, width)
        y = random.randint(-150, height)
        size = random.randint(120, 360)
        color = random.choice([
            (255, 255, 255, 22),
            (255, 180, 120, 28),
            (120, 200, 255, 28),
            (220, 120, 255, 24),
        ])
        draw.ellipse((x, y, x + size, y + size), fill=color)

    overlay = overlay.filter(ImageFilter.GaussianBlur(18))
    image = Image.alpha_composite(image, overlay)

    glass = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glass)

    gdraw.rounded_rectangle(
        (70, 170, 1010, 1180),
        radius=55,
        fill=(0, 0, 0, 95),
        outline=(255, 255, 255, 45),
        width=2
    )

    image = Image.alpha_composite(image, glass)
    draw = ImageDraw.Draw(image)

    try:
        font_big = ImageFont.truetype("Montserrat-Bold.ttf", 78)
        font_mid = ImageFont.truetype("Montserrat-Bold.ttf", 38)
        font_small = ImageFont.truetype("Montserrat-Bold.ttf", 30)
    except Exception:
        font_big = ImageFont.load_default()
        font_mid = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((110, 230), "AI CONTENT", font=font_small, fill=(220, 220, 220, 210))
    draw.text((110, 275), "POSTER", font=font_mid, fill=(255, 255, 255, 235))

    lines = wrap_text(title.upper(), 15)

    y = 500
    for line in lines:
        draw.text((110, y), line, font=font_big, fill=(255, 255, 255, 255))
        y += 92

    draw.rounded_rectangle(
        (110, 1010, 520, 1085),
        radius=35,
        fill=(255, 255, 255, 230)
    )

    draw.text((145, 1030), "Создать пост 🚀", font=font_small, fill=(20, 20, 25, 255))
    draw.text((110, 1225), "Создано в AI SaaS Bot", font=font_small, fill=(230, 230, 230, 180))

    final = image.convert("RGB")
    buffer = BytesIO()
    final.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


@router.message(F.text == "🖼 Пост с картинкой")
async def image_post_button(message: Message):
    await message.answer(
        "🖼 Пост с картинкой\n\n"
        "Команда:\n"
        "/image_post тема\n\n"
        "Пример:\n"
        "/image_post AI для бизнеса"
    )


@router.message(F.text.startswith("/image_post"))
async def image_post(message: Message):
    user_id = message.from_user.id
    topic = message.text.replace("/image_post", "", 1).strip()

    if not topic:
        await message.answer("Пример:\n/image_post AI для бизнеса")
        return

    if not await can_use_feature(user_id, "post_image"):
        await message.answer("❌ Лимит FREE на посты с картинкой закончился. Оформи PRO.")
        return

    await register_user(user_id, message.from_user.username, message.from_user.first_name)

    await message.answer("🎨 Создаю красивый пост с картинкой...")

    post = await ask_ai(
        f"""
Напиши красивый Telegram-пост на тему: {topic}

Стиль:
живой, уверенный, дорогой, современный.

Формат:
эмодзи в начале, короткие абзацы, сильная мысль, CTA в конце.

Запрещено:
markdown, звёздочки, ###, таблицы, палочки.
"""
    )

    poster = create_beautiful_poster(topic)

    photo = BufferedInputFile(
        poster.getvalue(),
        filename="beautiful_post.png"
    )

    await message.answer_photo(
        photo=photo,
        caption=post[:1024]
    )

    if len(post) > 1024:
        await message.answer(post)

    await track_usage(user_id, "post_image")