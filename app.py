# app.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers.users.main import start_router
from handlers.users.admin.admin_spams import router as admin_spams_router
from handlers.users.main.converter import router as converter_router
from handlers.users.admin.admin import router as admin_router
from middlewares.checksub import CheckSubscriptionMiddleware
from dotenv import load_dotenv
from data.config import load_config
from utils.database.db_init import init_db

load_dotenv()

# API va utillar
from utils.currency_api import (
    CurrencyApi,
    currency_update_task,
    daily_notification_task,
)


# Currency API instance
currency_api = CurrencyApi()

# Logger sozlamalari
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


async def setup_currency_service():
    """Valyuta API ni sozlash"""
    try:
        if await currency_api.update_rates():
            logger.info("Valyuta kurslari muvaffaqiyatli yuklandi")
            rates_info = "\n".join(
                [f"{k}: {v:,.2f} UZS" for k, v in currency_api.rates.items()]
            )
            logger.info(f"Joriy kurslar:\n{rates_info}")
            return True
        else:
            logger.error("Valyuta kurslarini yuklashda xatolik")
            return False
    except Exception as e:
        logger.error(f"Valyuta servisini ishga tushirishda xatolik: {e}")
        return False


async def init_services(bot: Bot):
    """Barcha servislarni ishga tushirish"""
    logger.info("Servislar ishga tushmoqda...")

    # Database ni ishga tushirish
    try:
        await init_db()
        logger.info("Database muvaffaqiyatli ishga tushdi")
    except Exception as e:
        logger.error(f"Database xatosi: {e}")
        return False

    # Valyuta servisini ishga tushirish
    if not await setup_currency_service():
        return False

    try:
        # Background tasklar
        asyncio.create_task(currency_update_task())
        logger.info("Valyuta yangilash task ishga tushdi")

        asyncio.create_task(daily_notification_task(bot))
        logger.info("Kunlik xabar task ishga tushdi")

        return True
    except Exception as e:
        logger.error(f"Background tasklar ishga tushishida xatolik: {e}")
        return False


def setup_handlers(dp: Dispatcher):
    """Barcha handlerlarni ulash va middleware'ni qo'shish"""
    # Middleware'ni barcha routerlarga qo'shish
    middleware = CheckSubscriptionMiddleware()

    # Admin router uchun middleware
    admin_router.message.middleware(middleware)
    admin_router.callback_query.middleware(middleware)

    # Start router uchun middleware
    start_router.message.middleware(middleware)
    start_router.callback_query.middleware(middleware)

    # Admin spams router uchun middleware
    admin_spams_router.message.middleware(middleware)
    admin_spams_router.callback_query.middleware(middleware)

    # Converter router uchun middleware
    converter_router.message.middleware(middleware)
    converter_router.callback_query.middleware(middleware)

    # Routerlarni Dispatcher'ga ulash
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(admin_spams_router)
    dp.include_router(converter_router)

    logger.info("Barcha handlerlar va middleware'lar ulandi")


async def main():
    # Configni yuklash
    config = load_config()
    await init_db()

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Handlerlar va middleware'larni ulash
    setup_handlers(dp)

    # Servislarni ishga tushirish
    if not await init_services(bot):
        logger.error("Servislarni ishga tushirishda xatolik. Bot to'xtatildi.")
        await bot.session.close()
        return

    # Botni ishga tushirish
    try:
        logger.info("Bot ishga tushdi")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot ishga tushishida xatolik: {e}")
    finally:
        # Bot to'xtaganda barcha resurslarni yopish
        await bot.session.close()
        await currency_api._close_session()
        logger.info("Bot va barcha resurslar to'xtatildi")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot administrativ tarzda to'xtatildi")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
        sys.exit(1)