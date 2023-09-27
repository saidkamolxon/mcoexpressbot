from data.config import OWNER_ID
from keyboards.inline.callbackdata import cb
from loader import dp, db, bot, media
from aiogram import types
from keyboards.inline.keyboards import yes_or_no_btn
from utils.send_messages import send_messages
from utils.common_functions import get_id
from utils.common_variables import sent_note
from utils.aiogram_calendar import simple_cal_callback, SimpleCalendar
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@dp.callback_query_handler(cb.filter(action=list(map(lambda x: f'gr_{x}', range(1, 10)))))
async def confirm_sending(query: types.CallbackQuery, callback_data: dict):
    action = callback_data.get('action')
    groups = await db.get_groups()
    chats = groups.get(action)
    if chats:
        confirm_markup = InlineKeyboardMarkup(row_width=1)
        confirm_markup.add(
            InlineKeyboardButton(f"✅ Confirm sending to {chats}", callback_data=cb.new(f"confirm_sending_to-{action}")),
            InlineKeyboardButton("❌ Cancel sending", callback_data=cb.new("cancel"))
        )
        await query.message.edit_reply_markup(reply_markup=confirm_markup)
    else:
        await query.answer(text='No chats found for this group.', show_alert=True)


@dp.callback_query_handler(cb.filter(action=list(map(lambda x: f'confirm_sending_to-gr_{x}', range(1, 10)))))
async def send_to_chats(query: types.CallbackQuery, callback_data: dict):
    action = callback_data.get('action').split("-")[-1]
    groups = await db.get_groups()
    chats = groups.get(action)
    await query.answer(text=f'Your message on its way...', show_alert=True)
    try:
        if query.message.content_type in [types.ContentType.TEXT]:
            await query.message.edit_text(text=f'{query.message.html_text}\n\n<code>{sent_note}{chats} -/-</code>')
        else:
            caption = query.message.parse_entities(
                query.message.caption) if query.message.caption is not None else str()
            await query.message.edit_caption(caption=f'{caption}\n\n<code>{sent_note}{chats} -/-</code>')
    except:
        await query.message.delete_reply_markup()
        await query.message.reply(text=f'<code>{sent_note}{chats} -/-</code>')
    await send_messages(chats, query.message)


@dp.callback_query_handler(cb.filter(action=list(map(lambda x: f'mg_gr_{x}', range(1, 10)))))
async def send_to_chats(query: types.CallbackQuery, callback_data: dict):
    action = str(callback_data.get('action'))[3:]
    groups = await db.get_groups()
    chats = groups.get(action)
    user_id = str(query.message.chat.id)
    await query.answer(text=f'Your message on its way...', show_alert=True)
    await send_messages(chats, query.message, True, media.get(user_id))
    media[user_id].clear()
    await query.message.edit_text(text=f'<code>{sent_note}{chats} -/-</code> ')


@dp.callback_query_handler(cb.filter(action=list(map(lambda x: f'add_to_gr_{x}', range(1, 10)))))
async def add_chat(query: types.CallbackQuery, callback_data: dict):
    order = callback_data.get('action').split('_')[-1]
    groups = await db.get_groups()
    chats = groups.get(f'gr_{order}')
    await query.answer(f'Added to {chats}...')
    _title, _id = await get_id(query.message.text)
    await db.add_to_chats(chats, chat_id=_id, chat_title=_title)
    await query.message.delete()


@dp.callback_query_handler(cb.filter(action=['cancel', 'disregard', 'reject']))
async def cancel(query: types.CallbackQuery, callback_data: dict):
    action = callback_data.get('action')
    await query.answer(f'{action}ed ❌'.capitalize())
    if action == 'reject':
        _name, _id = await get_id(query.message.text)
        await bot.send_message(chat_id=_id, text="Sorry, but your request has been <b>rejected</b> by admin.")
        await query.message.edit_text(f'{query.message.html_text}\n\n<b><em>Rejected ❌</em></b>')
    else:
        await query.message.delete()


@dp.callback_query_handler(text='request_an_access')
async def request_an_access(query: types.CallbackQuery):
    await query.answer(text="Request sended...")
    full_name = f'<b><a href="{query.from_user.url}">{query.from_user.full_name}</a></b>'
    user_id = query.from_user.id
    await bot.send_message(chat_id=OWNER_ID,
                           text=f'{full_name}\n{user_id}\nThis user is asking a permission to use this bot.',
                           reply_markup=yes_or_no_btn)
    await query.message.edit_text('Request has been sent...')


@dp.callback_query_handler(text='accept')
async def accept(query: types.CallbackQuery):
    await query.answer(text="Accepted...")
    _name, _id = await get_id(query.message.text)
    await db.add_to_users(user_id=_id, name=_name)
    await db.add_to_chats('teammates', _id, _name)
    await bot.send_message(chat_id=_id, text="Accepted ✅, now you can send me any message.")
    await query.message.edit_text(f'{query.message.html_text}\n\n<b><em>Accepted ✅</em></b>', parse_mode="HTML")


@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'You selected {date.strftime("%d/%m/%Y")}'
        )
