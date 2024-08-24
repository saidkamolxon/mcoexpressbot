from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.db_api.postgresql import CoreSQL
from data.config import BOT_TOKEN
from utils.apis.fleet_locate import FleetLocate
from utils.apis.road_ready import RoadReady
from utils.apis.swift_eld import SwiftELD

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)
db = CoreSQL()
fl = FleetLocate(database=db)
rr = RoadReady(database=db)
sw = SwiftELD(database=db)
media = dict()
