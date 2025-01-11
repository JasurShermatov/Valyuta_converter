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
        """Foydalanuvchining barcha kanallarga a'zoligini tekshirish."""
        obuna_bolmagan_kanallar = []
        async with self.SessionLocal() as session:
            async with session.begin():
                query = await session.execute(select(Subscription))
                kanallar = query.scalars().all()

                for kanal in kanallar:
                    try:
                        kanal_username = kanal.link.replace("https://t.me/", "@")
                        user = await bot.get_chat_member(
                            chat_id=kanal_username, user_id=user_id
                        )
                        if user.status not in ["member", "administrator", "creator"]:
                            obuna_bolmagan_kanallar.append(
                                {"name": kanal.name, "link": kanal.link}
                            )
                    except Exception as e:
                        print(f"{kanal.name} kanali tekshirishda xatolik: {e}")
                        obuna_bolmagan_kanallar.append(
                            {"name": kanal.name, "link": kanal.link}
                        )

        return obuna_bolmagan_kanallar

    async def __call__(
        self,
        handler: Callable,
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        bot = data["bot"]

        # Check subscription buyrugʻi uchun tekshirish
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        # Start va Help buyruqlari uchun tekshirmasdan o'tkazib yuborish
        if isinstance(event, Message):
            if event.text in ["/start", "/help"]:
                return await handler(event, data)

        # A'zolikni tekshirish
        obuna_bolmagan_kanallar = await self.check_all_subscriptions(user_id, bot)

        # Agar obuna bo'lmagan kanallar mavjud bo'lsa
        if obuna_bolmagan_kanallar:
            tugmalar = await get_channel_keyboard(obuna_bolmagan_kanallar)
            xabar_matni = (
                f"📢 Iltimos, quyidagi {len(obuna_bolmagan_kanallar)} ta kanalga obuna bo'ling:"
            )

            try:
                if isinstance(event, CallbackQuery):
                    await event.message.edit_text(
                        text=xabar_matni,
                        reply_markup=tugmalar
                    )
                    await event.answer("Botdan foydalanish uchun kanallarga obuna bo'ling!", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer(
                        text=xabar_matni,
                        reply_markup=tugmalar
                    )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise e
            return

        # Agar barcha kanallarga obuna bo'lgan bo'lsa, handlerni ishga tushirish
        return await handler(event, data)