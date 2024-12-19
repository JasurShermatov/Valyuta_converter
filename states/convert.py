# states/convert.py
from aiogram.fsm.state import State, StatesGroup


class ConvertState(StatesGroup):
    waiting_for_second_currency = State()  # Ikkinchi valyutani kutish
    waiting_for_amount = State()  # Summani kutish
