from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from loader import dp, db


@dp.message_handler(CommandStart(), state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=True)
    if str(message.from_user.id) in await db.get_users(only_admins=True):
        await message.reply(f"Assalomu alaykum, {message.from_user.first_name}." +
                            " Send me anything, I will copy it to the appropriate chats")
    else:
        await message.reply(f"Assalomu alaykum, {message.from_user.first_name}." +
                            " You can ask me for the current status of the landmarks and the assets")
