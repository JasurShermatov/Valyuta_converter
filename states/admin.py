from aiogram.fsm.state import StatesGroup, State


class ChannelAdding(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_channel_name = State()


class ChannelModification(StatesGroup):
    waiting_for_new_id = State()
    waiting_for_new_name = State()


class TestAdding(StatesGroup):
    waiting_for_test_name = State()
    waiting_for_test_answer_key = State()
    waiting_for_test_document = State()
