async def send_long(message, text: str, chunk_size: int = 3900, parse_mode: str | None = None):
    if not text:
        await message.answer("Пустой ответ.")
        return

    async def _send(part: str):
        try:
            await message.answer(part, parse_mode=parse_mode, disable_web_page_preview=True)
        except TypeError:
            try:
                await message.answer(part, parse_mode=parse_mode)
            except Exception:
                await message.answer(part)
        except Exception:
            try:
                await message.answer(part, disable_web_page_preview=True)
            except TypeError:
                await message.answer(part)

    if len(text) <= chunk_size:
        await _send(text)
        return

    # Режем аккуратно, чтобы меньше ломать HTML.
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            cut = text.rfind("\n", start, end)
            if cut > start + 1000:
                end = cut
        await _send(text[start:end])
        start = end
