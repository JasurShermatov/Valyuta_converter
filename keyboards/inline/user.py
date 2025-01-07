from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Profile", callback_data="profile"),
        InlineKeyboardButton(text="ℹ️ Help", callback_data="help"),
    )
    return builder.as_markup()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.config import load_config
from utils.database.db import DataBase

data = DataBase()


async def get_channel_keyboard():
    # Await the async method to get all subscriptions
    channels = await data.get_all_subscriptions()

    # Check if there are any channels in the database
    if not channels:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="No channels available", callback_data="no_channels"
                    )
                ],
            ]
        )

    # Dynamically create buttons for each channel
    inline_buttons = [
        [
            InlineKeyboardButton(
                text=f"✅ OBUNA BO'LISH - {channel['name']}", url=channel["link"]
            )
        ]
        for channel in channels
    ]

    # Add the "Check Subscription" button
    inline_buttons.append(
        [InlineKeyboardButton(text="♻️ TEKSHIRISH", callback_data="check_subscription")]
    )

    # Return the keyboard
    return InlineKeyboardMarkup(inline_keyboard=inline_buttons)


def get_confirmation_keyboard():
    confirmation_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ha, xohlayman!", callback_data="confirm_participation"
                )
            ]
        ]
    )
    return confirmation_keyboard
