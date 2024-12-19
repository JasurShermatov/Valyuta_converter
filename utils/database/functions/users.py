# utils/database/functions/users.py
import psycopg2
from datetime import datetime, timedelta
import pandas as pd
from data.config import load_config

config = load_config()


class DatabaseManager:
    @staticmethod
    async def get_connection():
        return psycopg2.connect(
            dbname=config.db.database,
            user=config.db.user,
            password=config.db.password,
            host=config.db.host,
            port=config.db.port,
        )

    @staticmethod
    async def add_user(
        user_id: int, username: str, full_name: str, phone_number: str = None
    ):
        conn = await DatabaseManager.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO users (user_id, username, full_name, phone_number)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    full_name = EXCLUDED.full_name,
                    phone_number = EXCLUDED.phone_number,
                    last_active_at = CURRENT_TIMESTAMP
                RETURNING id;
            """,
                (user_id, username, full_name, phone_number),
            )
            user_db_id = cur.fetchone()[0]
            conn.commit()
            return user_db_id
        except Exception as e:
            conn.rollback()
            print(f"Error adding user: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    async def update_user_activity(user_id: int):
        conn = await DatabaseManager.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE users 
                SET last_active_at = CURRENT_TIMESTAMP,
                    is_active = TRUE
                WHERE user_id = %s
            """,
                (user_id,),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error updating user activity: {e}")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    async def get_users_stats():
        conn = await DatabaseManager.get_connection()
        cur = conn.cursor()
        try:
            # Bugungi statistika
            today = datetime.now().date()
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today_users,
                    COUNT(CASE WHEN DATE(created_at) > CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as weekly_users,
                    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_users,
                    COUNT(CASE WHEN is_premium = TRUE THEN 1 END) as premium_users
                FROM users;
            """
            )
            stats = cur.fetchone()
            return {
                "total_users": stats[0],
                "today_users": stats[1],
                "weekly_users": stats[2],
                "active_users": stats[3],
                "premium_users": stats[4],
            }
        finally:
            cur.close()
            conn.close()

    @staticmethod
    async def export_users_to_excel():
        conn = await DatabaseManager.get_connection()
        try:
            # Ma'lumotlarni pandas DataFrame ga o'qish
            query = """
                SELECT 
                    id, user_id, username, full_name, phone_number, 
                    created_at, last_active_at, is_active, is_premium
                FROM users
                ORDER BY created_at DESC;
            """
            df = pd.read_sql_query(query, conn)

            # Excel file yaratish
            filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            writer = pd.ExcelWriter(f"data/files/{filename}", engine="xlsxwriter")

            # DataFrameni Excel ga yozish
            df.to_excel(writer, sheet_name="Users", index=False)

            # Excel file formatlash
            workbook = writer.book
            worksheet = writer.sheets["Users"]

            # Ustun kengliklari
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)

            writer.close()
            return filename
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return None
        finally:
            conn.close()
