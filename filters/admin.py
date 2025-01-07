# filters/admin.py

from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from data.config import load_config


class AdminFilter(BaseFilter):
    """Foydalanuvchini admin ekanligini tekshiruvchi filter."""

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        config = load_config()
        user_id = event.from_user.id
        return user_id in config.bot.admin_ids
