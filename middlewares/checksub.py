from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from data.config import load_config
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from utils.database.models import Subscription
from sqlalchemy.future import select
from typing import Any, Dict, Callable
from keyboards.inline.user import get_channel_keyboard


class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self):
        config = load_config()
        self.engine = create_async_engine(config.db.sqlalchemy_database_url)
        self.SessionLocal = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def check_all_subscriptions(self, user_id: int, bot) -> list:

        obuna_bolmagan_kanallar = []
        async with self.SessionLocal() as session:
            async with session.begin():
                query = await session.execute(select(Subscription))
                kanallar = query.scalars().all()

                for kanal in kanallar:
                    kanal_username = kanal.link.replace("https://t.me/", "@")
                    kanal_id = kanal.channel_id  # Kanal ID bazadan olinadi

                    try:
                        # Asosiy tekshiruv: kanal_ID yoki username orqali
                        if kanal_id:
                            user = await bot.get_chat_member(
                                chat_id=int(kanal_id), user_id=user_id
                            )
                        else:
                            user = await bot.get_chat_member(
                                chat_id=kanal_username, user_id=user_id
                            )

                        # Agar foydalanuvchi kanal a'zosi bo‘lmasa
                        if user.status not in ["member", "administrator", "creator"]:
                            obuna_bolmagan_kanallar.append(
                                {"name": kanal.name, "link": kanal.link}
                            )

                    except Exception as e:
                        """
                        Bu yerga bot yoki Telegram tarafidan xatolik kelib tushsa,
                        foydalanuvchini obuna bo'lmaganlar ro'yxatiga kiritmasdan
                        o‘tkazib yuboramiz
                        """

                        """Muammo haqida log yozib qo'yishimiz mumkin"""

                        print(
                            f"{kanal.name} kanalini tekshirishda xatolik yuz berdi: {e}"
                        )

                        """Faqat obuna_bolmagan_kanallar ga qo‘shmaymiz, shunda foydalanuvchi
                        # "o‘tkazib yuboriladi"""
                        pass

        return obuna_bolmagan_kanallar

    async def __call__(
        self, handler: Callable, event: Message | CallbackQuery, data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        bot = data["bot"]

        # Check subscription buyrugʻi uchun tekshirish
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        # /start va /help buyruqlari uchun tekshiruvdan o'tkazmasdan davom etamiz
        if isinstance(event, Message):
            if event.text in ["/start", "/help"]:
                return await handler(event, data)

        # A'zolikni tekshirish
        obuna_bolmagan_kanallar = await self.check_all_subscriptions(user_id, bot)

        # Agar obuna bo'lmagan kanallar mavjud bo'lsa
        if obuna_bolmagan_kanallar:
            tugmalar = await get_channel_keyboard(obuna_bolmagan_kanallar)
            xabar_matni = f"📢 Iltimos, quyidagi {len(obuna_bolmagan_kanallar)} ta kanalga obuna bo'ling:"

            try:
                if isinstance(event, CallbackQuery):
                    await event.message.edit_text(
                        text=xabar_matni, reply_markup=tugmalar
                    )
                    await event.answer(
                        "Botdan foydalanish uchun kanallarga obuna bo'ling!",
                        show_alert=True,
                    )
                elif isinstance(event, Message):
                    await event.answer(text=xabar_matni, reply_markup=tugmalar)
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise e

            # Tekshiruvdan to‘xtab, handlerni chaqirmasdan qaytamiz
            return

        # Agar barcha kanallarga obuna bo'lgan bo'lsa (yoki xatolik bilan "o‘tkazib yuborilgan" bo‘lsa)
        # handlerni ishga tushiramiz
        return await handler(event, data)
