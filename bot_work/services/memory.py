import aiosqlite
from datetime import datetime

DB_PATH = "bot.db"


async def init_memory_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            user_id INTEGER PRIMARY KEY,
            tone TEXT,
            persona TEXT,
            style_sample TEXT,
            updated_at TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS usage_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            feature TEXT,
            created_at TEXT
        )
        """)

        await db.commit()


async def save_brand_voice(user_id: int, tone: str | None = None, persona: str | None = None, sample: str | None = None):
    current = await get_brand_voice(user_id)

    new_tone = tone or current.get("tone")
    new_persona = persona or current.get("persona")
    new_sample = sample or current.get("style_sample")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR REPLACE INTO user_memory 
        (user_id, tone, persona, style_sample, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            new_tone,
            new_persona,
            new_sample,
            datetime.utcnow().isoformat()
        ))

        await db.commit()


async def get_brand_voice(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        SELECT tone, persona, style_sample FROM user_memory WHERE user_id = ?
        """, (user_id,))
        row = await cursor.fetchone()

    if not row:
        return {
            "tone": None,
            "persona": None,
            "style_sample": None
        }

    return {
        "tone": row[0],
        "persona": row[1],
        "style_sample": row[2]
    }


async def track_usage(user_id: int, feature: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO usage_tracking (user_id, feature, created_at)
        VALUES (?, ?, ?)
        """, (user_id, feature, datetime.utcnow().isoformat()))

        await db.commit()


from database.db import get_user_style


async def build_profile_block(user_id: int):

    style = await get_user_style(user_id)

    if not style:
        return ""

    return f"""
Brand Brain автора:

{style}
"""


from database.db import get_user_memory_profile


async def build_memory_profile_block(user_id: int):
    profile = await get_user_memory_profile(user_id)

    if not profile:
        return ""

    return f"""
AI Memory Profile:

Ниша:
{profile.get("niche")}

Аудитория:
{profile.get("audience")}

Оффер:
{profile.get("offer")}

Tone of voice:
{profile.get("tone")}

CTA:
{profile.get("cta")}

Продукт:
{profile.get("product")}
"""