# handlers/users/admin/admin_base.py
from typing import Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from filters.admin import AdminFilter
from handlers.users.admin.admin import admin_panel
from utils.database.db import DataBase

router = Router()
db = DataBase()


@router.message(AdminFilter(), Command("admin"), StateFilter("*"))
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)
