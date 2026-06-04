from io import BytesIO
import random
import urllib.parse

import aiohttp
from PIL import Image, ImageDraw, ImageFont


CHANNEL_WATERMARK = "@primeonix26"


STYLE_PROMPTS = {
    "luxury": "luxury premium advertising photo, cinematic light, expensive lifestyle, high-end brand campaign",
    "neon": "futuristic neon cyberpunk advertising photo, glowing lights, modern digital business, vibrant contrast",
    "dark": "dark premium cinematic advertising photo, moody atmosphere, deep shadows, luxury black aesthetic",
    "apple": "clean minimal Apple style advertising visual, soft gradients, white space, premium minimalism",
    "business": "modern business advertising photo, premium office, entrepreneurs, clean professional composition",
    "creative": "creative colorful advertising image, bold modern composition, social media campaign style",
}


async def download_file(url: str) -> BytesIO:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=120) as response:
            data = await response.read()

    buffer = BytesIO(data)
    buffer.seek(0)
    return buffer


async def generate_replicate_image(prompt: str, visual_style: str = "luxury"):
    from config import settings

    if not settings.REPLICATE_API_TOKEN:
        return None

    style_prompt = STYLE_PROMPTS.get(
        visual_style,
        STYLE_PROMPTS["luxury"]
    )

    full_prompt = (
        f"{style_prompt}. "
        f"Main topic: {prompt}. "
        "High quality realistic commercial image. "
        "Professional photography. "
        "Instagram 4:5 vertical composition. "
        "Natural proportions. "
        "No text, no letters, no logo, no watermark."
    )

    payload = {
        "version": "black-forest-labs/flux-schnell",
        "input": {
            "prompt": full_prompt,
            "aspect_ratio": "4:5",
            "output_format": "jpg",
            "output_quality": 95,
            "num_outputs": 1
        }
    }

    headers = {
        "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
        "Prefer": "wait"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.replicate.com/v1/predictions",
                json=payload,
                headers=headers,
                timeout=180
            ) as response:

                data = await response.json()

                print("REPLICATE STATUS:", response.status)
                print("REPLICATE RESPONSE:", data)

                if response.status != 200 and response.status != 201:
                    return None

                output = data.get("output")

                if isinstance(output, list) and output:
                    return await download_file(output[0])

                if isinstance(output, str):
                    return await download_file(output)

                return None

    except Exception as e:
        print("REPLICATE IMAGE ERROR FULL:")
        print(e)
        return None


def create_fallback_image(prompt: str, visual_style: str = "luxury", add_brand: bool = False) -> BytesIO:
    width, height = 1080, 1350

    colors = {
        "luxury": ((18, 18, 18), (212, 175, 55)),
        "neon": ((8, 8, 25), (0, 255, 255)),
        "dark": ((10, 10, 10), (120, 120, 120)),
        "apple": ((240, 240, 245), (120, 120, 140)),
        "business": ((25, 45, 75), (180, 220, 255)),
        "creative": ((60, 30, 90), (255, 120, 180)),
    }

    bg, accent = colors.get(visual_style, colors["luxury"])

    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)

    for _ in range(18):
        x = random.randint(-100, width)
        y = random.randint(-100, height)
        size = random.randint(120, 420)
        draw.ellipse((x, y, x + size, y + size), outline=accent, width=3)

    try:
        title_font = ImageFont.truetype("arial.ttf", 70)
        small_font = ImageFont.truetype("arial.ttf", 32)
    except Exception:
        title_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    words = prompt.upper().split()
    lines = []
    line = ""

    for word in words:
        if len(line + " " + word) < 18:
            line = f"{line} {word}".strip()
        else:
            lines.append(line)
            line = word

    if line:
        lines.append(line)

    y = 180

    for line in lines[:5]:
        draw.text((80, y), line, font=title_font, fill=(255, 255, 255))
        y += 90

    if add_brand:
        draw.text((80, 1240), CHANNEL_WATERMARK, font=small_font, fill=(220, 220, 220))

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    return buffer


def add_watermark(image_buffer: BytesIO) -> BytesIO:
    image_buffer.seek(0)

    image = Image.open(image_buffer).convert("RGB")
    image = image.resize((1080, 1350))

    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        font = ImageFont.load_default()

    text = CHANNEL_WATERMARK

    draw.rounded_rectangle(
        (760, 1260, 1050, 1320),
        radius=18,
        fill=(0, 0, 0)
    )

    draw.text((785, 1276), text, font=font, fill=(255, 255, 255))

    result = BytesIO()
    image.save(result, format="JPEG", quality=95)
    result.seek(0)
    return result


async def generate_quality_image(
    prompt: str,
    is_pro: bool = False,
    visual_style: str = "luxury",
    user_plan: str = "free"
) -> BytesIO:

    try:
        user_plan = (user_plan or "free").lower()

        should_add_watermark = (
            user_plan == "free"
            and not is_pro
        )

        # VIP / PREMIUM / PRO сначала пробуют Flux через Replicate.
        # Если на Replicate нет баланса, функция вернёт None и бот уйдёт в Pollinations.
        if user_plan in ["vip", "premium", "pro"] or is_pro:
            image = await generate_replicate_image(
                prompt=prompt,
                visual_style=visual_style
            )

            if image:
                image.seek(0)
                return image

        # FREE / START / PLUS / fallback для платных тарифов без баланса Replicate.
        image = await generate_pollinations_image(prompt)

        if should_add_watermark:
            image = add_watermark(image)

        image.seek(0)
        return image

    except Exception as e:

        print(f"IMAGE GENERATION ERROR: {e}")

        image = create_fallback_image(
            prompt=prompt,
            visual_style=visual_style,
            add_brand=(user_plan == "free" and not is_pro)
        )

        image.seek(0)
        return image


import urllib.parse


async def generate_pollinations_image(prompt: str) -> BytesIO:
    encoded = urllib.parse.quote(prompt)

    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        "?width=1080"
        "&height=1350"
        "&enhance=true"
        "&nologo=true"
        "&safe=true"
    )

    return await download_file(url)