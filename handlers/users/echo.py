from aiogram import types
from keyboards.inline.keyboards import groups_keyboard
from loader import dp, db


@dp.message_handler(content_types=types.ContentType.ANY)
async def echo(message: types.Message):
    if str(message.chat.id) in await db.get_users(only_admins=True):
        if message.content_type == [types.ContentType.TEXT]:
            await message.answer(message.html_text, reply_markup=await groups_keyboard())
        else:
            await message.copy_to(chat_id=message.chat.id, reply_markup=await groups_keyboard())
        await message.delete()
