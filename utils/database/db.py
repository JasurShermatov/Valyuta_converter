# utils/database/db.py
import logging
from datetime import datetime
import psycopg2
from aiogram.client import bot
from psycopg2.extras import DictCursor
from data.config import load_config

logger = logging.getLogger(__name__)


class DataBase:
    def __init__(self):
        self.config = load_config()
        # Debug level ga o'tkazamiz
        logger.setLevel(logging.DEBUG)

    async def get_connection(self):
        try:
            conn = psycopg2.connect(
                dbname=self.config.db.database,
                user=self.config.db.user,
                password=self.config.db.password,
                host=self.config.db.host,
                port=self.config.db.port,
            )
            logger.debug("Database connection established successfully")
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    async def count_users(self) -> int:
        """Jami foydalanuvchilar sonini qaytaradi"""
        conn = await self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
            count = cur.fetchone()[0]
            logger.debug(f"Total active users count: {count}")
            return count
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
        finally:
            conn.close()

    async def count_users_by_date(self, date: datetime.date) -> int:
        """Berilgan sanadagi yangi foydalanuvchilar sonini qaytaradi"""
        conn = await self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) = %s", (date,)
            )
            count = cur.fetchone()[0]
            logger.debug(f"Users count for date {date}: {count}")
            return count
        except Exception as e:
            logger.error(f"Error counting users by date: {e}")
            return 0
        finally:
            conn.close()

    async def get_all_users(self):
        """Barcha faol foydalanuvchilarni qaytaradi"""
        conn = await self.get_connection()
        try:
            cur = conn.cursor(cursor_factory=DictCursor)
            query = """
                SELECT * FROM users 
                WHERE is_active = TRUE 
                ORDER BY created_at DESC
            """
            logger.debug(f"Executing query: {query}")
            cur.execute(query)
            users = cur.fetchall()

            # Debug ma'lumotlari
            logger.debug(f"Found {len(users)} active users")
            for user in list(users)[:5]:  # Birinchi 5 ta foydalanuvchini log qilish
                logger.debug(
                    f"Sample user data - ID: {user['user_id']}, "
                    f"Username: {user['username']}, "
                    f"Active: {user['is_active']}"
                )

            return users
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []
        finally:
            conn.close()

    async def add_user(
        self,
        user_id: int,
        username: str = None,
        full_name: str = None,
        phone_number: str = None,
        is_premium: bool = False,
    ):
        """Yangi foydalanuvchi qo'shish"""
        conn = await self.get_connection()
        try:
            # Telefon raqamini tozalash
            cleaned_phone = None
            if phone_number:
                cleaned_phone = "".join(filter(str.isdigit, phone_number))
                if len(cleaned_phone) < 9:
                    cleaned_phone = None

            cur = conn.cursor()
            query = """
                INSERT INTO users (
                    user_id, username, full_name, phone_number, is_premium
                ) 
                VALUES (%s, %s, %s, %s, %s) 
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    full_name = EXCLUDED.full_name,
                    phone_number = CASE 
                        WHEN EXCLUDED.phone_number IS NOT NULL THEN EXCLUDED.phone_number
                        ELSE users.phone_number
                    END,
                    is_premium = CASE 
                        WHEN EXCLUDED.is_premium != users.is_premium THEN EXCLUDED.is_premium
                        ELSE users.is_premium
                    END,
                    last_active_at = CURRENT_TIMESTAMP
                RETURNING id
            """
            logger.debug(f"Adding/Updating user - ID: {user_id}, Username: {username}")
            cur.execute(
                query, (user_id, username, full_name, cleaned_phone, is_premium)
            )
            user_db_id = cur.fetchone()[0]
            conn.commit()
            logger.debug(f"Successfully added/updated user with DB ID: {user_db_id}")
            return user_db_id
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    async def update_user_activity(self, user_id: int):
        """Foydalanuvchi faolligini yangilash"""
        conn = await self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                UPDATE users 
                SET last_active_at = CURRENT_TIMESTAMP,
                    is_active = TRUE
                WHERE user_id = %s
            """
            cur.execute(query, (user_id,))
            rows_affected = cur.rowcount
            conn.commit()
            logger.debug(
                f"Updated activity for user {user_id}, rows affected: {rows_affected}"
            )
        except Exception as e:
            logger.error(f"Error updating activity for user {user_id}: {e}")
            conn.rollback()
        finally:
            conn.close()

    async def get_users_count_and_ids(self):
        """Foydalanuvchilar soni va ID larini olish (debug uchun)"""
        conn = await self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE is_active = TRUE")
            user_ids = [row[0] for row in cur.fetchall()]
            logger.debug(f"Active user IDs: {user_ids}")
            return len(user_ids), user_ids
        finally:
            conn.close()

    async def update_premium_status(self, user_id: int, is_premium: bool = True):
        """Foydalanuvchi premium statusini yangilash"""
        conn = await self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                UPDATE users 
                SET is_premium = %s,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                RETURNING id
            """
            cur.execute(query, (is_premium, user_id))
            conn.commit()
            success = cur.rowcount > 0
            if success:
                logger.debug(f"Premium status yangilandi: {user_id} -> {is_premium}")
            return success
        except Exception as e:
            logger.error(f"Premium statusni yangilashda xato {user_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    async def get_premium_users(self):
        """Premium foydalanuvchilarni olish"""
        conn = await self.get_connection()
        try:
            cur = conn.cursor(cursor_factory=DictCursor)
            query = """
                SELECT * FROM users 
                WHERE is_premium = TRUE AND is_active = TRUE 
                ORDER BY created_at DESC
            """
            cur.execute(query)
            users = cur.fetchall()
            logger.debug(f"Premium foydalanuvchilar soni: {len(users)}")
            return users
        except Exception as e:
            logger.error(f"Premium foydalanuvchilarni olishda xato: {e}")
            return []
        finally:
            conn.close()

    async def count_premium_users(self) -> int:
        """Premium foydalanuvchilar sonini olish"""
        conn = await self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE is_premium = TRUE AND is_active = TRUE"
            )
            count = cur.fetchone()[0]
            logger.debug(f"Premium foydalanuvchilar soni: {count}")
            return count
        except Exception as e:
            logger.error(f"Premium foydalanuvchilarni sanashda xato: {e}")
            return 0
        finally:
            conn.close()
