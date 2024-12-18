# app.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Handler va routerlar
from handlers.users.main import start_router
from handlers.users.admin.admin import router as admin_router
from handlers.users.admin.admin_base import router as admin_base_router
from handlers.users.admin.admin_spams import router as admin_spams_router
from handlers.users.main.converter import router as converter_router

# API va utillar
from utils.currency_api import CurrencyApi, currency_update_task, daily_notification_task
from data.config import load_config
from utils.database.db_init import init_db

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
    """Barcha handlerlarni ulash"""
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(admin_base_router)
    dp.include_router(admin_spams_router)
    dp.include_router(converter_router)
    logger.info("Barcha handlerlar ulandi")


async def main():
    # Configni yuklash
    config = load_config()

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Handlerlarni ulash
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