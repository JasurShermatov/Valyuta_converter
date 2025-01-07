from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.database.db import DataBase

db = DataBase()


# Ro'yxatni har 2 tadan bo'lib qaytaradigan funksiya
def chunk_list(values, chunk_size=2):
    return [values[i : i + chunk_size] for i in range(0, len(values), chunk_size)]


# Kanallarni o'chirish uchun inline tugmalarni yaratish
async def get_delete_channel_keyboard():
    """Bazadagi barcha kanallarni o'chirish uchun inline tugmalar."""
    channels = await db.get_all_subscriptions()

    if not channels:
        return None

    # Kanallarni InlineKeyboardButton formatiga o'zgartiramiz
    buttons = [
        InlineKeyboardButton(
            text=f"❌ {channel['name']}",
            callback_data=f"delete_channel:{channel['id']}",
        )
        for channel in channels
    ]

    # 2 tadan qatorlarga ajratib InlineKeyboardMarkup ga joylaymiz
    keyboard = InlineKeyboardMarkup(inline_keyboard=chunk_list(buttons, chunk_size=2))

    return keyboard
