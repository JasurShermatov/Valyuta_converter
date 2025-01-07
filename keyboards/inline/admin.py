# keyboards/inline/admin.py

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.database.db import DataBase


def admin_main_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
        InlineKeyboardButton(text="📤 Xabar yuborish", callback_data="admin_broadcast"),
    )
    keyboard.adjust(1)
    return keyboard.as_markup()


def admin_back_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back"))
    return keyboard.as_markup()


# filters/admin.py
from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from data.config import load_config


class AdminFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        config = load_config()
        user_id = (
            event.from_user.id if isinstance(event, Message) else event.from_user.id
        )
        return user_id in config.bot.admin_ids


router = Router()


@router.message(AdminFilter(), Command("admin"))
@router.callback_query(AdminFilter(), F.data == "admin_back")
async def show_admin_panel(event: Union[Message, CallbackQuery], state: FSMContext):
    await state.clear()

    # Database instance
    db = DataBase()

    try:
        total_users = await db.count_users()
        today = datetime.now().date()
        today_users = await db.count_users_by_date(today)

        text = [
            f"👋 Admin panel\n",
            f"📊 Statistika:\n",
            f"👤 Jami foydalanuvchilar: {total_users:,}",
            f"🆕 Bugun qo'shilganlar: {today_users:,}",
        ]

        if isinstance(event, CallbackQuery):
            await event.message.edit_text(
                "\n".join(text), reply_markup=admin_main_menu()
            )
        else:
            await event.answer("\n".join(text), reply_markup=admin_main_menu())

    except Exception as e:
        error_text = "Xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        print(f"Error in admin panel: {e}")
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(error_text)
        else:
            await event.answer(error_text)


@router.callback_query(AdminFilter(), F.data == "admin_stats")
async def show_statistics(callback: CallbackQuery):
    db = DataBase()

    try:
        total_users = await db.count_users()
        today = datetime.now().date()

        # Last 7 days statistics
        weekly_stats = []
        for i in range(7):
            date = today - timedelta(days=i)
            count = await db.count_users_by_date(date)
            if count > 0:
                weekly_stats.append(f"📅 {date.strftime('%d.%m.%Y')}: +{count}")

        text = [
            "📊 Bot statistikasi\n",
            f"👥 Jami foydalanuvchilar: {total_users:,}",
            f"\n📈 So'nggi 7 kun:",
            *weekly_stats,
        ]

        await callback.message.edit_text(
            "\n".join(text), reply_markup=admin_back_menu()
        )
    except Exception as e:
        print(f"Error in statistics: {e}")
        await callback.answer("Statistikani olishda xatolik yuz berdi", show_alert=True)
