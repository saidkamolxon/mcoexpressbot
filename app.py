from aiogram import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from loader import dp, db
import middlewares, filters, handlers
from utils.scheduled_messages import monday_mileage
from utils import on_startup_notify, on_shutdown_notify, set_default_commands
# from utils import set_default_commands


async def on_startup(dispatcher):
    # Birlamchi komandalar (/star va /help)
    await set_default_commands(dispatcher)

    # Databazani ishga tushirish
    try:
        await db.create()
        await db.create_table_users()
    except:
        pass

    # Bot ishga tushgani haqida adminga xabar berish
    await on_startup_notify(dispatcher)


async def on_shutdown(dispatcher):
    await on_shutdown_notify(dispatcher)


cron = CronTrigger(day_of_week='MON', hour=7)
sch = AsyncIOScheduler()
sch.start()
sch.add_job(monday_mileage, trigger=cron)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
