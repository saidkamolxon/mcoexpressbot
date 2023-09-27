from aiogram_media_group import media_group_handler
from aiogram.dispatcher.filters import MediaGroupFilter
from typing import List
from data.config import BOT_USERNAME, OWNER_ID
from aiogram.types import Message, ContentType
from keyboards.inline.keyboards import groups_keyboard, add_to_group_keyboard, request_btn
from loader import dp, db, media
from utils.common_functions import is_file_typed, get_media_file, get_caption, input_media_by_type
from utils.common_variables import cant_use_note


@dp.message_handler(content_types=ContentType.NEW_CHAT_MEMBERS)
async def new_group_member(message: Message):
    if BOT_USERNAME in [new_member.username for new_member in message.new_chat_members]:
        who_added = str(message.from_user.id)
        acceptance = f'{message.chat.title}\n<code>{message.chat.id}</code>\nBot was invited to this group.' + \
                     'Decide what to do:'
        if who_added in await db.get_users():
            try:
                await dp.bot.send_message(chat_id=who_added, text=acceptance,
                                          reply_markup=await add_to_group_keyboard())
            except:
                await dp.bot.send_message(chat_id=OWNER_ID, text=acceptance, reply_markup=await add_to_group_keyboard())
        else:
            await dp.bot.send_message(chat_id=OWNER_ID, text=acceptance, reply_markup=await add_to_group_keyboard())


@dp.message_handler(content_types=ContentType.LEFT_CHAT_MEMBER)
async def left_group_member(message: Message):
    who_removed = f'<a href="{message.from_user.url}">{message.from_user.full_name}</a>'
    chat_id = str(abs(message.chat.id))
    if len(chat_id) > 10 and chat_id[:3] == '100':
        chat_id = chat_id[3:]
    chat = f'<a href="https://t.me/c/{chat_id}/">{message.chat.title}</a>'

    if BOT_USERNAME == message.left_chat_member.username:
        await dp.bot.send_message(chat_id=OWNER_ID, text=f'Bot was removed from <b>{chat}</b> by <b>{who_removed}</b>.')
        await db.remove_from_all_chats(str(message.chat.id))


@dp.message_handler(MediaGroupFilter(is_media_group=True), content_types=ContentType.ANY)
@media_group_handler
async def album_handler(msgs: List[Message]):
    if str(msgs[0].chat.id) in await db.get_users(only_admins=True):
        user_media = list()
        if not is_file_typed(msgs[0]):
            user_media.append(input_media_by_type(msgs[0])(media=get_media_file(msgs[0]), caption=get_caption(msgs[0]),
                                                           caption_entities=msgs[0].caption_entities))
            for m in msgs[1:]:
                user_media.append(input_media_by_type(m)(media=get_media_file(m)))
        else:
            for m in msgs[:-1]:
                user_media.append(input_media_by_type(m)(media=get_media_file(m), caption=m.caption,
                                                         caption_entities=m.caption_entities))
            user_media.append(
                input_media_by_type(msgs[-1])(media=get_media_file(msgs[-1]), caption=get_caption(msgs[-1]),
                                              caption_entities=msgs[-1].caption_entities))
        media[str(msgs[0].from_user.id)] = user_media
        await msgs[0].reply(text='Now please choose on of the group of chats:',
                            reply_markup=await groups_keyboard(is_media_group=True))