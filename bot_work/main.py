import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.db import init_db, init_autopost_db, init_referral_db

from services.queue import queue_worker
from services.autopost_worker import autopost_worker
from services.global_nav import GlobalNavigationMiddleware

from handlers.start import router as start_router
from handlers.primeonix_v2_clean import router as primeonix_v2_clean_router
from handlers.ui_navigation import router as ui_navigation_router
from handlers.admin import router as admin_router
from handlers.content import router as content_router
from handlers.rewrite import router as rewrite_router
from handlers.image_post import router as image_post_router
from handlers.brand import router as brand_router
from handlers.payments import router as payments_router
from handlers.analyze import router as analyze_router
from handlers.setup import router as setup_router
from handlers.cabinet import router as cabinet_router
from handlers.hooks import router as hooks_router
from handlers.funnel import router as funnel_router
from handlers.series import router as series_router
from handlers.cta import router as cta_router
from handlers.lead_magnet import router as lead_magnet_router
from handlers.referral import router as referral_router
from handlers.ig_tg_funnel import router as ig_tg_funnel_router
from handlers.admin_prime import router as admin_prime_router
from handlers.prime_viral import router as prime_viral_router
from handlers.prime_autopost import router as prime_autopost_router
from handlers.ai_chat import router as ai_chat_router


bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.message.middleware(GlobalNavigationMiddleware())

dp.include_router(start_router)
dp.include_router(primeonix_v2_clean_router)
dp.include_router(ui_navigation_router)
# PrimeOnix V2 admin router is placed before legacy admin router so V2 buttons do not fall through to old handlers.
dp.include_router(admin_prime_router)
dp.include_router(admin_router)
dp.include_router(prime_viral_router)
dp.include_router(prime_autopost_router)
dp.include_router(ai_chat_router)
dp.include_router(content_router)
dp.include_router(setup_router)
dp.include_router(analyze_router)
dp.include_router(rewrite_router)
dp.include_router(image_post_router)
dp.include_router(brand_router)
dp.include_router(payments_router)
dp.include_router(cabinet_router)
dp.include_router(hooks_router)
dp.include_router(funnel_router)
dp.include_router(series_router)
dp.include_router(cta_router)
dp.include_router(lead_magnet_router)
dp.include_router(referral_router)
dp.include_router(ig_tg_funnel_router)


async def main():
    await init_db()
    await init_autopost_db()
    await init_referral_db()
    for i in range(3):
        asyncio.create_task(queue_worker(worker_id=i + 1))

    asyncio.create_task(autopost_worker(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())