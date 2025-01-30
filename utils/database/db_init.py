# utils/database/db_init.py
import logging
import psycopg2
import asyncio
from data.config import load_config

logger = logging.getLogger(__name__)
config = load_config()


async def init_db():
    logger.info("Starting database initialization...")
    conn = None
    try:
        # Database ga ulanish parametrlarini sozlaymiz
        conn_params = {
            "dbname": config.db.database,
            "user": config.db.user,
            "password": config.db.password,
            "host": config.db.host,
            "port": config.db.port,
        }
        logger.info(f"Trying to connect to database with params: {conn_params}")

        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        logger.info("Checking if 'users' table exists...")
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        users_table_exists = cur.fetchone()[0]

        if not users_table_exists:
            # Jadval mavjud bo'lmasa — yaratamiz
            logger.info("Creating 'users' table...")
            create_users_table_query = """
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE,
                    username VARCHAR(32),
                    full_name VARCHAR(128),
                    phone_number VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_premium BOOLEAN DEFAULT FALSE
                );
            """
            cur.execute(create_users_table_query)
            conn.commit()
            logger.info("'users' table created successfully!")
        else:
            logger.info("'users' table already exists. Skipping creation.")


        logger.info("Checking if 'subscription' table exists...")
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = 'subscription'
            );
        """)
        subscription_table_exists = cur.fetchone()[0]

        if not subscription_table_exists:
            # Jadval mavjud bo'lmasa — yaratamiz
            logger.info("Creating 'subscription' table...")
            create_subscription_table_query = """
                CREATE TABLE subscription (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    link VARCHAR(255) NOT NULL,
                    channel_id BIGINT UNIQUE
                );
            """
            cur.execute(create_subscription_table_query)
            conn.commit()
            logger.info("'subscription' table created successfully!")
        else:
            logger.info("'subscription' table already exists. Skipping creation.")

        #
        # Tekshirish (ixtiyoriy)
        #
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
        )
        table_exists = cur.fetchone()[0]
        if table_exists:
            logger.info("Verified: 'users' table exists in database.")
        else:
            logger.error("Table creation failed: 'users' table not found in database.")

        cur.close()
        return True

    except psycopg2.Error as e:
        logger.error(f"Database error occurred: {e}")
        return False
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")