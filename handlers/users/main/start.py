from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.database.db import DataBase
from keyboards.inline.user import get_channel_keyboard
from data.config import load_config
from middlewares.checksub import CheckSubscriptionMiddleware
from keyboards.inline.currency_kb import create_currency_keyboard

router = Router()
db = DataBase()
config = load_config()


# Start handler
@router.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    await db.add_user(
        user_id=user_id, username=username, full_name=full_name, is_premium=False
    )

    is_subscribed = await CheckSubscriptionMiddleware().check_all_subscriptions(
        user_id, message.bot
    )
    if not is_subscribed:
        await message.answer(
            "Iltimos, botdan foydalanish uchun avval kanalga obuna bo'ling.",
            reply_markup=await get_channel_keyboard(),
        )
    else:
        await show_main_menu(message)


# Confirmation and subscription check
@router.callback_query(F.data == "confirm_subscription")
async def confirm_subscription_handler(callback: CallbackQuery):
    is_subscribed = await CheckSubscriptionMiddleware().check_all_subscriptions(
        callback.from_user.id, callback.bot
    )
    if is_subscribed:
        await callback.message.edit_text(
            "Obuna tasdiqlandi! Endi botni to'liq ishlatishingiz mumkin."
        )
        await show_main_menu(callback.message)
    else:
        await callback.answer("Iltimos, avval kanalga obuna bo'ling!", show_alert=True)


@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery):
    is_subscribed = await CheckSubscriptionMiddleware().check_all_subscriptions(
        callback.from_user.id, callback.bot
    )
    if not is_subscribed:
        await callback.answer("Siz kanalga a'zo bo'lmagansiz!", show_alert=True)
    else:
        await show_main_menu(callback.message)


async def show_main_menu(message: Message):
    await message.answer(
        f"👋 Assalomu alaykum, {message.from_user.first_name}\n"
        f"Valyuta konvertatsiya botiga xush kelibsiz!\n\n"
        f"💱 Quyidagi valyutalardan birini tanlang:\n\n"
        f"✅ Bir vaqtning o'zida bir nechta valyutaga konvertatsiya qilishingiz mumkin!",
        reply_markup=create_currency_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "🔰 Bot imkoniyatlari:\n\n"
        "1. Valyutalarni tanlang\n"
        "2. Bir nechta valyutani bir vaqtda tanlash mumkin ✅\n"
        "3. Summani kiriting va natijani oling 🧮\n\n"
        "📊 Kurslar CBU.uz dan olinadi va har 5 daqiqada yangilanib turadi.\n"
        "📬 Har kuni ertalab soat 7:30 da joriy kurslar sizga yuboriladi.\n\n"
        "🔄 Qaytadan boshlash uchun /start buyrug'ini yuboring\n"
        "❓ Yordam uchun /help buyrug'ini yuboring"
    )
    await message.answer(help_text)


@router.callback_query(F.data == "back_to_main")
@router.callback_query(F.data == "reset")
async def reset_conversion(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "💱 Quyidagi valyutalardan birini tanlang:\n\n"
        "ℹ️ Tanlangan valyutadan boshqa valyutalarga konvertatsiya qilish mumkin.\n"
        "✅ Bir vaqtning o'zida bir nechta valyutaga konvertatsiya qilish imkoniyati mavjud.",
        reply_markup=create_currency_keyboard(),
    )
