import uuid
from aiogram import types
from loader import dp, db, fl

#
# @dp.inline_handler()
# async def inline_article(inline_query: types.InlineQuery) -> None:
#     text = inline_query.query or 'None'
#     print(text)
#     if str(inline_query.from_user.id) in await db.get_users():
#         res = await fl.get_trl_location(text)
#         if res == -1:
#             print('Yes')
#             # await inline_query.answer('Not found.')
#             pass
#         else:
#             print('No')
#             asset = types.InlineQueryResultVenue(
#                 id = str(uuid.uuid4()),
#                 latitude=res['lat'],
#                 longitude=res['lng'],
#                 address=res['address'],
#                 title=res['title'],
#                 thumb_url=f"https://maps.google.com/maps?q={res['lat']},{res['lng']}"
#             )
#             try:
#                 await inline_query.answer(results=[asset])
#             except:
#                 pass
