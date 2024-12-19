# filters/admin.py
from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from data.config import load_config


class AdminFilter(BaseFilter):
    is_admin: bool = True

    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        if hasattr(obj, "from_user"):
            return obj.from_user.id in load_config().bot.admin_ids
        return False
