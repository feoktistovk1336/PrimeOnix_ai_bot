import aiosqlite
from datetime import datetime, timedelta


DB_PATH = "data.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            plan TEXT DEFAULT 'free',
            pro_until TEXT,
            trial_used TEXT DEFAULT 'no',
            created_at TEXT
        )
        """)

        try:
            await db.execute("ALTER TABLE users ADD COLUMN trial_used TEXT DEFAULT 'no'")
        except Exception:
            pass

        for column_def in [
            "blocked INTEGER DEFAULT 0",
            "bonus_generations INTEGER DEFAULT 0",
            "last_active_at TEXT"
        ]:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {column_def}")
            except Exception:
                pass

        await db.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            event TEXT,
            details TEXT,
            created_at TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS style_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sample_text TEXT,
            analysis TEXT,
            created_at TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            feature TEXT,
            created_at TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_styles (
            user_id INTEGER PRIMARY KEY,
            style_text TEXT,
            updated_at TEXT
        )
        """)


        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            niche TEXT,
            audience TEXT,
            offer TEXT,
            city TEXT,
            cta TEXT,
            updated_at TEXT
        )
        """)

        for column_def in [
            "visual_style TEXT",
            "visual_style_title TEXT",
            "content_goal TEXT",
            "content_goal_title TEXT",
        ]:
            try:
                await db.execute(f"ALTER TABLE user_profiles ADD COLUMN {column_def}")
            except Exception:
                pass

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_memory_profiles (
            user_id INTEGER PRIMARY KEY,
            niche TEXT,
            audience TEXT,
            offer TEXT,
            tone TEXT,
            cta TEXT,
            product TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            user_id INTEGER PRIMARY KEY,
            favorite_topics TEXT,
            favorite_style TEXT,
            preferred_cta TEXT,
            preferred_tone TEXT,
            updated_at TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            image_path TEXT,
            publish_at TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at TEXT
        )
        """)

        try:
            await db.execute("ALTER TABLE scheduled_posts ADD COLUMN image_path TEXT")
        except Exception:
            pass

        defaults = {
            "limit_rewrite": "5",
            "limit_content_factory": "3",
            "limit_brand_rewrite": "3",
            "limit_post_image": "3",
            "limit_content_pack": "2"
        }

        for key, value in defaults.items():
            await db.execute("""
            INSERT OR IGNORE INTO app_settings (key, value)
            VALUES (?, ?)
            """, (key, value))

        await db.commit()


async def init_autopost_db():
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            image_path TEXT,
            publish_at TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at TEXT
        )
        """)

        try:
            await db.execute("ALTER TABLE scheduled_posts ADD COLUMN image_path TEXT")
        except Exception:
            pass

        await db.commit()


async def register_user(user_id: int, username=None, first_name=None):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        INSERT OR IGNORE INTO users (
            user_id,
            username,
            first_name,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """, (
            user_id,
            username,
            first_name,
            datetime.utcnow().isoformat()
        ))

        await db.commit()


async def get_user_plan(user_id: int):
    from config import settings

    if settings.ADMIN_ID and user_id == settings.ADMIN_ID:
        return "pro"

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        SELECT plan, pro_until
        FROM users
        WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    if not row:
        return "free"

    plan, pro_until = row

    if not plan:
        return "free"

    if plan == "free":
        return "free"

    if pro_until:
        try:
            end_date = datetime.fromisoformat(pro_until)

            if end_date > datetime.utcnow():
                return plan
            else:
                return "free"

        except Exception:
            return "free"

    return "free"


async def activate_pro(user_id: int, days: int = 30):
    await register_user(user_id)

    pro_until = datetime.utcnow() + timedelta(days=days)

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        UPDATE users
        SET plan = 'pro',
            pro_until = ?
        WHERE user_id = ?
        """, (
            pro_until.isoformat(),
            user_id
        ))

        await db.commit()


async def track_usage(user_id: int, feature: str):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        INSERT INTO usage (
            user_id,
            feature,
            created_at
        )
        VALUES (?, ?, ?)
        """, (
            user_id,
            feature,
            datetime.utcnow().isoformat()
        ))

        await db.commit()


async def get_daily_usage(user_id: int, feature: str):
    today = datetime.utcnow().date().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM usage
        WHERE user_id = ?
        AND feature = ?
        AND DATE(created_at) = ?
        """, (
            user_id,
            feature,
            today
        ))

        row = await cursor.fetchone()

    return row[0] if row else 0


async def get_setting(key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT value
        FROM app_settings
        WHERE key = ?
        """, (key,))

        row = await cursor.fetchone()

    return row[0] if row else default


async def set_setting(key: str, value):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        INSERT OR REPLACE INTO app_settings (
            key,
            value
        )
        VALUES (?, ?)
        """, (
            key,
            str(value)
        ))

        await db.commit()


async def can_use_feature(user_id: int, feature: str):
    from config import settings

    if settings.ADMIN_ID and user_id == settings.ADMIN_ID:
        return True

    plan = await get_user_plan(user_id)

    tariff = TARIFFS.get(plan, TARIFFS["free"])

    if tariff["unlimited"]:
        return True

    limit = await get_feature_limit(user_id, feature)
    used = await get_daily_usage(user_id, feature)

    return used < limit


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM users
        """)
        total_users = (await cursor.fetchone())[0]

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE plan = 'pro'
        """)
        total_pro = (await cursor.fetchone())[0]

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM usage
        """)
        total_generations = (await cursor.fetchone())[0]

    return {
        "total_users": total_users,
        "total_pro": total_pro,
        "total_generations": total_generations
    }


async def get_all_limits():
    return {
        "rewrite": await get_setting("limit_rewrite"),
        "content_factory": await get_setting("limit_content_factory"),
        "brand_rewrite": await get_setting("limit_brand_rewrite"),
        "post_image": await get_setting("limit_post_image"),
        "content_pack": await get_setting("limit_content_pack")
    }


async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT user_id
        FROM users
        """)

        rows = await cursor.fetchall()

    return [row[0] for row in rows]


async def get_subscription_info(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        SELECT plan, pro_until, created_at
        FROM users
        WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    if not row:
        return {
            "plan": "free",
            "pro_until": None,
            "created_at": None,
            "days_left": 0
        }

    plan, pro_until, created_at = row

    days_left = 0

    if plan != "free" and pro_until:
        try:
            end_date = datetime.fromisoformat(pro_until)
            seconds_left = (end_date - datetime.utcnow()).total_seconds()
            days_left = max(0, int(seconds_left // 86400) + 1)
        except Exception:
            days_left = 0

    return {
        "plan": plan,
        "pro_until": pro_until,
        "created_at": created_at,
        "days_left": days_left
    }


async def save_user_style(user_id: int, style_text: str):
    await register_user(user_id)

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        INSERT OR REPLACE INTO user_styles (
            user_id,
            style_text,
            updated_at
        )
        VALUES (?, ?, ?)
        """, (
            user_id,
            style_text,
            datetime.utcnow().isoformat()
        ))

        await db.commit()


async def get_user_style(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT style_text
        FROM user_styles
        WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    return row[0] if row else None


async def reset_user_style(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        DELETE FROM user_styles
        WHERE user_id = ?
        """, (user_id,))

        await db.commit()


async def save_user_profile_field(user_id: int, field: str, value: str):
    await register_user(user_id)

    allowed_fields = [
        "niche",
        "audience",
        "offer",
        "city",
        "cta",
        "visual_style",
        "visual_style_title",
        "content_goal",
        "content_goal_title",
    ]

    if field not in allowed_fields:
        return False

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        INSERT OR IGNORE INTO user_profiles (
            user_id,
            updated_at
        )
        VALUES (?, ?)
        """, (
            user_id,
            datetime.utcnow().isoformat()
        ))

        await db.execute(f"""
        UPDATE user_profiles
        SET {field} = ?,
            updated_at = ?
        WHERE user_id = ?
        """, (
            value,
            datetime.utcnow().isoformat(),
            user_id
        ))

        await db.commit()

    return True


async def get_user_profile(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT niche, audience, offer, city, cta, visual_style, visual_style_title, content_goal, content_goal_title
        FROM user_profiles
        WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    if not row:
        return {
            "niche": None,
            "audience": None,
            "offer": None,
            "city": None,
            "cta": None,
            "visual_style": None,
            "visual_style_title": None,
            "content_goal": None,
            "content_goal_title": None,
        }

    return {
        "niche": row[0],
        "audience": row[1],
        "offer": row[2],
        "city": row[3],
        "cta": row[4],
        "visual_style": row[5] if len(row) > 5 else None,
        "visual_style_title": row[6] if len(row) > 6 else None,
        "content_goal": row[7] if len(row) > 7 else None,
        "content_goal_title": row[8] if len(row) > 8 else None,
    }


async def reset_user_profile(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        DELETE FROM user_profiles
        WHERE user_id = ?
        """, (user_id,))

        await db.commit()


async def add_scheduled_post(text: str, publish_at: str, image_path: str | None = None):
    await init_autopost_db()

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        INSERT INTO scheduled_posts (
            text,
            image_path,
            publish_at,
            status,
            created_at
        )
        VALUES (?, ?, ?, 'scheduled', ?)
        """, (
            text,
            image_path,
            publish_at,
            datetime.utcnow().isoformat()
        ))

        await db.commit()


async def get_scheduled_posts():
    await init_autopost_db()

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT id, text, image_path, publish_at, status
        FROM scheduled_posts
        WHERE status = 'scheduled'
        ORDER BY publish_at ASC
        LIMIT 10
        """)

        rows = await cursor.fetchall()

    return rows


async def get_due_posts():
    await init_autopost_db()

    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT id, text, image_path, publish_at
        FROM scheduled_posts
        WHERE status = 'scheduled'
        AND publish_at <= ?
        ORDER BY publish_at ASC
        """, (now,))

        rows = await cursor.fetchall()

    return rows


async def mark_post_published(post_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        UPDATE scheduled_posts
        SET status = 'published'
        WHERE id = ?
        """, (post_id,))

        await db.commit()


async def get_scheduled_post_by_id(post_id: int):
    await init_autopost_db()

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT id, text, image_path, publish_at, status
        FROM scheduled_posts
        WHERE id = ?
        """, (post_id,))

        row = await cursor.fetchone()

    return row


async def delete_scheduled_post(post_id: int):
    await init_autopost_db()

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        UPDATE scheduled_posts
        SET status = 'deleted'
        WHERE id = ?
        """, (post_id,))

        await db.commit()


async def publish_scheduled_post_now(post_id: int):
    await init_autopost_db()

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT id, text, image_path, publish_at
        FROM scheduled_posts
        WHERE id = ?
        AND status = 'scheduled'
        """, (post_id,))

        row = await cursor.fetchone()

    return row


async def save_user_memory(
    user_id: int,
    favorite_topics=None,
    favorite_style=None,
    preferred_cta=None,
    preferred_tone=None
):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        INSERT OR IGNORE INTO user_memory (
            user_id,
            updated_at
        )
        VALUES (?, ?)
        """, (
            user_id,
            datetime.utcnow().isoformat()
        ))

        if favorite_topics is not None:
            await db.execute("""
            UPDATE user_memory
            SET favorite_topics = ?
            WHERE user_id = ?
            """, (
                favorite_topics,
                user_id
            ))

        if favorite_style is not None:
            await db.execute("""
            UPDATE user_memory
            SET favorite_style = ?
            WHERE user_id = ?
            """, (
                favorite_style,
                user_id
            ))

        if preferred_cta is not None:
            await db.execute("""
            UPDATE user_memory
            SET preferred_cta = ?
            WHERE user_id = ?
            """, (
                preferred_cta,
                user_id
            ))

        if preferred_tone is not None:
            await db.execute("""
            UPDATE user_memory
            SET preferred_tone = ?
            WHERE user_id = ?
            """, (
                preferred_tone,
                user_id
            ))

        await db.commit()


async def get_user_memory(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT
            favorite_topics,
            favorite_style,
            preferred_cta,
            preferred_tone
        FROM user_memory
        WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    if not row:
        return {
            "favorite_topics": None,
            "favorite_style": None,
            "preferred_cta": None,
            "preferred_tone": None
        }

    return {
        "favorite_topics": row[0],
        "favorite_style": row[1],
        "preferred_cta": row[2],
        "preferred_tone": row[3]
    }

TARIFFS = {
    "free": {
        "title": "FREE", "price": 0, "unlimited": False,
        "limits": {"content_factory": 1, "post_image": 1, "carousel": 0, "reels": 0, "ai_chat": 10, "content_pack": 0, "rewrite": 1, "brand_rewrite": 0, "style_train": 0, "queue": 0}
    },
    "start_premium": {
        "title": "Start Premium", "price": 119, "unlimited": False,
        "limits": {"content_factory": 3, "post_image": 2, "carousel": 1, "reels": 0, "ai_chat": 20, "content_pack": 0, "rewrite": 3, "brand_rewrite": 1, "style_train": 0, "queue": 0}
    },
    "plus": {
        "title": "Plus", "price": 179, "unlimited": False,
        "limits": {"content_factory": 5, "post_image": 4, "carousel": 1, "reels": 0, "ai_chat": 50, "content_pack": 1, "rewrite": 5, "brand_rewrite": 2, "style_train": 0, "queue": 1}
    },
    "vip": {
        "title": "VIP", "price": 299, "unlimited": False,
        "limits": {"content_factory": 8, "post_image": 6, "carousel": 2, "reels": 1, "ai_chat": 100, "content_pack": 2, "rewrite": 8, "brand_rewrite": 4, "style_train": 0, "queue": 1}
    },
    "premium": {
        "title": "Premium", "price": 399, "unlimited": False,
        "limits": {"content_factory": 12, "post_image": 8, "carousel": 3, "reels": 2, "ai_chat": 300, "content_pack": 3, "rewrite": 12, "brand_rewrite": 8, "style_train": 3, "queue": 1}
    },
    "pro": {
        "title": "PRO", "price": 599, "unlimited": False,
        "limits": {"content_factory": 16, "post_image": 10, "carousel": 4, "reels": 3, "ai_chat": 600, "content_pack": 4, "rewrite": 16, "brand_rewrite": 10, "style_train": 999, "queue": 1}
    },
}


async def activate_tariff(user_id: int, tariff: str, days: int = 30):
    await register_user(user_id)

    if tariff not in TARIFFS:
        tariff = "free"

    now = datetime.utcnow()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        SELECT pro_until
        FROM users
        WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

        base_date = now

        if row and row[0]:
            try:
                current_end = datetime.fromisoformat(row[0])
                if current_end > now:
                    base_date = current_end
            except Exception:
                base_date = now

        pro_until = base_date + timedelta(days=days)

        await db.execute("""
        UPDATE users
        SET plan = ?,
            pro_until = ?
        WHERE user_id = ?
        """, (
            tariff,
            pro_until.isoformat(),
            user_id
        ))

        await db.commit()


async def get_tariff_info(user_id: int):
    plan = await get_user_plan(user_id)

    if plan not in TARIFFS:
        plan = "free"

    return TARIFFS[plan]


async def get_feature_limit(user_id: int, feature: str):
    plan = await get_user_plan(user_id)
    tariff = TARIFFS.get(plan, TARIFFS["free"])

    limits = tariff.get("limits", {})
    if feature in limits:
        return int(limits[feature])

    # Fallback for old/internal features not yet mapped to the new tariff grid.
    base_limit = await get_setting(f"limit_{feature}")
    if not base_limit:
        return 0
    try:
        return int(base_limit)
    except Exception:
        return 0
async def has_used_trial(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        SELECT trial_used
        FROM users
        WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    if not row:
        return False

    return row[0] == "yes"


async def mark_trial_used(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE users
        SET trial_used = 'yes'
        WHERE user_id = ?
        """, (user_id,))

        await db.commit()    


async def save_user_memory_profile(
    user_id: int,
    niche: str = None,
    audience: str = None,
    offer: str = None,
    tone: str = None,
    cta: str = None,
    product: str = None
):
    await register_user(user_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_memory_profiles (
            user_id INTEGER PRIMARY KEY,
            niche TEXT,
            audience TEXT,
            offer TEXT,
            tone TEXT,
            cta TEXT,
            product TEXT
        )
        """)

        await db.execute("""
        INSERT INTO user_memory_profiles (
            user_id, niche, audience, offer, tone, cta, product
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            niche = COALESCE(excluded.niche, niche),
            audience = COALESCE(excluded.audience, audience),
            offer = COALESCE(excluded.offer, offer),
            tone = COALESCE(excluded.tone, tone),
            cta = COALESCE(excluded.cta, cta),
            product = COALESCE(excluded.product, product)
        """, (
            user_id,
            niche,
            audience,
            offer,
            tone,
            cta,
            product
        ))

        await db.commit()


async def get_user_memory_profile(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_memory_profiles (
            user_id INTEGER PRIMARY KEY,
            niche TEXT,
            audience TEXT,
            offer TEXT,
            tone TEXT,
            cta TEXT,
            product TEXT
        )
        """)

        cursor = await db.execute("""
        SELECT niche, audience, offer, tone, cta, product
        FROM user_memory_profiles
        WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    if not row:
        return {}

    return {
        "niche": row[0],
        "audience": row[1],
        "offer": row[2],
        "tone": row[3],
        "cta": row[4],
        "product": row[5],
    }


async def get_admin_analytics():
    async with aiosqlite.connect(DB_PATH) as db:
        users_cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await users_cursor.fetchone())[0]

        pro_cursor = await db.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE plan != 'free'
        """)
        paid_users = (await pro_cursor.fetchone())[0]

        usage_cursor = await db.execute("""
        SELECT feature, COUNT(*)
        FROM usage
        GROUP BY feature
        ORDER BY COUNT(*) DESC
        """)
        usage_rows = await usage_cursor.fetchall()

        posts_cursor = await db.execute("""
        SELECT COUNT(*)
        FROM scheduled_posts
        WHERE status = 'scheduled'
        """)
        pending_posts = (await posts_cursor.fetchone())[0]

    return {
        "total_users": total_users,
        "paid_users": paid_users,
        "usage": usage_rows,
        "pending_posts": pending_posts
    }


async def init_referral_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_id INTEGER,
            invited_id INTEGER UNIQUE,
            created_at TEXT
        )
        """)
        await db.commit()


async def add_referral(inviter_id: int, invited_id: int):
    if inviter_id == invited_id:
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        SELECT invited_id
        FROM referrals
        WHERE invited_id = ?
        """, (invited_id,))

        exists = await cursor.fetchone()

        if exists:
            return False

        await db.execute("""
        INSERT INTO referrals (inviter_id, invited_id, created_at)
        VALUES (?, ?, ?)
        """, (
            inviter_id,
            invited_id,
            datetime.utcnow().isoformat()
        ))

        await db.commit()

    return True


async def get_referral_count(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM referrals
        WHERE inviter_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    return row[0] if row else 0


async def get_referral_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM referrals
        WHERE inviter_id = ?
        """, (user_id,))

        total = (await cursor.fetchone())[0]

    return {
        "total_referrals": total,
        "premium_days": total * 3
    }

# ===== PRIME admin helpers =====
async def log_admin_event(level: str, event: str, details: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            event TEXT,
            details TEXT,
            created_at TEXT
        )
        """)
        await db.execute("INSERT INTO admin_logs (level,event,details,created_at) VALUES (?,?,?,?)",
                         (level, event, details, datetime.utcnow().isoformat()))
        await db.commit()

async def get_admin_logs(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            event TEXT,
            details TEXT,
            created_at TEXT
        )
        """)
        cur = await db.execute("SELECT level,event,details,created_at FROM admin_logs ORDER BY id DESC LIMIT ?", (limit,))
        return await cur.fetchall()

async def set_user_blocked(user_id: int, blocked: int = 1):
    await register_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("ALTER TABLE users ADD COLUMN blocked INTEGER DEFAULT 0")
        except Exception:
            pass
        await db.execute("UPDATE users SET blocked=? WHERE user_id=?", (int(blocked), int(user_id)))
        await db.commit()

async def add_user_bonus(user_id: int, amount: int = 10):
    await register_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("ALTER TABLE users ADD COLUMN bonus_generations INTEGER DEFAULT 0")
        except Exception:
            pass
        await db.execute("UPDATE users SET bonus_generations=COALESCE(bonus_generations,0)+? WHERE user_id=?", (int(amount), int(user_id)))
        await db.commit()

async def reset_user_limits(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM usage WHERE user_id=? AND DATE(created_at)=DATE('now')", (int(user_id),))
        await db.commit()

async def deactivate_pro(user_id: int):
    await register_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET plan='free', pro_until=NULL WHERE user_id=?", (int(user_id),))
        await db.commit()

async def get_user_history(user_id: int, limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT feature, created_at FROM usage WHERE user_id=? ORDER BY id DESC LIMIT ?", (int(user_id), int(limit)))
        return await cur.fetchall()

async def save_style_sample(user_id: int, sample_text: str, analysis: str):
    await register_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS style_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sample_text TEXT,
            analysis TEXT,
            created_at TEXT
        )
        """)
        await db.execute("INSERT INTO style_samples (user_id,sample_text,analysis,created_at) VALUES (?,?,?,?)",
                         (int(user_id), sample_text, analysis, datetime.utcnow().isoformat()))
        await db.commit()

async def get_style_samples(user_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS style_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sample_text TEXT,
            analysis TEXT,
            created_at TEXT
        )
        """)
        cur = await db.execute("SELECT sample_text, analysis, created_at FROM style_samples WHERE user_id=? ORDER BY id DESC LIMIT ?", (int(user_id), int(limit)))
        return await cur.fetchall()
