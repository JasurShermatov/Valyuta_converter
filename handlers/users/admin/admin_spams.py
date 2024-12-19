# handlers/users/admin/admin_spams.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from filters.admin import AdminFilter
from utils.database.db import DataBase
from datetime import datetime
import asyncio

router = Router()
db = DataBase()


class BroadcastStates(StatesGroup):
    waiting_message = State()


@router.message(AdminFilter(), F.text == "📨 Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    await message.answer(
        "✍️ Yubormoqchi bo'lgan xabaringizni yuboring.\n"
        "🔔 Barcha turdagi xabarlarni yuborishingiz mumkin "
        "(Matn, rasm, video, audio va boshqalar)\n\n"
        "❌ Bekor qilish uchun /cancel buyrug'ini yuboring."
    )
    await state.set_state(BroadcastStates.waiting_message)


@router.message(AdminFilter(), BroadcastStates.waiting_message)
async def process_broadcast(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Xabar yuborish bekor qilindi")
        return

    users = await db.get_all_users()
    all_users = len(users)

    status_msg = await message.answer(
        "📤 Xabar yuborish boshlandi...\n\n"
        f"📊 Jami foydalanuvchilar: {all_users} ta"
    )

    for user in users:
        try:
            # Har qanday turdagi xabarni yuborish
            await message.copy_to(user["user_id"])
            await asyncio.sleep(0.05)  # Anti-flood
        except Exception as e:
            continue

    await status_msg.edit_text("✅ Xabar yuborish yakunlandi!")
    await state.clear()


@router.message(Command("cancel"), BroadcastStates.waiting_message)
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Xabar yuborish bekor qilindi")