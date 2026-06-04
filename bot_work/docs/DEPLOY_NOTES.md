# Deploy Notes

## Minimum environment variables

- `BOT_TOKEN`
- `GROQ_API_KEY`
- `ADMIN_ID`

## Optional

- `REPLICATE_API_TOKEN` — premium image generation.
- `CHANNEL_ID` — Telegram channel for autoposting.
- `OPENAI_API_KEY` — legacy compatibility helpers.

## Important

SQLite is okay for local testing and first launch. For public production, migrate to PostgreSQL.
