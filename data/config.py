# data/config.py
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# .env faylini o'qish
load_dotenv()


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: int


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]  # Qo'shildi
    use_redis: bool = False


@dataclass
class Config:
    bot: TgBot
    db: DbConfig


def load_config():
    # Admin IDlarni olish
    admin_ids_str = os.getenv("ADMIN_IDS", "").split(",")
    admin_ids = [
        int(admin_id.strip()) for admin_id in admin_ids_str if admin_id.strip()
    ]

    return Config(
        bot=TgBot(
            token=os.getenv("BOT_TOKEN"),
            admin_ids=admin_ids,  # Qo'shildi
            use_redis=os.getenv("USE_REDIS", "False").lower() == "true",
        ),
        db=DbConfig(
            host=os.getenv("DB_HOST", "localhost"),
            password=os.getenv("DB_PASS", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            database=os.getenv("DB_NAME", "postgres"),
            port=int(os.getenv("PORT", 5432)),
        ),
    )
