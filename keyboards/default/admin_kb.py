# keyboards/default/admin_kb.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="📨 Xabar yuborish"),
        ],
        [KeyboardButton(text="📥 Users Excel"), KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)
