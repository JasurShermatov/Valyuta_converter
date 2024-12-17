from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from data import config

# Initialize bot with HTML parse mode
bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
