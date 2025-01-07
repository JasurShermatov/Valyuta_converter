# keyboards/default/admin_kb.py
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from utils.database.db import DataBase

data = DataBase()


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📥 Users Excel")],
        [
            KeyboardButton(text="➕ Kanal qo'shish"),
            KeyboardButton(text="➖ Kanal o'chirish"),
        ],
        [
            KeyboardButton(text="📋 Kanallar ro'yxati"),
            KeyboardButton(text="📨 Xabar yuborish"),
        ],
        [KeyboardButton(text="⬅️ Orqaga")],
    ],
    resize_keyboard=True,
)


# Kichik listlarga ajratish funksiyasi
def chunk_list(values, chunk_size=2):
    """Ro'yxatni har chunk_size ta elementdan ajratadi."""
    return [values[i : i + chunk_size] for i in range(0, len(values), chunk_size)]


# Kanallar uchun inline tugmalar yaratish funksiyasi
async def channels_button():
    buttons = await data.get_all_subscriptions()

    if not buttons:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Kanallar hali mavjud emas", callback_data="kanallar"
                    )
                ]
            ]
        )

    # Kanallarni tugmalar shaklida yaratamiz
    button_list = [
        InlineKeyboardButton(text=button["name"], callback_data=button["name"])
        for button in buttons
    ]

    # Tugmalarni 2 tadan ajratib InlineKeyboardMarkup ga joylaymiz
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=chunk_list(button_list, chunk_size=2)
    )

    return keyboard
