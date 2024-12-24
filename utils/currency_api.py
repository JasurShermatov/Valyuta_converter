import aiohttp
import asyncio
from datetime import datetime, time, timedelta
import logging
from typing import Dict, Optional, Tuple
from utils.database.db import DataBase

logger = logging.getLogger(__name__)


class CurrencyApi:
    """CBU.uz API orqali valyuta kurslarini olish"""

    def __init__(self):
        self.rates: Dict[str, float] = {}
        self.last_update: Optional[datetime] = None
        self.update_interval: int = 300  # 5 daqiqa
        self.db = DataBase()
        self._session: Optional[aiohttp.ClientSession] = None
        self._url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"  # CBU.uz API manzili
        self._headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """aiohttp session ni olish yoki yaratish"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self._headers)
        return self._session

    async def _close_session(self):
        """Session ni yopish"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_rates(self) -> Optional[Dict[str, float]]:
        """CBU.uz dan valyuta kurslarini olish"""
        try:
            session = await self._get_session()
            async with session.get(self._url) as response:
                if response.status != 200:
                    logger.error(f"CBU.uz API xatosi: {response.status}")
                    return None

                data = await response.json()
                rates = {}

                for item in data:
                    try:
                        code = item[
                            "Ccy"
                        ]  # CBU.uz API da "Ccy" kalit so'zi ishlatiladi
                        if code in ["USD", "EUR", "GBP", "RUB"]:
                            rate = float(
                                item["Rate"]
                            )  # CBU.uz API da "Rate" kalit so'zi ishlatiladi
                            rates[code] = rate
                            logger.debug(f"Parsed {code}: {rate}")

                    except (KeyError, ValueError) as e:
                        logger.error(f"Valyutani parse qilishda xato {code}: {e}")
                        continue

                if not rates:
                    logger.error("Birorta ham kurs olinmadi")
                    return None

                logger.info(f"Kurslar muvaffaqiyatli olindi: {rates}")
                return rates

        except aiohttp.ClientError as e:
            logger.error(f"API so'rov yuborishda xato: {e}")
            return None
        except Exception as e:
            logger.error(f"Kutilmagan xato: {e}")
            return None
        finally:
            await self._close_session()

    async def update_rates(self) -> bool:
        """Kurslarni yangilash va farqlarni tekshirish"""
        try:
            new_rates = await self.get_rates()
            if not new_rates:
                return False

            # Kurslar o'zgarishini tekshirish
            if self.rates:
                changes = []
                for currency, new_rate in new_rates.items():
                    old_rate = self.rates.get(currency)
                    if (
                        old_rate and abs(new_rate - old_rate) >= 0.01
                    ):  # 1 tiyin o'zgarish
                        diff = new_rate - old_rate
                        percent = (diff / old_rate) * 100
                        changes.append(
                            f"{currency}: {old_rate:,.2f} → {new_rate:,.2f} UZS "
                            f"({diff:+.2f} / {percent:+.2f}%)"
                        )

                if changes:
                    logger.info("🔄 Kurslar o'zgardi:\n" + "\n".join(changes))

            self.rates = new_rates
            self.last_update = datetime.now()
            return True

        except Exception as e:
            logger.error(f"Kurslarni yangilashda xato: {e}")
            return False

    async def get_rate(
        self, from_currency: str, to_currency: str
    ) -> Tuple[float, datetime]:
        """Konvertatsiya kursini hisoblash"""
        if (
            not self.rates
            or not self.last_update
            or (datetime.now() - self.last_update).seconds > self.update_interval
        ):
            if not await self.update_rates():
                raise ValueError("Kurslarni yangilashda xatolik")

        try:
            if from_currency == "UZS":
                rate = 1 / self.rates[to_currency]
            elif to_currency == "UZS":
                rate = self.rates[from_currency]
            else:
                rate = self.rates[from_currency] / self.rates[to_currency]
            return rate, self.last_update

        except KeyError:
            logger.error(f"Noto'g'ri valyuta kodi: {from_currency} yoki {to_currency}")
            raise ValueError("Noto'g'ri valyuta kodi")
        except Exception as e:
            logger.error(f"Kursni hisoblashda xatolik: {e}")
            raise

    async def send_daily_notification(self, bot):
        """Kunlik valyuta kurslari haqida xabar yuborish"""
        try:
            if not await self.update_rates():
                logger.error("Kunlik xabar uchun kurslarni yangilab bo'lmadi")
                return

            message = (
                "💰 Bugungi valyuta kurslari (CBU.uz):\n\n"
                f"🇺🇸 1 USD = {self.rates.get('USD', 0):,.2f} UZS\n"
                f"🇪🇺 1 EUR = {self.rates.get('EUR', 0):,.2f} UZS\n"
                f"🇬🇧 1 GBP = {self.rates.get('GBP', 0):,.2f} UZS\n"
                f"🇷🇺 1 RUB = {self.rates.get('RUB', 0):,.2f} UZS\n\n"
                f"🕐 Yangilangan vaqt: {self.last_update.strftime('%H:%M')}"
            )

            users = await self.db.get_all_users()
            sent = 0
            failed = 0

            for user in users:
                try:
                    await bot.send_message(chat_id=user["user_id"], text=message)
                    sent += 1
                    await asyncio.sleep(0.05)  # Anti-flood
                except Exception as e:
                    failed += 1
                    logger.error(f"Xabar yuborishda xato {user['user_id']}: {e}")

            logger.info(f"Kunlik xabar: {sent} ta yuborildi, {failed} ta xato")

        except Exception as e:
            logger.error(f"Kunlik xabar yuborishda xato: {e}")


# Global instance
currency_api = CurrencyApi()


async def currency_update_task():
    """Har 5 daqiqada kurslarni yangilash"""
    while True:
        try:
            if await currency_api.update_rates():
                logger.info(
                    f"Kurslar yangilandi: {currency_api.last_update.strftime('%H:%M:%S')}"
                )
            else:
                logger.error("Kurslarni yangilashda xatolik")
        except Exception as e:
            logger.error(f"Update task xatolik: {e}")
        await asyncio.sleep(300)  # 5 daqiqa


import pytz
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

def toshkent_now() -> datetime:
    """Toshkent vaqtini olish"""
    toshkent_zone = pytz.timezone('Asia/Tashkent')
    return datetime.now(toshkent_zone).replace(tzinfo=None)

async def daily_notification_task(bot):
    """Har kuni Toshkent vaqti bilan soat 7:30 da xabar yuborish"""
    target_hour, target_minute = 7, 30

    while True:
        now = toshkent_now()
        next_run = now.replace(
            hour=target_hour,
            minute=target_minute,
            second=0,
            microsecond=0
        )

        # Agar vaqt o'tgan bo'lsa, ertangi kunni hisoblang
        if now >= next_run:
            next_run += timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        logger.info(
            f"Keyingi xabar yuborish vaqti: {next_run} "
            f"(Toshkent vaqti bilan {next_run.strftime('%H:%M')})"
            f"({wait_seconds} soniya)"
        )

        await asyncio.sleep(wait_seconds)
        await currency_api.send_daily_notification(bot)