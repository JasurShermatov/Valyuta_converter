# handlers/users/admin/admin.py
import os
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from filters.admin import AdminFilter
from keyboards.default.admin_kb import admin_keyboard
from utils.database.db import DataBase
import pandas as pd
from openpyxl.styles import Font, PatternFill

router = Router()
db = DataBase()

# 'data/files' papkasini yaratish
os.makedirs("data/files", exist_ok=True)


@router.message(Command("admin"))
async def admin_panel(message: Message):
    # Admin ekanligini tekshirish
    if not await AdminFilter()(message):
        await message.answer("Bu buyruq faqat adminlar uchun!")
        return

    await message.answer(
        "👋 Admin panel:\n\n" "🔍 Quyidagi funksiyalardan foydalanishingiz mumkin:",
        reply_markup=admin_keyboard,
    )


@router.message(AdminFilter(), F.text == "📊 Statistika")
async def show_statistics(message: Message):
    try:
        # Asosiy statistikalar
        total_users = await db.count_users()
        today_users = await db.count_users_by_date(datetime.now().date())

        # So'nggi 7 kunlik statistika
        weekly_stats = []
        for i in range(7):
            date = datetime.now().date() - pd.Timedelta(days=i)
            count = await db.count_users_by_date(date)
            if count > 0:
                weekly_stats.append(f"📅 {date.strftime('%d.%m.%Y')}: +{count}")

        stats = [
            "📊 Bot statistikasi\n",
            f"👥 Jami foydalanuvchilar: {total_users:,} ta",
            f"📅 Bugun qo'shilganlar: {today_users} ta\n",
            "📈 So'nggi 7 kunlik statistika:",
            *weekly_stats,
        ]

        await message.answer("\n".join(stats))

    except Exception as e:
        print(f"Error showing statistics: {e}")
        await message.answer("❌ Statistikani olishda xatolik yuz berdi")


@router.message(AdminFilter(), F.text == "📥 Users Excel")
async def get_users_excel(message: Message):
    await message.answer("📊 Excel fayl tayyorlanmoqda...")

    try:
        users = await db.get_all_users()
        if not users:
            await message.answer("❌ Foydalanuvchilar topilmadi")
            return

        # Ma'lumotlarni list of dict ko'rinishiga o'tkazamiz
        users_data = []
        for user in users:
            try:
                users_data.append(
                    {
                        "ID": user["id"] if "id" in user else "",
                        "Telegram ID": user["user_id"] if "user_id" in user else "",
                        "Username": user["username"] if "username" in user else "",
                        "To'liq ismi": user["full_name"] if "full_name" in user else "",
                        "Telefon raqami": (
                            user["phone_number"] if "phone_number" in user else ""
                        ),
                        "Ro'yxatdan o'tgan vaqti": (
                            user["created_at"] if "created_at" in user else ""
                        ),
                        "Oxirgi faolligi": (
                            user["last_active_at"] if "last_active_at" in user else ""
                        ),
                        "Holati": (
                            "Faol" if user.get("is_active", False) else "Faol emas"
                        ),
                        "Premium": "Ha" if user.get("is_premium", False) else "Yo'q",
                    }
                )
            except Exception as e:
                print(f"Error processing user data: {e}")
                continue

        df = pd.DataFrame(users_data)

        # Excel fayl nomi
        filename = f"users_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
        filepath = f"data/files/{filename}"

        # Excel faylni yaratish
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Foydalanuvchilar", index=False)

            workbook = writer.book
            worksheet = writer.sheets["Foydalanuvchilar"]

            # Ustun kengliklarini moslash
            for idx, col in enumerate(df.columns):
                max_length = (
                    max(df[col].astype(str).apply(len).max(), len(str(col))) + 2
                )
                worksheet.column_dimensions[
                    worksheet.cell(1, idx + 1).column_letter
                ].width = max_length

            # Sarlavhalarni formatlash
            for cell in worksheet[1]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(
                    start_color="CCE5FF", end_color="CCE5FF", fill_type="solid"
                )

        # Faylni yuborish
        if os.path.exists(filepath):
            excel_file = FSInputFile(filepath)
            await message.answer_document(
                document=excel_file,
                caption=(
                    f"📊 Bot foydalanuvchilari ro'yxati:\n"
                    f"📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                    f"👥 Jami: {len(users):,} ta foydalanuvchi"
                ),
            )
        else:
            raise FileNotFoundError(f"Excel file not found at {filepath}")

    except Exception as e:
        print(f"Error creating Excel file: {e}")
        await message.answer("❌ Excel fayl yaratishda xatolik yuz berdi")


@router.message(AdminFilter(), F.text == "⬅️ Orqaga")
async def back_handler(message: Message, state: FSMContext):
    # FSM holatini tozalash
    await state.clear()

    # Admin paneldan chiqishni bildirish
    await message.answer("Siz admin  siz sizga admin panel korinib turadi")
