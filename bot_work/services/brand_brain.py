from services.ai import ask_ai


async def build_brand_brain(samples: str):

    result = await ask_ai(f"""
Ты — elite Brand Voice strategist и senior copywriter.

Проанализируй примеры постов автора.

Посты:

{samples}

Создай глубокий Brand Brain Profile.

Структура:

1. Tone of voice
Как звучит автор.

2. Эмоциональность
Какие эмоции вызывает.

3. Структура постов
Как строятся тексты.

4. Hooks
Как автор цепляет внимание.

5. CTA
Как автор призывает к действию.

6. Vocabulary
Какие слова и обороты часто использует.

7. Sentence style
Какие предложения:
- короткие
- длинные
- резкие
- спокойные

8. Energy level
Насколько энергичный стиль.

9. Expert positioning
Как автор показывает экспертность.

10. Storytelling
Есть ли истории, аналогии, метафоры.

11. Forbidden style
Как НЕ надо писать.

12. Writing instructions
Как генерировать новые посты в стиле автора.

Правила:
- без markdown
- без таблиц
- без воды
- максимально конкретно
- пиши как AI-анализ личности бренда
""")

    return result.strip()