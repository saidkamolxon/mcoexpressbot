import logging
from aiogram.types import Update
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from keyboards.inline.keyboards import request_btn
from utils.common_variables import cant_use_note
from loader import db


class CheckUser(BaseMiddleware):
    async def on_pre_process_update(self, update: Update, data: dict):
        chat_id = 0
        is_command = False
        if update.message:
            user = update.message.from_user.id
            is_command = update.message.is_command()
            chat_id = update.message.chat.id
        elif update.callback_query:
            if update.callback_query.data == 'request_an_access':
                return
            user = update.callback_query.from_user.id
        else:
            return
        logging.info(user)
        # if chat_id > 0:
        if str(user) not in await db.get_users() and is_command:
            try:
                if chat_id > 0:
                    await update.message.answer(cant_use_note, reply_markup=request_btn)
            except:
                await update.callback_query.answer(cant_use_note)
            raise CancelHandler()
