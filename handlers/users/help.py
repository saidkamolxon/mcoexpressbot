from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from loader import dp


@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = ("<b>Commands: </b>",
            "/start - Restart",
            "/all_trl_info - Information about all trailers",
            "/lane_info - Information about asked lane",
            "/lanes_update - All lanes that have trailers",
            "/trailer_loc = Location of asked trailer"
            )
    await message.answer("\n".join(text))