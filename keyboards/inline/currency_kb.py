from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict

# Qo'llab-quvvatlanadigan valyutalar ro'yxati
SUPPORTED_CURRENCIES: List[str] = ["UZS", "RUB", "EUR", "GBP", "USD"]

# Valyuta emojilar
CURRENCY_EMOJIS: Dict[str, str] = {
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "GBP": "🇬🇧",
    "RUB": "🇷🇺",
    "UZS": "🇺🇿",
}


def get_currency_emoji(currency: str) -> str:

    return CURRENCY_EMOJIS.get(currency.upper(), "")


def create_currency_keyboard():

    kb = InlineKeyboardBuilder()

    for curr in SUPPORTED_CURRENCIES:
        emoji = get_currency_emoji(curr)
        kb.button(text=f"{emoji} {curr}".strip(), callback_data=f"select_{curr}")

    kb.adjust(1)  # Har bir qatorda 1 ta tugma
    return kb.as_markup()


def create_convert_keyboard(from_currency: str, selected_currencies: List[str] = None):

    if selected_currencies is None:
        selected_currencies = []

    kb = InlineKeyboardBuilder()
    available_currencies = [c for c in SUPPORTED_CURRENCIES if c != from_currency]

    # Valyutalarni chiqarish
    for curr in available_currencies:
        emoji = get_currency_emoji(curr)
        is_selected = curr in selected_currencies
        mark = "✅" if is_selected else ""

        kb.button(text=f"{emoji} {curr} {mark}".strip(), callback_data=f"toggle_{curr}")

    kb.button(text="🧮 Hisoblash", callback_data="calculate")

    kb.button(text="🔄 Qaytadan tanlash", callback_data="reset")

    buttons_count = len(available_currencies)
    layout = [1] * buttons_count + [2]
    kb.adjust(*layout)
    return kb.as_markup()


def create_result_keyboard():

    kb = InlineKeyboardBuilder()

    kb.button(text="🔄 Yangi konvertatsiya", callback_data="reset")

    return kb.as_markup()
