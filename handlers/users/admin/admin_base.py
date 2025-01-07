# from aiogram import Router, F
# from aiogram.types import Message, CallbackQuery
# from filters.admin import AdminFilter
# from utils.database.db import DataBase
# from keyboards.inline.channel_actions import get_delete_channel_keyboard
#
# router = Router()
# db = DataBase()
#
# # Kanal o'chirish funksiyasi
# @router.message(AdminFilter(), F.text == "➖ Kanal o'chirish")
# async def delete_channel(message: Message):
#     keyboard = await get_delete_channel_keyboard()
#     if not keyboard:
#         await message.answer("❌ Bazada kanallar mavjud emas!")
#         return
#
#     await message.answer(
#         "🗑 O'chirmoqchi bo'lgan kanalingizni tanlang:",
#         reply_markup=keyboard
#     )
#
# # Kanalni o'chirish jarayoni
# @router.callback_query(F.data.startswith("delete_channel:"))
# async def process_delete_channel(callback: CallbackQuery):
#     subscription_id = int(callback.data.split(":")[1])
#     try:
#         await db.delete_subscription(subscription_id)
#         await callback.answer("✅ Kanal muvaffaqiyatli o'chirildi!", show_alert=True)
#     except Exception as e:
#         await callback.answer(f"❌ Xatolik yuz berdi: {e}", show_alert=True)
#
#     new_keyboard = await get_delete_channel_keyboard()
#     if new_keyboard:
#         await callback.message.edit_text(
#             "🗑 O'chirmoqchi bo'lgan kanalingizni tanlang:",
#             reply_markup=new_keyboard
#         )
#     else:
#         await callback.message.edit_text("✅ Barcha kanallar o'chirildi!")
#
