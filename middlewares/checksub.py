from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from data.config import load_config
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from utils.database.models import Subscription
from sqlalchemy.future import select
from typing import Any
import re


class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self):
        config = load_config()
        self.engine = create_async_engine(config.db.sqlalchemy_database_url)
        self.SessionLocal = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def check_all_subscriptions(self, user_id: int, bot) -> bool:
        """Check if the user is subscribed to all required channels."""
        async with self.SessionLocal() as session:
            async with session.begin():
                query = await session.execute(select(Subscription))
                channels = query.scalars().all()

                for channel in channels:
                    try:
                        # Extract the username from the link (e.g., https://t.me/username -> @username)
                        match = re.search(r"t\.me/([\w\d_]+)", channel.link)
                        if not match:
                            print(f"Invalid link format for channel: {channel.name}")
                            return False

                        channel_username = f"@{match.group(1)}"
                        member = await bot.get_chat_member(
                            chat_id=channel_username, user_id=user_id
                        )
                        if member.status not in ["member", "administrator", "creator"]:
                            return False
                    except Exception as e:
                        print(
                            f"Error checking subscription for channel {channel.name}: {e}"
                        )
                        return False

        return True  # User is subscribed to all channels

    async def __call__(
        self, handler, event: Message | CallbackQuery, data: dict
    ) -> Any:
        user_id = event.from_user.id
        bot = data["bot"]

        # Check if the user is subscribed to all channels
        is_subscribed = await self.check_all_subscriptions(user_id, bot)

        if not is_subscribed:
            message_text = (
                "Iltimos, quyidagi barcha kanallarga obuna bo'ling va qayta tekshiring!"
            )
            if isinstance(event, CallbackQuery):
                await event.answer(message_text, show_alert=True)
            elif isinstance(event, Message):
                await event.reply(message_text)
            return

        # Continue with the handler if the user is subscribed
        return await handler(event, data)
