from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.callbackdata import cb
from loader import db


async def groups_keyboard(is_media_group=False):
    keyboard = InlineKeyboardMarkup(row_width=4)
    buttons = await db.get_groups()
    if is_media_group:
        for k, v in buttons.items():
            keyboard.insert(InlineKeyboardButton(text=v, callback_data=cb.new(f'mg_{k}')))
    else:
        for k, v in buttons.items():
            keyboard.insert(InlineKeyboardButton(text=v, callback_data=cb.new(k)))
    keyboard.add(InlineKeyboardButton(text='❌ cancel', callback_data=cb.new('cancel')))
    return keyboard


# getKeyboard2()
async def add_to_group_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    groups = await db.get_groups()
    for id, name in groups.items():
        keyboard.insert(
            InlineKeyboardButton(text=f"Add to {name}", callback_data=cb.new(f'add_to_{id}'))
        )

    keyboard.add(
        InlineKeyboardButton(text="Disregard ❌", callback_data=cb.new('disregard'))
    )
    return keyboard


# getKeyboard3():
request_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Request an access', callback_data='request_an_access')
        ]
    ]
)

# getKeyboard4():
yes_or_no_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Accept ✅', callback_data='accept'),
            InlineKeyboardButton(text='Reject ❌', callback_data=cb.new('reject'))
        ]
    ]
)