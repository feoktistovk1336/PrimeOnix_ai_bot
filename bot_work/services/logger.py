from loguru import logger

logger.add(
    "bot_errors.log",
    rotation="5 MB",
    retention="7 days",
    encoding="utf-8"
)