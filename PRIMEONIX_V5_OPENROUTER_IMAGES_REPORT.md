# PrimeOnix V5 — OpenRouter Images

База: primeonix_ai_bot_v7_n8n_quality_actions_v4_fix.

Исправлено:
- Бот теперь умеет отправлять картинки, которые OpenRouter возвращает как `data:image/...;base64,...`.
- Обычные URL картинок также поддерживаются.
- Качество поста выводится отдельным сообщением, а не внутри текста поста.
- Кнопки после генерации остаются под материалом.

Связанный workflow:
- primeonix_v2_openrouter_content_engine_v5_openrouter_images.json

Важно:
- В n8n во всех OpenRouter HTTP Request узлах нужно заменить `Bearer sk-or-v1-PASTE_OPENROUTER_KEY_HERE` на реальный OpenRouter ключ.
- Image model по умолчанию: `x-ai/grok-imagine-image-quality`.
