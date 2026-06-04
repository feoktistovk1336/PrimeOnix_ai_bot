from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    BOT_TOKEN: str

    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    REPLICATE_API_TOKEN: str | None = None

    ADMIN_ID: int | None = None
    CHANNEL_ID: int | None = None

    STRIPE_KEY: str | None = None

    BRAND_USERNAME: str | None = None
    TELEGRAM_LINK: str = "https://t.me/primeonix26"

    # n8n automation webhook. This is the main bridge:
    # Telegram bot -> n8n -> AI/Metricool/Instagram/Telegram workflows
    N8N_WEBHOOK_URL: str | None = None
    N8N_WEBHOOK_SECRET: str | None = None
    # Split n8n webhooks. If a specific webhook is empty, bot falls back to N8N_WEBHOOK_URL.
    # Supports both Railway variable styles:
    # N8N_TELEGRAM_WEBHOOK and N8N_TELEGRAM_WEBHOOK_URL.
    N8N_SYSTEM_WEBHOOK: str | None = None
    N8N_TELEGRAM_WEBHOOK: str | None = None
    N8N_INSTAGRAM_WEBHOOK: str | None = None
    N8N_CAROUSEL_WEBHOOK: str | None = None
    N8N_REELS_WEBHOOK: str | None = None
    N8N_FUNNEL_WEBHOOK: str | None = None
    N8N_BROADCAST_WEBHOOK: str | None = None
    N8N_PRO_WEBHOOK: str | None = None

    N8N_SYSTEM_WEBHOOK_URL: str | None = None
    N8N_TELEGRAM_WEBHOOK_URL: str | None = None
    N8N_INSTAGRAM_WEBHOOK_URL: str | None = None
    N8N_CAROUSEL_WEBHOOK_URL: str | None = None
    N8N_REELS_WEBHOOK_URL: str | None = None
    N8N_FUNNEL_WEBHOOK_URL: str | None = None
    N8N_BROADCAST_WEBHOOK_URL: str | None = None
    N8N_PRO_WEBHOOK_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()