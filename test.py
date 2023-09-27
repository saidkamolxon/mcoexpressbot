from datetime import datetime, timedelta
from aiogram import types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.aiogram_calendar import SimpleCalendar, simple_cal_callback
from pytz import timezone
from states.states import ScheduleMessageStates

from loader import dp, db

from keyboards.default.keyboards import *

scheduler = AsyncIOScheduler()
scheduler.timezone = timezone('US/Eastern')


@dp.message_handler(commands=['schedule'])
async def schedule_command(message: types.Message):
    await ScheduleMessageStates.WaitingForType.set()
    await message.answer('How would you like to schedule your message? Do you want it to be repeated or a one-off?',
                         reply_markup=await onetime_or_everytime())


@dp.message_handler(state=ScheduleMessageStates.WaitingForType)
async def define_type(message: types.Message, state: FSMContext):
    # await state.update_data()
    if message.text == "🕒 One-time":
        await message.answer("Please select a date: ", reply_markup=await SimpleCalendar().start_calendar())
    elif message.text == "🔁 Repeatable":
        await ScheduleMessageStates.WaitingForSequence.set()
        await message.answer('Select the sequence: ', reply_markup=await sequence_kb())


@dp.message_handler(state=ScheduleMessageStates.WaitingForSequence)
async def define_type(message: types.Message, state: FSMContext):
    await state.update_data()
    if message.text == "1️⃣ Daily":
        await ScheduleMessageStates.WaitingForTime.set()
        await message.answer('Now enter time (hour and minute) like 07:41')
    elif message.text == "7️⃣ Weekly":
        await ScheduleMessageStates.WaitingForWeekday.set()
        await message.answer('Enter weekday: ', reply_markup=await weekdays_kb())
    elif message.text == "3️⃣0️⃣ Monthly":
        pass


@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(date=date)
        await ScheduleMessageStates.WaitingForTime.set()
        await callback_query.message.answer('Now enter time (hour and minute) like 07:41')


# Create a table to store scheduled messages
await db.execute('''CREATE TABLE IF NOT EXISTS scheduled_messages
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date TEXT,
                   receivers TEXT,
                   message TEXT,
                   sender TEXT)''', commit=True)


@dp.message_handler(state=ScheduleMessageStates.WaitingForTime)
async def process_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    date = data.get('date')
    print(date)
    try:
        if len(message.text) == 4:
            hour, minute = int(message.text[0]), int(message.text[2:])
        else:
            hour, minute = int(message.text[:2]), int(message.text[3:])
        date = date + timedelta(hours=hour, minutes=minute)
        await state.update_data(date=date)
        await ScheduleMessageStates.WaitingForReceivers.set()
        await message.reply('Please provide the receivers (comma-separated)',reply_markup=await group_keyboards())
    except ValueError:
        await message.reply('Invalid date format. Please try again.')


@dp.message_handler(state=ScheduleMessageStates.WaitingForReceivers)
async def process_receivers(message: types.Message, state: FSMContext):
    receivers = message.text.split(',')
    await state.update_data(receivers=receivers)
    await ScheduleMessageStates.WaitingForMessage.set()
    await message.reply('Please enter the message you want to send', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=ScheduleMessageStates.WaitingForMessage)
async def process_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    date = data.get('date')
    receivers = data.get('receivers')
    await state.finish()
    # Insert the scheduled message into the database
    await db.execute("INSERT INTO scheduled_messages (date, receivers, message, sender) VALUES (?, ?, ?, ?)",
                   (date.strftime('%Y-%m-%d %H:%M:%S'), ','.join(receivers), message.html_text, message.from_user.full_name), commit=True)
    # Schedule the message
    scheduler.add_job(send_scheduled_message, 'date', run_date=date,
                      args=[message.chat.id, message.text, receivers, message.from_user.full_name])
    await message.answer(f'Your message has been scheduled successfully for {date} EDT!')


async def send_scheduled_message(chat_id, message_text, receivers, sender):
    # Send the message to all the receivers
    for receiver in receivers:
        await dp.bot.send_message(receiver.strip(), f'{message_text}\n\n<b>{sender}</b>')
    # Delete the scheduled message from the database
    await db.execute("DELETE FROM scheduled_messages WHERE message=?", (message_text,), commit=True)


# Load scheduled messages from the database and schedule them
rows = await db.execute("SELECT date, message, receivers, sender FROM scheduled_messages", fetchall=True)
for row in rows:
    date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
    message_text = row[1]
    receivers = row[2].split(',')
    sender = row[3]
    scheduler.add_job(send_scheduled_message, 'date', run_date=date,
                      args=[None, message_text, receivers, sender])

# Start the scheduler
scheduler.start()

# Start the bot
executor.start_polling(dp, skip_updates=True)
