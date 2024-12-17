# handlers/users/admin/admin_spams.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from filters.admin import AdminFilter
from utils.database.db import DataBase
from datetime import datetime

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
    sent = 0
    errors = 0

    status_msg = await message.answer(
        "📤 Xabar yuborish boshlandi...\n\n" f"📊 Jami foydalanuvchilar: {all_users} ta"
    )

    for user in users:
        try:
            # Har qanday turdagi xabarni yuborish
            await message.copy_to(user["user_id"])
            sent += 1

            # Har 10 ta yuborilgandan keyin statusni yangilash
            if sent % 10 == 0:
                success_rate = (sent / all_users) * 100
                await status_msg.edit_text(
                    f"📤 Xabar yuborish davom etmoqda...\n\n"
                    f"📊 Progress: {sent}/{all_users} ({success_rate:.1f}%)\n"
                    f"✅ Yuborildi: {sent} ta\n"
                    f"❌ Xato: {errors} ta"
                )
        except Exception as e:
            errors += 1
            print(f"Error sending message to user {user['user_id']}: {e}")

    # Yakuniy statistika
    success_rate = (sent / all_users) * 100 if all_users > 0 else 0
    error_rate = (errors / all_users) * 100 if all_users > 0 else 0

    await status_msg.edit_text(
        f"✅ Xabar yuborish yakunlandi!\n\n"
        f"📊 Statistika:\n"
        f"👥 Jami foydalanuvchilar: {all_users} ta\n"
        f"✅ Muvaffaqiyatli yuborildi: {sent} ta ({success_rate:.1f}%)\n"
        f"❌ Xatolik yuz berdi: {errors} ta ({error_rate:.1f}%)\n\n"
        f"🕐 Yakunlangan vaqt: {datetime.now().strftime('%H:%M:%S')}"
    )

    await state.clear()


# Xabarni bekor qilish uchun handler
@router.message(Command("cancel"), BroadcastStates.waiting_message)
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Xabar yuborish bekor qilindi")
