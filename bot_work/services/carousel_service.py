from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import random
import os
import re


BRAND = "@primeonix26"
WIDTH = 1080
HEIGHT = 1350


PALETTES = {
    "luxury": {
        "bg": (14, 12, 10),
        "bg2": (70, 46, 25),
        "accent": (255, 205, 115),
        "accent2": (160, 110, 55),
        "text": (255, 255, 255),
        "muted": (230, 220, 200),
    },
    "neon": {
        "bg": (5, 7, 28),
        "bg2": (50, 20, 120),
        "accent": (0, 240, 255),
        "accent2": (255, 55, 190),
        "text": (255, 255, 255),
        "muted": (215, 235, 255),
    },
    "dark": {
        "bg": (8, 9, 12),
        "bg2": (35, 38, 50),
        "accent": (210, 210, 240),
        "accent2": (95, 110, 150),
        "text": (255, 255, 255),
        "muted": (215, 215, 225),
    },
    "apple": {
        "bg": (235, 238, 245),
        "bg2": (205, 218, 240),
        "accent": (255, 255, 255),
        "accent2": (120, 135, 160),
        "text": (18, 20, 25),
        "muted": (70, 75, 90),
    },
    "business": {
        "bg": (15, 32, 55),
        "bg2": (25, 85, 150),
        "accent": (205, 235, 255),
        "accent2": (75, 155, 230),
        "text": (255, 255, 255),
        "muted": (220, 235, 255),
    },
    "creative": {
        "bg": (35, 18, 65),
        "bg2": (190, 55, 135),
        "accent": (255, 220, 90),
        "accent2": (255, 105, 120),
        "text": (255, 255, 255),
        "muted": (255, 235, 220),
    },
}


def clean_text(text: str) -> str:
    text = text.replace("*", "").replace("#", "").replace("|", "")
    text = text.replace("—", "-").replace("–", "-")
    text = re.sub(r"[^\w\s.,!?;:()/%+\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()




def limit_text(text: str, max_chars: int = 95) -> str:
    text = clean_text(text)

    if len(text) <= max_chars:
        return text

    cut = text[:max_chars].rsplit(" ", 1)[0].strip()

    if not cut:
        cut = text[:max_chars].strip()

    return cut + "..."


def get_font(size: int, bold: bool = True):
    candidates = []

    if os.name == "nt":
        candidates += [
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/tahomabd.ttf" if bold else "C:/Windows/Fonts/tahoma.ttf",
        ]

    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "arial.ttf",
    ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass

    return ImageFont.load_default()


def gradient_background(style: str, slide_number: int):
    p = PALETTES.get(style, PALETTES["luxury"])

    image = Image.new("RGB", (WIDTH, HEIGHT), p["bg"])
    px = image.load()

    for y in range(HEIGHT):
        t = y / HEIGHT
        for x in range(WIDTH):
            s = x / WIDTH
            glow = 0.18 * (1 - abs(s - 0.5) * 2)

            r = int(p["bg"][0] * (1 - t) + p["bg2"][0] * t + p["accent"][0] * glow)
            g = int(p["bg"][1] * (1 - t) + p["bg2"][1] * t + p["accent"][1] * glow)
            b = int(p["bg"][2] * (1 - t) + p["bg2"][2] * t + p["accent"][2] * glow)

            px[x, y] = (min(255, r), min(255, g), min(255, b))

    image = image.convert("RGBA")

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)

    random.seed(777 + slide_number)

    for _ in range(10):
        x = random.randint(-250, WIDTH)
        y = random.randint(-250, HEIGHT)
        size = random.randint(250, 680)
        color = random.choice([p["accent"], p["accent2"]])
        d.ellipse(
            (x, y, x + size, y + size),
            fill=(color[0], color[1], color[2], random.randint(28, 55))
        )

    glow = glow.filter(ImageFilter.GaussianBlur(55))
    return Image.alpha_composite(image, glow)


def wrap_lines(text: str, width: int):
    return textwrap.wrap(clean_text(text), width=width)


def draw_wrapped(draw, text, x, y, font, fill, width, gap, max_lines=None):
    lines = wrap_lines(text, width)

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1].rstrip(".,;: ")
        lines[-1] = last + "..."

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += gap

    return y


def split_title_body(title: str, body: str):
    title = clean_text(title)
    body = clean_text(body)

    if title.lower().startswith("слайд"):
        title = title.split(":", 1)[-1].strip()

    title = re.sub(r"^(заголовок|title)\s*[:\-]\s*", "", title, flags=re.IGNORECASE).strip()
    body = re.sub(r"^(текст|описание|body)\s*[:\-]\s*", "", body, flags=re.IGNORECASE).strip()

    if not title:
        title = "Главная мысль"

    if not body:
        body = "Коротко и по делу: покажи аудитории понятную мысль и следующий шаг."

    title = limit_text(title, 54)
    body = limit_text(body, 135)

    return title, body


def add_brand(draw, p, light=False):
    font = get_font(28, True)
    draw.text(
        (70, 1265),
        BRAND,
        font=font,
        fill=p["muted"] if not light else (70, 75, 90, 255)
    )


def draw_badge(draw, text, x, y, p, light=False):
    font = get_font(30, True)

    fill = (255, 255, 255, 230) if not light else (20, 20, 25, 235)
    text_fill = (18, 20, 25, 255) if not light else (255, 255, 255, 255)

    draw.rounded_rectangle((x, y, x + 190, y + 62), radius=28, fill=fill)
    draw.text((x + 28, y + 16), text, font=font, fill=text_fill)


def slide_hero(title, body, number, style, show_brand: bool = True):
    p = PALETTES.get(style, PALETTES["luxury"])
    light = style == "apple"

    img = gradient_background(style, number)
    d = ImageDraw.Draw(img)

    title_font = get_font(70, True)
    body_font = get_font(38, False)

    draw_badge(d, f"{number}/5", 70, 90, p, light)

    d.rounded_rectangle(
        (70, 230, 1010, 1100),
        radius=70,
        fill=(255, 255, 255, 205) if light else (0, 0, 0, 105),
        outline=(255, 255, 255, 70),
        width=2
    )

    d.ellipse((690, 210, 1110, 630), fill=(p["accent"][0], p["accent"][1], p["accent"][2], 35))
    d.rounded_rectangle((110, 920, 970, 1040), radius=50, fill=(p["accent"][0], p["accent"][1], p["accent"][2], 210))

    y = 310
    y = draw_wrapped(
        d,
        title.upper(),
        120,
        y,
        title_font,
        p["text"] if not light else p["text"],
        15,
        88,
        max_lines=5
    )

    draw_wrapped(
        d,
        body,
        120,
        790,
        body_font,
        p["muted"] if not light else p["muted"],
        30,
        52,
        max_lines=3
    )

    if show_brand:
        add_brand(d, p, light)
    return img


def slide_pain(title, body, number, style, show_brand: bool = True):
    p = PALETTES.get(style, PALETTES["luxury"])
    light = style == "apple"

    img = gradient_background(style, number)
    d = ImageDraw.Draw(img)

    title_font = get_font(60, True)
    body_font = get_font(40, False)
    big_font = get_font(150, True)

    draw_badge(d, f"{number}/5", 70, 90, p, light)

    d.text((80, 220), "!", font=big_font, fill=(p["accent"][0], p["accent"][1], p["accent"][2], 230))

    d.rounded_rectangle(
        (190, 255, 1010, 1180),
        radius=60,
        fill=(255, 255, 255, 205) if light else (0, 0, 0, 120),
        outline=(255, 255, 255, 70),
        width=2
    )

    draw_wrapped(
        d,
        title.upper(),
        230,
        330,
        title_font,
        p["text"],
        16,
        76,
        max_lines=4
    )

    d.line((230, 680, 930, 680), fill=(p["accent"][0], p["accent"][1], p["accent"][2], 210), width=5)

    draw_wrapped(
        d,
        body,
        230,
        740,
        body_font,
        p["muted"] if not light else p["muted"],
        27,
        58,
        max_lines=5
    )

    if show_brand:
        add_brand(d, p, light)
    return img


def slide_stats(title, body, number, style, show_brand: bool = True):
    p = PALETTES.get(style, PALETTES["luxury"])
    light = style == "apple"

    img = gradient_background(style, number)
    d = ImageDraw.Draw(img)

    title_font = get_font(58, True)
    body_font = get_font(36, False)
    num_font = get_font(84, True)

    draw_badge(d, f"{number}/5", 70, 90, p, light)

    boxes = [
        (90, 250, 490, 560),
        (590, 250, 990, 560),
        (90, 660, 990, 1080),
    ]

    for idx, box in enumerate(boxes, start=1):
        d.rounded_rectangle(
            box,
            radius=50,
            fill=(255, 255, 255, 205) if light else (0, 0, 0, 105),
            outline=(255, 255, 255, 60),
            width=2
        )

        d.text(
            (box[0] + 40, box[1] + 35),
            f"0{idx}",
            font=num_font,
            fill=(p["accent"][0], p["accent"][1], p["accent"][2], 255)
        )

    draw_wrapped(d, title.upper(), 130, 430, title_font, p["text"], 10, 68, max_lines=2)
    draw_wrapped(d, "Ключевая мысль", 630, 430, body_font, p["muted"], 16, 48, max_lines=2)
    draw_wrapped(d, body, 135, 780, body_font, p["muted"], 35, 52, max_lines=5)

    if show_brand:
        add_brand(d, p, light)
    return img


def slide_solution(title, body, number, style, show_brand: bool = True):
    p = PALETTES.get(style, PALETTES["luxury"])
    light = style == "apple"

    img = gradient_background(style, number)
    d = ImageDraw.Draw(img)

    title_font = get_font(58, True)
    body_font = get_font(38, False)

    draw_badge(d, f"{number}/5", 70, 90, p, light)

    d.rounded_rectangle(
        (70, 240, 1010, 520),
        radius=55,
        fill=(p["accent"][0], p["accent"][1], p["accent"][2], 225)
    )

    draw_wrapped(
        d,
        title.upper(),
        120,
        300,
        title_font,
        (18, 20, 25, 255),
        17,
        74,
        max_lines=3
    )

    d.rounded_rectangle(
        (70, 610, 1010, 1130),
        radius=60,
        fill=(255, 255, 255, 205) if light else (0, 0, 0, 115),
        outline=(255, 255, 255, 70),
        width=2
    )

    draw_wrapped(
        d,
        body,
        125,
        690,
        body_font,
        p["text"] if light else p["muted"],
        30,
        58,
        max_lines=6
    )

    if show_brand:
        add_brand(d, p, light)
    return img


def slide_cta(title, body, number, style, show_brand: bool = True):
    p = PALETTES.get(style, PALETTES["luxury"])
    light = style == "apple"

    img = gradient_background(style, number)
    d = ImageDraw.Draw(img)

    title_font = get_font(64, True)
    body_font = get_font(40, False)
    cta_font = get_font(46, True)

    draw_badge(d, f"{number}/5", 70, 90, p, light)

    d.rounded_rectangle(
        (70, 210, 1010, 1160),
        radius=80,
        fill=(255, 255, 255, 210) if light else (0, 0, 0, 120),
        outline=(255, 255, 255, 70),
        width=2
    )

    draw_wrapped(
        d,
        title.upper(),
        120,
        310,
        title_font,
        p["text"],
        15,
        84,
        max_lines=4
    )

    draw_wrapped(
        d,
        body,
        120,
        720,
        body_font,
        p["muted"],
        28,
        58,
        max_lines=4
    )

    d.rounded_rectangle(
        (120, 990, 960, 1090),
        radius=45,
        fill=(p["accent"][0], p["accent"][1], p["accent"][2], 235)
    )

    d.text((170, 1018), "СОХРАНИ И ПРИМЕНИ", font=cta_font, fill=(18, 20, 25, 255))

    if show_brand:
        add_brand(d, p, light)
    return img


def parse_carousel_text(text: str):
    raw_text = text.strip()

    slide_pattern = r"Слайд\s*(\d+)\s*[:\-]\s*(.*?)(?=Слайд\s*\d+\s*[:\-]|$)"
    matches = re.findall(slide_pattern, raw_text, flags=re.IGNORECASE | re.DOTALL)

    slides = []

    for number, content in matches:
        content = content.strip()

        title_match = re.search(
            r"Заголовок\s*[:\-]\s*(.*?)(?=\n\s*(?:Текст|Описание)\s*[:\-]|$)",
            content,
            flags=re.IGNORECASE | re.DOTALL
        )
        body_match = re.search(
            r"(?:Текст|Описание)\s*[:\-]\s*(.*)$",
            content,
            flags=re.IGNORECASE | re.DOTALL
        )

        if title_match:
            title = title_match.group(1).strip()
            body = body_match.group(1).strip() if body_match else ""
        else:
            content = clean_text(content)

            if "." in content:
                title, body = content.split(".", 1)
            else:
                parts = content.split(" ", 7)
                title = " ".join(parts[:5])
                body = " ".join(parts[5:]) if len(parts) > 5 else content

        title, body = split_title_body(title, body)
        slides.append((title, body))

    if len(slides) < 5:
        slides = [
            ("Хватит делать вслепую", "Тема должна попадать в боль аудитории и вести к действию."),
            ("Главная ошибка", "Люди пишут о себе, а аудитория хочет увидеть свою проблему."),
            ("Что работает", "Хук, конкретная боль, простой пример и сильный следующий шаг."),
            ("Как применить", "Возьми одну проблему клиента и покажи понятное решение."),
            ("Действуй", "Сохрани эту структуру и используй для следующего поста."),
        ]

    return slides[:5]

def create_slide(title: str, body: str, number: int, style: str = "luxury", show_brand: bool = True) -> BytesIO:
    title, body = split_title_body(title, body)

    layouts = [
        slide_hero,
        slide_pain,
        slide_stats,
        slide_solution,
        slide_cta
    ]

    image = layouts[(number - 1) % len(layouts)](title, body, number, style, show_brand=show_brand)

    out = BytesIO()
    image.convert("RGB").save(out, format="JPEG", quality=95)
    out.seek(0)
    return out


def create_carousel_images(carousel_text: str, style: str = "luxury", show_brand: bool = True):
    slides = parse_carousel_text(carousel_text)

    return [
        create_slide(title, body, i, style, show_brand=show_brand)
        for i, (title, body) in enumerate(slides, start=1)
    ]