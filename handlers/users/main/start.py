# handlers/users/main/start.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.database.db import DataBase
from keyboards.inline.currency_kb import (
    create_currency_keyboard,
    get_currency_emoji,
)

router = Router()
db = DataBase()

@router.message(Command("start"))
async def start_handler(message: Message):
    # Foydalanuvchini bazaga qo'shish
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    await db.add_user(
        user_id=user_id,
        username=username,
        full_name=full_name
    )

    await message.answer(
        text=(
            f"👋 Assalomu alaykum, {message.from_user.first_name}\n"
            f"Valyuta konvertatsiya botiga xush kelibsiz!\n\n"
            f"💱 Quyidagi valyutalardan birini tanlang:\n\n"
            f"✅ Bir vaqtning o'zida bir nechta valyutaga konvertatsiya qilishingiz mumkin!."
        ),
        reply_markup=create_currency_keyboard()
    )

@router.message(Command("help"))
async def help_command(message: Message):
    """Yordam ko'rsatish"""
    help_text = (
        "🔰 Bot imkoniyatlari:\n\n"
        "1. Valyutalarni tanlang\n"
        "2. Bir nechta valyutani bir vaqtda tanlash mumkin ✅\n"
        "3. Summani kiriting va natijani oling 🧮\n\n"
        "📊 Kurslar NBU.uz dan olinadi va har 5 daqiqada yangilanib turadi.\n"
        "📬 Har kuni ertalab soat 11:36 da joriy kurslar sizga yuboriladi.\n\n"
        "🔄 Qaytadan boshlash uchun /start buyrug'ini yuboring\n"
        "❓ Yordam uchun /help buyrug'ini yuboring"
    )
    await message.answer(help_text)

@router.callback_query(F.data == "back_to_main")
@router.callback_query(F.data == "reset")
async def reset_conversion(callback: CallbackQuery, state: FSMContext):
    """Bosh menyuga qaytish"""
    await state.clear()
    await callback.message.edit_text(
        "💱 Quyidagi valyutalardan birini tanlang:\n\n"
        "ℹ️ Tanlangan valyutadan boshqa valyutalarga konvertatsiya qilish mumkin.\n"
        "✅ Bir vaqtning o'zida bir nechta valyutaga konvertatsiya qilish imkoniyati mavjud.",
        reply_markup=create_currency_keyboard()
    )