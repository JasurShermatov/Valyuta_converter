# data.config
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: int
    sqlalchemy_database_url: str  # Adding a URL for SQLAlchemy


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    channel_id: str  # Telegram Channel ID
    use_redis: bool = False


@dataclass
class Config:
    bot: TgBot
    db: DbConfig


def load_config() -> Config:
    admin_ids_str = os.getenv("ADMIN_IDS", "").split(",")
    admin_ids = [
        int(admin_id.strip()) for admin_id in admin_ids_str if admin_id.strip()
    ]

    # Create a PostgreSQL connection URL for SQLAlchemy
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASS", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "postgres")
    db_port = os.getenv(
        "DB_PORT", "5432"
    )  # Note: Changed "PORT" to "DB_PORT" to avoid conflicts with other apps
    sqlalchemy_database_url = (
        f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )

    return Config(
        bot=TgBot(
            token=os.getenv("BOT_TOKEN"),
            admin_ids=admin_ids,
            channel_id=os.getenv("CHANNEL_ID"),
            use_redis=os.getenv("USE_REDIS", "False").lower() == "true",
        ),
        db=DbConfig(
            host=db_host,
            password=db_pass,
            user=db_user,
            database=db_name,
            port=int(db_port),
            sqlalchemy_database_url=sqlalchemy_database_url,  # Include this in the DbConfig
        ),
    )
