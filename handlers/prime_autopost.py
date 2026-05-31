from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.admin import is_admin
from handlers.prime_viral import LAST_PRIME_RESULT
from keyboards import prime_panel_menu, prime_autopost_menu, dm_funnel_topic_menu, publish_prepare_menu, prime_publish_hub_menu, prime_checks_menu
from services.ai import ask_ai
from services.sender import send_long
from services.content_queue import (
    add_prime_content,
    list_prime_content,
    get_prime_content,
    schedule_prime_content,
    mark_prime_content,
    update_prime_content,
    build_publish_payload,
    STATUS_SCHEDULED,
    STATUS_READY,
    STATUS_SENT_TO_N8N,
    STATUS_IG_SENT,
    STATUS_TG_SENT,
)
from services.instagram_publisher import check_instagram_connection, instagram_config_status, publish_reel
from services.n8n_client import call_n8n, ping_n8n, n8n_config_status


router = Router()


class PrimeAutoPostState(StatesGroup):
    waiting_dm_topic = State()
    waiting_custom_dm_topic = State()
    waiting_reel_publish = State()
    waiting_schedule_time = State()


DM_TOPICS = {
    "🎁 10 нейронок": "лид-магнит: файл с 10 бесплатными нейронками, промптами и порядком применения",
    "🎬 Reels-промпт": "лид-магнит: промпт для viral Reels и инструкция как делать ролики под охваты",
    "🎠 Карусель": "лид-магнит: структура Instagram-карусели, промпт и порядок создания",
    "💸 AI для продаж": "лид-магнит: AI-инструменты и промпты для продаж через Instagram и Telegram",
}


AUTOPUBLISH_HELP = (
    "📤 <b>AutoPost Center</b>\n\n"
    "Центр управления публикациями Instagram → Telegram.\n\n"
    "Рабочая схема сейчас:\n"
    "• бот генерирует/сохраняет материал\n"
    "• очередь хранит статус, платформу, тип и время\n"
    "• n8n получает задачу и публикует через твой workflow/Metricool/Instagram\n\n"
    "Кнопки:\n"
    "• 📲 Instagram пакет — готовит Instagram-пакет через n8n\n"
    "• 📣 Telegram пакет — готовит Telegram-пакет через n8n\n"
    "• 🧪 Проверить IG Pipeline — тестирует связку bot → n8n\n"
    "• 📅 Публикация позже — сохраняет материал в scheduled\n"
    "• 📌 Очередь публикаций — показывает материалы и ID\n\n"
    "Meta API можно подключить позже. Сейчас основная безопасная связка: Telegram-бот → n8n → Instagram/Telegram."
)


@router.message(F.text.in_({"📤 AutoPost Center", "⬅️ AutoPost Center"}))
async def open_autopost_center(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    await state.clear()
    await message.answer(AUTOPUBLISH_HELP, reply_markup=prime_autopost_menu, parse_mode="HTML")


@router.message(F.text == "📲 Подключение Instagram")
async def instagram_setup_info(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    ok, missing, cfg = instagram_config_status()
    status = "✅ базовые переменные найдены" if ok else "⚠️ не хватает: " + ", ".join(missing)
    n8n_ok, n8n_missing, n8n_cfg = n8n_config_status()
    text = (
        "📲 <b>Подключение Instagram</b>\n\n"
        "Основной путь для проекта сейчас:\n"
        "<b>Telegram-бот → n8n → Metricool/Instagram</b>\n\n"
        f"n8n webhook: {'✅ подключен' if n8n_ok else '⚠️ не настроен'}\n"
        f"Meta API напрямую: {status}\n\n"
        "Что уже должно быть:\n"
        "1. Instagram добавлен в Metricool/автопостинг-сервис\n"
        "2. В n8n опубликован workflow с Webhook POST instagram-autopost\n"
        "3. В Railway есть N8N_WEBHOOK_URL\n\n"
        "Что нажимать дальше:\n"
        "• 🧪 Проверить n8n — проверить webhook\n"
        "• 🧪 Проверить IG Pipeline — отправить тестовую Instagram-задачу в n8n\n"
        "• 📲 Instagram пакет — подготовить последний материал для Instagram через n8n\n\n"
        "Для прямого Meta API позже нужны:\n"
        "META_ACCESS_TOKEN, IG_USER_ID, FB_PAGE_ID."
    )
    await message.answer(text, reply_markup=prime_autopost_menu, parse_mode="HTML")


@router.message(F.text == "🧪 Проверить n8n")
async def check_n8n_webhook(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    ok, missing, cfg = n8n_config_status()
    if not ok:
        await message.answer(
            "⚠️ n8n webhook не настроен.\n\n"
            "Добавь в Railway → Variables переменную:\n"
            "N8N_WEBHOOK_URL=http://37.252.21.95:5678/webhook/instagram-autopost\n\n"
            "После этого перезапусти бота и нажми проверку снова.",
            reply_markup=prime_autopost_menu,
        )
        return

    await message.answer("🧪 Проверяю n8n webhook...")
    result = await ping_n8n()
    if result.get("ok"):
        await message.answer(
            "✅ n8n webhook отвечает.\n\n"
            f"URL: {cfg.get('webhook_url')}\n"
            f"HTTP status: {result.get('status')}\n\n"
            "Теперь Telegram-бот может отправлять задачи в n8n.",
            reply_markup=prime_autopost_menu,
        )
        return

    await message.answer(
        "❌ n8n webhook не ответил как надо.\n\n"
        f"Ошибка: {result.get('error')}\n"
        f"Детали: {result.get('message') or result.get('raw') or result.get('data')}\n\n"
        "Проверь, что workflow опубликован в n8n и Webhook Method = POST.",
        reply_markup=prime_autopost_menu,
    )


@router.message(F.text == "🚀 Отправить в n8n")
async def send_last_prime_to_n8n(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    last = LAST_PRIME_RESULT.get(message.from_user.id)
    if not last:
        await message.answer(
            "Сначала создай материал в PRIME PANEL или IG→TG Воронке, потом отправляй его в n8n.",
            reply_markup=prime_panel_menu,
        )
        return

    await message.answer("🚀 Отправляю последний PRIME-материал в n8n...")
    result = await call_n8n({
        "action": "process_prime_content",
        "source": "telegram_bot",
        "telegram_user_id": message.from_user.id,
        "username": message.from_user.username,
        "tool": last.get("tool"),
        "topic": last.get("topic"),
        "content": last.get("content"),
        "expected_response": {
            "text": "Что n8n сделал с материалом: подготовил, поставил в очередь или вернул план публикации",
            "format": "json"
        }
    })

    if result.get("ok") and result.get("text"):
        await send_long(message, "✅ n8n обработал материал:\n\n" + result["text"])
        await message.answer("Что делаем дальше?", reply_markup=prime_autopost_menu)
        return

    if result.get("ok"):
        await message.answer(
            "✅ n8n принял материал.\n\n"
            "Но workflow пока не вернул текстовый ответ. Это нормально для первого этапа.\n"
            "Чтобы бот показывал результат, добавь в n8n финальный Respond to Webhook с JSON полем text.",
            reply_markup=prime_autopost_menu,
        )
        return

    await message.answer(
        "❌ Не удалось отправить материал в n8n.\n\n"
        f"Ошибка: {result.get('error')}\n"
        f"Детали: {result.get('message') or result.get('raw') or result.get('data')}",
        reply_markup=prime_autopost_menu,
    )


@router.message(F.text == "🧪 Проверить Instagram API")
async def check_instagram_api(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await message.answer("🧪 Проверяю Instagram API...")
    result = await check_instagram_connection()
    if result.get("ok"):
        data = result.get("data", {})
        await message.answer(
            "✅ Instagram API подключен.\n\n"
            f"Аккаунт: @{data.get('username', 'unknown')}\n"
            f"Тип: {data.get('account_type', 'unknown')}\n"
            f"Media count: {data.get('media_count', 'unknown')}",
            reply_markup=prime_autopost_menu,
        )
        return

    if result.get("error") == "missing_config":
        await message.answer(
            "⚠️ Instagram API пока не подключен.\n\n"
            "Не хватает переменных:\n"
            + "\n".join(f"• {x}" for x in result.get("missing", []))
            + "\n\nДобавь их в Railway → Variables.",
            reply_markup=prime_autopost_menu,
        )
        return

    await message.answer(
        "❌ Instagram API вернул ошибку.\n\n"
        f"Тип: {result.get('error')}\n"
        f"Статус: {result.get('status')}\n"
        f"Ответ: {result.get('data')}",
        reply_markup=prime_autopost_menu,
    )


@router.message(F.text == "📤 Подготовить Reels к IG")
async def prepare_reels_to_ig(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    last = LAST_PRIME_RESULT.get(message.from_user.id)
    if not last:
        await message.answer(
            "Сначала создай материал в PRIME PANEL: например Viral Reels или IG→TG Воронка.\n\n"
            "После генерации вернись сюда и нажми «📤 Подготовить Reels к IG».",
            reply_markup=prime_panel_menu,
        )
        return

    prompt = f"""
Ты — Instagram publishing producer.

Подготовь последний PRIME-материал к публикации Reels.

Тема:
{last.get('topic')}

Материал:
{last.get('content')}

Сделай строго такие блоки:
1. Caption для Instagram
2. Кодовое слово для комментария/Direct
3. DM-ответ на кодовое слово
4. Telegram-пост продолжение
5. Что должно быть в видео
6. Чек-лист перед публикацией
7. UTM/метка для отслеживания переходов

Пиши кратко, без воды, на русском.
"""
    await message.answer("📤 Готовлю Reels к публикации в Instagram...")
    result = await ask_ai(prompt)
    LAST_PRIME_RESULT[message.from_user.id] = {
        "tool": "Instagram Publish Prep",
        "topic": last.get("topic", "PRIME"),
        "content": result,
    }
    await send_long(message, result)
    await message.answer("Готово. Можешь сохранить как ready или опубликовать по video_url.", reply_markup=publish_prepare_menu)


@router.message(F.text == "📌 Сохранить как готово к IG")
async def save_ready_to_instagram(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    last = LAST_PRIME_RESULT.get(message.from_user.id)
    if not last:
        await message.answer("Сначала подготовь материал к публикации.", reply_markup=prime_autopost_menu)
        return

    item = add_prime_content(
        user_id=message.from_user.id,
        tool="Instagram Ready",
        topic=last.get("topic", "PRIME"),
        content=last.get("content", ""),
        status="ig_ready",
        platform="instagram",
        content_type="reels_or_carousel",
        meta={"source": last.get("source", "telegram_bot"), "ready_for": "instagram_n8n"},
    )
    await message.answer(
        f"📌 Материал сохранён как готовый к Instagram.\n\nID: {item['id']}\nСтатус: ig_ready",
        reply_markup=prime_autopost_menu,
    )


@router.message(F.text == "📨 DM Funnel")
async def open_dm_funnel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.clear()
    await state.set_state(PrimeAutoPostState.waiting_dm_topic)
    await message.answer(
        "📨 <b>DM Funnel</b>\n\n"
        "Выбери тему для воронки или нажми «✍️ Своя DM-тема».\n\n"
        "На выходе получишь:\n"
        "• кодовое слово\n"
        "• ответ в Direct\n"
        "• ссылочную механику в TG\n"
        "• Telegram-пост\n"
        "• прогрев после входа",
        reply_markup=dm_funnel_topic_menu,
        parse_mode="HTML",
    )


@router.message(PrimeAutoPostState.waiting_dm_topic)
async def choose_dm_topic(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    text = (message.text or "").strip()
    if text == "⬅️ AutoPost Center":
        await state.clear()
        await message.answer(AUTOPUBLISH_HELP, reply_markup=prime_autopost_menu, parse_mode="HTML")
        return
    if text == "✍️ Своя DM-тема":
        await state.set_state(PrimeAutoPostState.waiting_custom_dm_topic)
        await message.answer("Напиши тему DM-воронки одним сообщением.", reply_markup=dm_funnel_topic_menu)
        return

    topic = DM_TOPICS.get(text, text)
    await _generate_dm_funnel(message, state, topic)


@router.message(PrimeAutoPostState.waiting_custom_dm_topic)
async def custom_dm_topic(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    topic = (message.text or "").strip()
    if len(topic) < 5:
        await message.answer("Напиши тему подробнее.")
        return
    await _generate_dm_funnel(message, state, topic)


async def _generate_dm_funnel(message: Message, state: FSMContext, topic: str):
    await state.clear()
    prompt = f"""
Ты — Instagram DM funnel strategist.

Создай DM-воронку Instagram → Telegram на тему:
{topic}

Формат:
1. Кодовое слово: одно короткое слово латиницей или кириллицей
2. CTA для Reels: что сказать в конце ролика
3. CTA для карусели: что написать на последнем слайде
4. Автоответ в Direct: коротко, дружелюбно, с переходом в Telegram
5. Telegram-пост продолжение: готовый текст
6. Лид-магнит: что человек получает в TG
7. Прогрев после входа: 3 следующих сообщения/поста
8. Как не выглядеть спамно

Правила:
- без воды
- не обещай гарантированные миллионы просмотров
- сделай связку максимально понятной
- пиши на русском
"""
    await message.answer("📨 Собираю DM-воронку...")
    result = await ask_ai(prompt)
    LAST_PRIME_RESULT[message.from_user.id] = {
        "tool": "DM Funnel",
        "topic": topic,
        "content": result,
    }
    await send_long(message, result)
    await message.answer("✅ DM-воронка готова. Можно сохранить или подготовить к публикации.", reply_markup=publish_prepare_menu)


@router.message(F.text == "📅 Публикация позже")
async def schedule_publication_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    last = LAST_PRIME_RESULT.get(message.from_user.id)
    if last:
        await state.clear()
        await state.update_data(schedule_source="last")
        await state.set_state(PrimeAutoPostState.waiting_schedule_time)
        await message.answer(
            "📅 <b>Публикация позже</b>\n\n"
            "Я запланирую последний сгенерированный материал.\n\n"
            "Напиши дату и время одним сообщением.\n\n"
            "Примеры:\n"
            "• сегодня 20:30\n"
            "• завтра 18:00\n"
            "• 30.05 19:00\n"
            "• 2026-05-30 19:00\n\n"
            "Или нажми «⬅️ AutoPost Center», чтобы отменить.",
            reply_markup=prime_autopost_menu,
            parse_mode="HTML",
        )
        return

    await message.answer(
        "📅 <b>Публикация позже</b>\n\n"
        "Сейчас нет последнего материала в памяти бота.\n\n"
        "Можно запланировать материал из очереди командой:\n\n"
        "<code>запланировать 3 завтра 18:00</code>\n\n"
        "Где 3 — ID материала из очереди.\n"
        "Нажми «📌 Очередь публикаций», чтобы посмотреть ID.",
        reply_markup=prime_autopost_menu,
        parse_mode="HTML",
    )


def _parse_schedule_time(raw: str):
    from datetime import datetime, timedelta
    import re

    text = (raw or "").strip().lower().replace("  ", " ")
    now = datetime.now()

    m = re.search(r"(\d{1,2})[:.](\d{2})", text)
    hour = int(m.group(1)) if m else 10
    minute = int(m.group(2)) if m else 0

    if "послезавтра" in text:
        dt = now + timedelta(days=2)
        return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if "завтра" in text:
        dt = now + timedelta(days=1)
        return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if "сегодня" in text:
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt

    for fmt in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%d.%m %H:%M"):
        try:
            dt = datetime.strptime(text, fmt)
            if fmt == "%d.%m %H:%M":
                dt = dt.replace(year=now.year)
                if dt <= now:
                    dt = dt.replace(year=now.year + 1)
            return dt
        except ValueError:
            pass

    # If user sent only time, schedule today if future, otherwise tomorrow.
    if re.fullmatch(r"\d{1,2}[:.]\d{2}", text):
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt

    return None


@router.message(PrimeAutoPostState.waiting_schedule_time)
async def schedule_last_material_time(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    text = (message.text or "").strip()
    if text == "⬅️ AutoPost Center":
        await state.clear()
        await message.answer(AUTOPUBLISH_HELP, reply_markup=prime_autopost_menu, parse_mode="HTML")
        return

    dt = _parse_schedule_time(text)
    if not dt:
        await message.answer(
            "Не понял дату/время. Напиши так:\n\n"
            "завтра 18:00\n"
            "или\n"
            "30.05 19:00",
            reply_markup=prime_autopost_menu,
        )
        return

    last = LAST_PRIME_RESULT.get(message.from_user.id)
    if not last:
        await state.clear()
        await message.answer("Не нашёл последний материал. Создай материал ещё раз или выбери из очереди.", reply_markup=prime_autopost_menu)
        return

    item = add_prime_content(
        user_id=message.from_user.id,
        tool=last.get("tool", "PRIME"),
        topic=last.get("topic", "Без темы"),
        content=last.get("content", ""),
        status=STATUS_SCHEDULED,
        scheduled_at=dt.strftime("%Y-%m-%d %H:%M"),
        platform="all",
        content_type=last.get("tool", "PRIME"),
        meta={"source": last.get("source", "telegram_bot"), "publish_pipeline": "ig_tg"},
    )
    await state.clear()
    await message.answer(
        "✅ Материал запланирован.\n\n"
        f"ID: {item['id']}\n"
        f"Статус: scheduled\n"
        f"Время: {item['scheduled_at']}\n"
        f"Тема: {item['topic']}\n\n"
        "Пока это сохраняет материал в очередь. Следующий шаг — подключим n8n worker, который будет забирать scheduled и публиковать в Instagram/Telegram.",
        reply_markup=prime_autopost_menu,
    )


@router.message(F.text.regexp(r"^запланировать\s+\d+\s+.+"))
async def schedule_queue_item_by_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    import re
    m = re.match(r"^запланировать\s+(\d+)\s+(.+)$", (message.text or "").strip(), re.I)
    if not m:
        await message.answer("Формат: запланировать 3 завтра 18:00", reply_markup=prime_autopost_menu)
        return

    item_id = int(m.group(1))
    dt = _parse_schedule_time(m.group(2))
    if not dt:
        await message.answer("Не понял дату/время. Пример: запланировать 3 завтра 18:00", reply_markup=prime_autopost_menu)
        return

    item = get_prime_content(item_id, message.from_user.id)
    if not item:
        await message.answer("Не нашёл материал с таким ID в твоей очереди.", reply_markup=prime_autopost_menu)
        return

    updated = schedule_prime_content(item_id, dt.strftime("%Y-%m-%d %H:%M"))
    await message.answer(
        "✅ Материал запланирован из очереди.\n\n"
        f"ID: {item_id}\n"
        f"Время: {updated.get('scheduled_at') if updated else dt.strftime('%Y-%m-%d %H:%M')}\n"
        f"Тема: {item.get('topic', 'Без темы')}",
        reply_markup=prime_publish_hub_menu,
    )


@router.message(F.text == "📌 Очередь публикаций")
async def publication_queue(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    items = list_prime_content(message.from_user.id, limit=15)
    if not items:
        await message.answer("📌 Очередь публикаций пока пустая.", reply_markup=prime_publish_hub_menu)
        return

    lines = ["📌 <b>Очередь публикаций</b>\n"]
    for item in items[:15]:
        topic = str(item.get("topic", "Без темы"))
        if len(topic) > 70:
            topic = topic[:67] + "..."
        scheduled = item.get("scheduled_at") or "—"
        lines.append(
            f"ID: {item.get('id')}\n"
            f"Статус: {item.get('status')}\n"
            f"Платформа: {item.get('platform') or 'all'}\n"
            f"Время: {scheduled}\n"
            f"Тип: {item.get('tool')}\n"
            f"Тема: {topic}\n"
        )
    lines.append("Команды:\n<code>запланировать 3 завтра 18:00</code>\n<code>готово 3</code>\n<code>удалить 3</code>")
    await message.answer("\n".join(lines), reply_markup=prime_publish_hub_menu, parse_mode="HTML")


async def _send_last_to_n8n_publish(message: Message, action: str, platform: str, human_title: str):
    last = LAST_PRIME_RESULT.get(message.from_user.id)
    if not last:
        await message.answer(
            "Сначала создай материал в PRIME PANEL или IG→TG Воронке.\n\n"
            "Потом нажми кнопку публикации ещё раз.",
            reply_markup=prime_autopost_menu,
        )
        return

    item = add_prime_content(
        user_id=message.from_user.id,
        tool=last.get("tool", "PRIME"),
        topic=last.get("topic", "Без темы"),
        content=last.get("content", ""),
        status=STATUS_READY,
        platform=platform,
        content_type=last.get("tool", "PRIME"),
        meta={
            "source": last.get("source", "telegram_bot"),
            "publish_action": action,
            "publish_pipeline": "bot_to_n8n",
        },
    )

    payload = build_publish_payload(item, action=action)
    payload.update({
        "username": message.from_user.username,
        "human_title": human_title,
        "telegram_parse_mode": "HTML",
    })

    await message.answer(f"🚀 Отправляю в n8n: {human_title}...")
    result = await call_n8n(payload)

    if result.get("ok"):
        # Важно: пока Meta/Metricool не подключены напрямую, не пишем fake "опубликовано".
        # Это статус подготовки/передачи в n8n.
        status = STATUS_SENT_TO_N8N
        if platform == "instagram":
            status = "ig_package_ready"
        elif platform == "telegram":
            status = "tg_package_ready"
        update_prime_content(item["id"], status=status, meta={**item.get("meta", {}), "n8n_result": result.get("data")})
        text = result.get("text") or "n8n принял задачу и подготовил пакет. Проверь Executions/очередь."
        title = human_title.replace("публикация", "пакет").replace("Публикация", "пакет")
        await send_long(message, f"✅ {title} готов\n\nID в очереди: {item['id']}\nСтатус: {status}\n\n{text}", parse_mode="HTML")
        await message.answer("Что делаем дальше?", reply_markup=prime_autopost_menu)
        return

    update_prime_content(item["id"], status="failed", meta={**item.get("meta", {}), "n8n_error": result})
    await message.answer(
        "❌ n8n не принял задачу публикации.\n\n"
        f"ID в очереди: {item['id']}\n"
        f"Ошибка: {result.get('error')}\n"
        f"Детали: {result.get('message') or result.get('raw') or result.get('data')}",
        reply_markup=prime_autopost_menu,
    )


@router.message(F.text.in_({"📲 Отправить в Instagram", "📣 Отправить в Telegram", "📲 Instagram пакет", "📣 Telegram пакет", "🚀 Запустить автопостинг", "🧪 Проверить IG Pipeline"}))
async def route_publish_action(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    if message.text == "🧪 Проверить IG Pipeline":
        await message.answer("🧪 Отправляю тестовую Instagram-задачу в n8n...")
        result = await call_n8n({
            "action": "test_instagram_pipeline",
            "source": "telegram_bot",
            "platform": "instagram",
            "content_type": "test",
            "topic": "PrimeOnix Instagram pipeline test",
            "content": "Тест: Telegram bot → n8n → Instagram/Metricool workflow",
            "expected_response": {"text": "Pipeline status for Telegram"},
        }, timeout=45)
        if result.get("ok"):
            await message.answer("✅ IG Pipeline ответил.\n\n" + (result.get("text") or "n8n принял тест."), reply_markup=prime_checks_menu)
        else:
            await message.answer(
                "❌ IG Pipeline не ответил как надо.\n\n"
                f"Ошибка: {result.get('error')}\n"
                f"Детали: {result.get('message') or result.get('raw') or result.get('data')}",
                reply_markup=prime_checks_menu,
            )
        return

    if message.text in {"📲 Отправить в Instagram", "📲 Instagram пакет"}:
        await _send_last_to_n8n_publish(message, "publish_instagram", "instagram", "Instagram публикация")
        return

    if message.text in {"📣 Отправить в Telegram", "📣 Telegram пакет"}:
        await _send_last_to_n8n_publish(message, "publish_telegram", "telegram", "Telegram публикация")
        return

    if message.text == "🚀 Запустить автопостинг":
        await _send_last_to_n8n_publish(message, "publish_ig_tg_pipeline", "all", "полный IG→TG автопостинг")
        return


@router.message(F.text == "📤 Опубликовать Reels по URL")
async def ask_reels_url(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    await state.set_state(PrimeAutoPostState.waiting_reel_publish)
    await message.answer(
        "📤 Отправь video_url и caption в формате:\n\n"
        "https://site.com/video.mp4 | Текст описания для Instagram\n\n"
        "Важно: video_url должен быть публичной прямой ссылкой на mp4.",
        reply_markup=publish_prepare_menu,
    )


@router.message(PrimeAutoPostState.waiting_reel_publish)
async def publish_reels_by_url(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return

    text = (message.text or "").strip()
    if text == "⬅️ AutoPost Center":
        await state.clear()
        await message.answer(AUTOPUBLISH_HELP, reply_markup=prime_autopost_menu, parse_mode="HTML")
        return

    if "|" not in text:
        await message.answer("Нужен формат: video_url | caption")
        return

    video_url, caption = [x.strip() for x in text.split("|", 1)]
    if not video_url.startswith("http"):
        await message.answer("video_url должен начинаться с http/https.")
        return

    await message.answer("📤 Отправляю Reels в Instagram API. Это может занять немного времени...")
    result = await publish_reel(video_url, caption)
    await state.clear()

    if result.get("ok"):
        await message.answer(
            "✅ Reels опубликован.\n\n"
            f"Media ID: {result.get('media_id')}\n"
            f"Creation ID: {result.get('creation_id')}",
            reply_markup=prime_autopost_menu,
        )
        return

    if result.get("error") == "missing_config":
        await message.answer(
            "⚠️ Публикация не запущена: не хватает переменных Instagram API.\n\n"
            + "\n".join(f"• {x}" for x in result.get("missing", [])),
            reply_markup=prime_autopost_menu,
        )
        return

    await message.answer(
        "❌ Instagram API не опубликовал Reels.\n\n"
        f"Ошибка: {result.get('error')}\n"
        f"Ответ: {result.get('data')}",
        reply_markup=prime_autopost_menu,
    )
