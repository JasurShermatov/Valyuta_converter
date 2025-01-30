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
        # Database ga ulanish
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

        # Users table yaratish
        logger.info("Creating users table...")
        create_table_query = """
            CREATE TABLE IF NOT EXISTS users (
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

        cur.execute(create_table_query)
        conn.commit()
        logger.info("Users table created successfully!")

        # Subscription table yaratish
        logger.info("Creating subscription table...")
        create_subscription_table_query = """
            CREATE TABLE IF NOT EXISTS subscription (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                link VARCHAR(255) NOT NULL,
                channel_id BIGINT UNIQUE
            );
        """
        cur.execute(create_subscription_table_query)
        conn.commit()
        logger.info("Subscription table created successfully!")

        # Table yaratilganini tekshirish
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
        )
        table_exists = cur.fetchone()[0]
        if table_exists:
            logger.info("Verified: Users table exists in database")
        else:
            logger.error("Table creation failed: Users table not found in database")

        cur.close()
        return True

    except psycopg2.Error as e:
        logger.error(f"Database error occurred: {e}")
        return False
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")
