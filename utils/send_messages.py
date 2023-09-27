import asyncio
from aiogram.types import Message, ContentType
from loader import dp, db


async def send_messages(gr_chats: str, message: Message, is_media_group=False, media: dict = None) -> None:
    if media is None:
        media = dict()
    chats: dict = await db.get_chats(gr_chats)
    if chats == -1:
        await message.reply('Not found any chat in this group')
    else:
        chats.pop(str(message.chat.id), None)
        not_found_chats = str()
        # region sender with a mentioning
        # if message.chat.username != None:
        #     sender = f'@{message.chat.username}'
        # else:
        #     sender = f'<a href="{message.chat.user_url}">{message.chat.first_name}</a>'
        # endregion
        sender = '' #message.chat.full_name
        n = 1
        for chat_id in chats:
            try:
                if is_media_group:
                    await dp.bot.send_media_group(chat_id=chat_id, media=media)
                else:
                    if message.content_type in [ContentType.TEXT]:
                        await dp.bot.send_message(chat_id, f'{message.html_text}\n\n<b>{sender}</b>')
                    else:
                        caption = message.parse_entities(message.caption) if message.caption is not None else str()
                        await message.copy_to(chat_id=chat_id, caption=f'{caption}\n\n<b>{sender}</b>')
            except:
                not_found_chat = chats[chat_id]
                not_found_chats = f'{not_found_chats}{n}. {not_found_chat}\n'
                n += 1
                continue
            else:
                await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)

        if not_found_chats:
            await message.reply(f"""<b>
Couldn't send this message to the following chats:</b>\n
{not_found_chats}
<i>Maybe these chats aren't available anymore or I do not have an access to send them any message.</i>
""")
