# handlers/users/admin/admin_broadcast.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from filters.admin import AdminFilter
from keyboards.inline.admin import admin_back_menu

router = Router()


class BroadcastStates(StatesGroup):
    waiting_message = State()


@router.callback_query(AdminFilter(), F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastStates.waiting_message)
    await callback.message.edit_text(
        "📤 Yubormoqchi bo'lgan xabaringizni yuboring.\n\n"
        "❌ Bekor qilish uchun /cancel buyrug'ini yuboring.",
        reply_markup=admin_back_menu(),
    )


@router.message(BroadcastStates.waiting_message)
async def process_broadcast(message: Message, state: FSMContext):
    db = DataBase()

    # Foydalanuvchilar ro'yxatini olish
    users = await db.get_all_users()

    sent = 0
    failed = 0

    status_message = await message.answer("⏳ Xabar yuborish boshlandi...")

    for user in users:
        try:
            await message.copy_to(user.user_id)
            sent += 1

            if sent % 25 == 0:  # Har 25 ta yuborilganda statusni yangilash
                await status_message.edit_text(
                    f"⏳ Jarayon davom etmoqda:\n"
                    f"✅ Yuborildi: {sent}\n"
                    f"❌ Xato: {failed}"
                )
        except Exception as e:
            failed += 1
            print(f"Error sending message to {user.user_id}: {e}")

    await status_message.edit_text(
        f"✅ Xabar yuborish yakunlandi:\n\n"
        f"👥 Jami foydalanuvchilar: {len(users)}\n"
        f"✅ Muvaffaqiyatli: {sent}\n"
        f"❌ Muvaffaqiyatsiz: {failed}"
    )
    await state.clear()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    async def get_delete_channel_keyboard():
        """Bazadagi barcha kanallarni o'chirish uchun inline tugmalar."""
        channels = await db.get_all_subscriptions()

        if not channels:
            return None

        builder = InlineKeyboardBuilder()
        for channel in channels:
            builder.add(
                InlineKeyboardButton(
                    text=f"❌ {channel['name']}",
                    callback_data=f"delete_channel:{channel['id']}",
                )
            )

        builder.adjust(1)  # Bir qatorga bitta tugma
        return builder.as_markup()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.database.db import DataBase

db = DataBase()


async def get_delete_channel_keyboard():
    """Bazadagi barcha kanallarni o'chirish uchun inline tugmalar."""
    channels = await db.get_all_subscriptions()

    if not channels:
        return None

    inline_buttons = [
        InlineKeyboardButton(
            text=f"❌ {channel['name']}",
            callback_data=f"delete_channel:{channel['id']}",
        )
        for channel in channels
    ]

    return InlineKeyboardMarkup(inline_keyboard=[inline_buttons])
