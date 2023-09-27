from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loader import db


async def group_keyboards():
    groups = await db.get_groups()
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for group in groups.values():
        kb.insert(
            KeyboardButton(
                group
            )
        )
    return kb

async def onetime_or_everytime():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.insert(
        KeyboardButton(
            text="🕒 One-time"
        )
    )
    kb.insert(
        KeyboardButton(
            text="🔁 Repeatable"
        )
    )
    return kb

async def sequence_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.insert(
        KeyboardButton(
            text="1️⃣ Daily"
        )
    )
    kb.insert(
        KeyboardButton(
            text="7️⃣ Weekly"
        )
    )
    kb.insert(
        KeyboardButton(
            text="3️⃣0️⃣ Monthly"
        )
    )
    return kb


async def weekdays_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    for day in days:
        kb.insert(
            KeyboardButton(
                text=day
            )
        )
    return kb