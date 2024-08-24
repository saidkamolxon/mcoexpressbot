from aiogram import types
from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters import Text
from loader import dp, db, fl, sw
from utils.fleet_config import get_landmark_info
from utils.common_functions import split_message
from states.states import AllStates
from prettytable import PrettyTable
import requests
from utils.apis import google_maps


@dp.message_handler(state=AllStates.group_name)
async def get_name(message: types.Message, state: FSMContext):
    name = message.text
    if name[0].isdigit():
        await message.answer("Name shouldn't be started with a digit.")
    else:
        await state.update_data(group_name=name)
        await message.answer(await db.add_a_group(name))
        await state.finish()


@dp.message_handler(state=AllStates.asked_lane)
async def get_name(message: types.Message, state: FSMContext):
    wm = await message.answer("I am searching...")
    lane = message.text
    await state.update_data(asked_lane=lane)
    lanes = await get_landmark_info(db, lane)
    if lanes == -1:
        await wm.edit_text('Sorry, not found any lane.')
    else:
        await wm.edit_text(text=f"Found {len(lanes)} lane(s). Sending... Please wait...")
        for lane in lanes:
            photo = requests.get(lane[1])
            await message.answer_photo(photo=photo.content, caption=lane[2])
        await wm.delete()
    await state.finish()


@dp.message_handler(state=AllStates.deleted_user)
async def delete_a_user(message: types.Message, state: FSMContext):
    if message.text.lower() != '/cancel':
        await message.answer(text=await db.remove_from_users(user_id=message.text))
    else:
        await message.answer('Cancelled')
    await state.finish()


@dp.message_handler(state=AllStates.made_admin)
async def make_admin(message: types.Message, state: FSMContext):
    if message.text.lower() != '/cancel':
        await message.answer(text=await db.make_an_admin(user_id=message.text))
    else:
        await message.answer('Cancelled')
    await state.finish()


@dp.message_handler(state=AllStates.asked_trailer)
async def get_trailer_loc(message: types.Message, state: FSMContext):
    trl = message.text
    await state.update_data(asked_trailer=trl)
    trl = await fl.get_asset_location(trl)
    if trl == -1:
        await message.answer('Not found.')
    else:
        photo = requests.get(trl[1])
        await message.answer_photo(photo=photo.content, caption=trl[2])
    await state.finish()


# @dp.message_handler(commands=await sw.get_truck_numbers()) ### need to check for users
@dp.message_handler(state=AllStates.asked_truck)
async def truck_location(message: types.Message, state: FSMContext):
    if str(message.from_user.id) in await db.get_users():
        truck = message.text
        await state.update_data(asked_truck=truck)
        res = await sw.get_truck_location(truck)
        if res == -1:
            await message.answer('Not found.')
        else:
            await message.answer_venue(latitude=res['lat'],
                                       longitude=res['lng'],
                                       address=res['address'],
                                       title=res['title'])
        await state.finish()


@dp.message_handler(state=AllStates.md_origin)
async def after_origin(message: types.Message, state: FSMContext):
    origin = message.text
    await state.update_data(md_origin=origin)
    await message.reply('Destination address: ')
    await AllStates.md_destination.set()


@dp.message_handler(state=AllStates.md_destination)
async def after_destination(message: types.Message, state: FSMContext):
    data = await state.get_data()
    origin = data.get('md_origin')
    destination = message.text
    answer = str(google_maps.DistanceMatrix(origin=origin, destination=destination))
    await message.reply(answer)
    await state.finish()


@dp.message_handler(state=AllStates.sql)
async def execute_sql(message: types.Message, state: FSMContext):
    sql = message.text
    try:
        connection = await db.connection
        cursor = connection.cursor()
        rows = cursor.execute(sql).fetchall()
        table = PrettyTable()
        table.field_names = [i[0] for i in cursor.description]
        cursor.close()
        for row in rows:
            table.add_row(row)
        text = table.get_string()
    except:
        text = 'ERROR! PLEASE CHECK YOUR QUERY...'
    msgs = split_message(text)
    for msg in msgs:
        await message.answer(f"<code>{msg}</code>")
    await state.finish()
