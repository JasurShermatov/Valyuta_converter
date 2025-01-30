from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import asyncio
from typing import Tuple, Optional
from keyboards.inline.currency_kb import (
    create_currency_keyboard,
    create_convert_keyboard,
    create_result_keyboard,
    get_currency_emoji,
    SUPPORTED_CURRENCIES
)
from utils.currency_api import currency_api
import logging

logger = logging.getLogger(__name__)
router = Router()

# Add retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


class ConvertStates(StatesGroup):
    waiting_currencies = State()
    waiting_amount = State()


def validate_currency(currency: str) -> bool:
    """Valyuta kodini tekshirish"""
    return currency in SUPPORTED_CURRENCIES


async def format_converted_amount(amount: float) -> str:
    """Konvertatsiya natijasini formatlash"""
    try:
        if amount is None:
            return "0"
        if abs(amount) < 0.0001:
            return "{:.8f}".format(amount).rstrip("0").rstrip(".")
        return "{:,.4f}".format(amount).rstrip("0").rstrip(".")
    except Exception as e:
        logger.error(f"Formatlashda xatolik: {e}")
        return str(amount)


async def safe_api_call(
    func, *args, **kwargs
) -> Tuple[Optional[float], Optional[datetime]]:
    """API chaqiruvlarini xavfsiz amalga oshirish"""
    for attempt in range(MAX_RETRIES):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"API chaqiruvida xatolik: {e}")
                raise
            await asyncio.sleep(RETRY_DELAY)


async def process_conversion(
    amount: float, from_currency: str, to_currency: str
) -> tuple[str, str, datetime]:
    """Bir valyutani konvertatsiya qilish"""
    try:
        if not validate_currency(from_currency) or not validate_currency(to_currency):
            raise ValueError(
                f"Noto'g'ri valyuta kodi: {from_currency} yoki {to_currency}"
            )

        rate, update_time = await safe_api_call(
            currency_api.get_rate, from_currency, to_currency
        )

        if rate is None:
            raise ValueError(
                f"Valyuta kursi topilmadi: {from_currency} -> {to_currency}"
            )

        converted = amount * rate
        formatted_result = await format_converted_amount(converted)
        to_emoji = get_currency_emoji(to_currency)

        result_text = (
            f"{to_emoji} {formatted_result} {to_currency}\n"
            f"💱 Kurs: 1 {from_currency} = {rate:.4f} {to_currency}"
        )
        return result_text, "success", update_time
    except ValueError as e:
        logger.error(f"Konvertatsiya xatosi: {e}")
        return f"❌ {to_currency}: {str(e)}", "error", datetime.now()
    except Exception as e:
        logger.error(f"Kutilmagan xato: {e}")
        return f"❌ {to_currency}: Texnik xatolik yuz berdi", "error", datetime.now()


@router.callback_query(F.data.startswith("select_"))
async def select_base_currency(callback: CallbackQuery, state: FSMContext):
    try:
        currency = callback.data.split("_")[1]

        if not validate_currency(currency):
            raise ValueError(f"Noto'g'ri valyuta kodi: {currency}")

        emoji = get_currency_emoji(currency)
        await state.update_data(from_currency=currency, selected_currencies=[])

        await callback.message.edit_text(
            f"{emoji} {currency} tanlandi.\n"
            f"Qaysi valyutalarga konvertatsiya qilmoqchisiz?\n"
            f"Bir nechta valyutani tanlashingiz mumkin ✅",
            reply_markup=create_convert_keyboard(currency),
        )
        await state.set_state(ConvertStates.waiting_currencies)
    except Exception as e:
        logger.error(f"Valyuta tanlashda xato: {e}")
        await callback.message.edit_text(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring:",
            reply_markup=create_currency_keyboard(),
        )
        await state.clear()


@router.callback_query(F.data.startswith("toggle_"))
async def toggle_currency(callback: CallbackQuery, state: FSMContext):
    try:
        currency = callback.data.split("_")[1]
        if not validate_currency(currency):
            raise ValueError(f"Noto'g'ri valyuta kodi: {currency}")

        data = await state.get_data()
        from_currency = data.get("from_currency")

        if not from_currency:
            raise ValueError("Asosiy valyuta topilmadi")

        selected = data.get("selected_currencies", [])

        if currency in selected:
            selected.remove(currency)
        else:
            if len(selected) >= 10:  # Limit the number of selections
                await callback.answer(
                    "❌ Ko'pi bilan 10 ta valyuta tanlash mumkin", show_alert=True
                )
                return
            selected.append(currency)

        await state.update_data(selected_currencies=selected)

        text = (
            f"{get_currency_emoji(from_currency)} {from_currency} tanlandi.\n"
            f"Tanlangan valyutalar: {len(selected)} ta\n"
            f"Qaysi valyutalarga konvertatsiya qilmoqchisiz?"
        )
        await callback.message.edit_text(
            text, reply_markup=create_convert_keyboard(from_currency, selected)
        )
    except Exception as e:
        logger.error(f"Valyutani tanlash/bekor qilishda xato: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        await state.clear()


@router.callback_query(F.data == "calculate")
async def request_amount(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        selected = data.get("selected_currencies", [])
        from_currency = data.get("from_currency")

        if not from_currency:
            raise ValueError("Asosiy valyuta topilmadi")

        if not selected:
            await callback.answer("❌ Hech qanday valyuta tanlanmagan", show_alert=True)
            return

        emoji = get_currency_emoji(from_currency)
        text = (
            f"{emoji} {from_currency} dan konvertatsiya.\n"
            f"Tanlangan valyutalar: {len(selected)} ta\n\n"
            f"✍️ Summani kiriting:"
        )
        await callback.message.edit_text(text)
        await state.set_state(ConvertStates.waiting_amount)
    except Exception as e:
        logger.error(f"Hisoblash so'rovida xato: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        await state.clear()


@router.message(ConvertStates.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount_text = message.text.replace(",", ".").strip()
        try:
            amount = float(amount_text)
        except ValueError:
            await message.answer(
                "❌ Noto'g'ri summa kiritildi.\n"
                "Iltimos, faqat raqam kiriting.\n"
                "Masalan: 100 yoki 100.50"
            )
            return

        if amount <= 0:
            await message.answer("❌ Musbat son kiriting")
            return

        if amount > 99999999999999:
            await message.answer("❌ Juda katta summa kiritildi")
            return

        data = await state.get_data()
        from_currency = data.get("from_currency")
        selected_currencies = data.get("selected_currencies", [])

        if not from_currency or not selected_currencies:
            raise ValueError("Kerakli ma'lumotlar topilmadi")

        from_emoji = get_currency_emoji(from_currency)
        results = [f"{from_emoji} {amount:,.2f} {from_currency} = "]

        latest_update = None
        for to_currency in selected_currencies:
            result, status, update_time = await process_conversion(
                amount, from_currency, to_currency
            )
            results.append(result)
            if status == "success":
                latest_update = update_time

        time_info = (
            f"\n\n🕐 Yangilangan vaqt: {(latest_update + timedelta(hours=5)).strftime('%H:%M:%S')}"
            if latest_update
            else ""
        )
        message_text = (
            f"💱 Konvertatsiya natijasi:\n\n" + "\n\n".join(results) + time_info
        )

        await message.answer(message_text, reply_markup=create_result_keyboard())
        await state.clear()

    except Exception as e:
        logger.error(f"Konvertatsiyada xatolik: {e}")
        await message.answer(
            "❌ Konvertatsiya qilishda xatolik yuz berdi.\n"
            "Iltimos, qaytadan urinib ko'ring.",
            reply_markup=create_currency_keyboard(),
        )
        await state.clear()


@router.callback_query(F.data == "reset")
async def reset_conversion(callback: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        await callback.message.edit_text(
            "💱 Valyutani tanlang:", reply_markup=create_currency_keyboard()
        )
    except Exception as e:
        logger.error(f"Qayta boshlashda xato: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        await state.clear()
