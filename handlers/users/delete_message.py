from aiogram import types
from keyboards.inline.keyboards import groups_keyboard
from loader import dp, bot

#
# @dp.message_handler(content_types=types.ContentType.ANY)
# async def echo(message: types.Message):
#     if message.forward_from.id == (await bot.me).id:
#         await bot.delete_message(chat_id=-921608850, message_id=message.message_id)
