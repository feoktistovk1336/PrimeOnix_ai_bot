from datetime import datetime


CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    plan TEXT DEFAULT 'free',
    pro_until TEXT,
    created_at TEXT
)
"""


CREATE_USAGE_TABLE = """
CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    feature TEXT,
    created_at TEXT
)
"""


CREATE_PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    provider TEXT,
    amount INTEGER,
    currency TEXT,
    status TEXT,
    payment_id TEXT,
    created_at TEXT
)
"""
