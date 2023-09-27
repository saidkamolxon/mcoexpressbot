from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.db_api.postgresql import CoreSQL
from data.config import BOT_TOKEN
from utils.fleet_config import Fleet, Swift

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = CoreSQL()
fl = Fleet()
sw = Swift()
media = dict()