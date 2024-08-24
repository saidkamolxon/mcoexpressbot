import requests
from aiogram import types
from aiogram.dispatcher import FSMContext
from data.config import OWNER_ID
from loader import dp, db, fl, sw, bot
from states.states import AllStates
from utils.apis.google_maps import TimeZone
from utils.fleet_config import get_trailer


# Getting all trailer info
@dp.message_handler(commands='all_trl_info')
async def all_trailer_info(message: types.Message):
    msg1, msg2, msg3 = await fl.get_all_assets_info()
    await message.answer(text=msg1)
    await message.answer(text=msg2)
    await message.answer(text=msg3)


@dp.message_handler(commands='get_odometers')
async def get_odometers(message: types.Message):
    res = await sw.get_odometers()
    await message.answer(res)


# Creating a group
@dp.message_handler(commands='add_group')
async def add_group(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=True)
    if str(message.chat.id) == OWNER_ID:
        await message.answer('Choose a name for the group.')
        await AllStates.group_name.set()


@dp.message_handler(commands='sql')
async def run_sql(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=True)
    if str(message.chat.id) == OWNER_ID:
        await message.answer('Enter your sql query: ')
        await AllStates.sql.set()


@dp.message_handler(commands='delete_user')
async def delete_user(message: types.Message, state: FSMContext):
    await state.finish()
    if str(message.chat.id) == OWNER_ID:
        msg, n = 'Copy one of these user ids & input it in order to delete user:\n\n', 1
        users = await db.get_users()
        for _id, _name in users.items():
            msg += f'{n}. <b>{_name}</b> - <code>{_id}</code>\n'
            n += 1
        msg += '\nSend /cancel to cancel.'
        await message.answer(msg)
        await AllStates.deleted_user.set()


@dp.message_handler(commands='make_admin')
async def make_admin(message: types.Message, state: FSMContext):
    await state.finish()
    if str(message.chat.id) == OWNER_ID:
        msg, n = 'Copy one of these user ids & input it in order to make user an admin:\n\n', 1
        users = await db.get_users()
        for _id, _name in users.items():
            msg += f'{n}. <b>{_name}</b> - <code>{_id}</code>\n'
            n += 1
        msg += '\nSend /cancel to cancel.'
        await message.answer(msg)
        await AllStates.made_admin.set()


@dp.message_handler(commands='lanes_update')
async def trailer_info(message: types.Message):
    updates = await fl.get_updated_lanes()
    if updates == -1:
        await message.answer('Something went wrong...')
    else:
        msg = ''
        for lane in updates:
            for k, v in lane.items():
                assets = str()
                for asset in sorted(v):
                    assets = f'{assets} {asset},'
                msg = f'{msg}<b>{k}:</b> {assets}\n\n'
        await message.answer(text=msg)


@dp.message_handler(commands='trailer_loc')
async def trailer_info(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Enter number of the trailer:')
    await AllStates.asked_trailer.set()


@dp.message_handler(commands=fl.get_assets())
async def trailer_location(message: types.Message):
    trl = message.text.split('/')[-1]
    res = await fl.get_trl_location(trl)
    if res == -1:
        await message.answer('Not found.')
    else:
        await message.answer_venue(latitude=res['lat'],
                                   longitude=res['lng'],
                                   address=res['address'],
                                   title=res['title'])


@dp.message_handler(commands='lane_info')
async def trailer_info(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Enter the name of a lane:')
    await AllStates.asked_lane.set()


@dp.message_handler(commands='truck_loc')
async def truck_loc(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Enter number of the truck:')
    await AllStates.asked_truck.set()


@dp.message_handler(commands=(sw.get_truck_numbers()))
async def truck_location(message: types.Message):
    truck = message.text.split('/')[-1]
    res = await sw.get_truck_location(truck)
    if res == -1:
        await message.answer('Not found.')
    else:
        await message.answer_venue(latitude=res['lat'],
                                   longitude=res['lng'],
                                   address=res['address'],
                                   title=res['title'])


@dp.message_handler(commands='activate')
async def deactivate(message: types.Message):
    if message.chat.id < 0:
        if str(message.from_user.id) in await db.get_users(only_admins=True):
            await message.answer(await db.set_on_off(str(message.chat.id), True))
    else:
        await message.answer(await db.set_on_off(str(message.chat.id), True))
        await message.answer(await db.set_on_off(str(message.chat.id), True))


@dp.message_handler(commands='deactivate')
async def deactivate(message: types.Message):
    if message.chat.id < 0:
        if str(message.from_user.id) in await db.get_users(only_admins=True):
            await message.answer(await db.set_on_off(str(message.chat.id), False))
    else:
        await message.answer(await db.set_on_off(str(message.chat.id), False))


@dp.message_handler(commands='distance')
async def measure_distance(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply('Current address: ')
    await AllStates.md_origin.set()


@dp.message_handler(commands='eta')
async def get_eta(message: types.Message, state: FSMContext):
    await state.finish()
    truck_number = message.text.split('/eta')[-1].strip()
    truck_data = await sw.get_truck_location(truck_number)
    try:
        truck_location = f"{truck_data['lat']},{truck_data['lng']}"
        await state.update_data(md_origin=truck_location)
        await message.reply('Destination: ')
        await AllStates.md_destination.set()
    except Exception as err:
        await state.finish()
        await message.reply(str(err))


@dp.message_handler(commands=['g', 'b'])
async def get_trailer_loc(message: types.Message, state: FSMContext):
    await state.finish()
    source = 'google'
    text = message.text.upper()
    if '/B' in text:
        asset = text.split('/B')[-1].strip()
        source = 'bing'
    else:
        asset = text.split('/G')[-1].strip()
    trl = await get_trailer(db, asset, source)
    if trl == -1:
        await message.answer('Not found.')
    else:
        photo = requests.get(trl[1])
        await message.answer_photo(photo=photo.content, caption=trl[2])


@dp.message_handler(commands='update_facilities')
async def update_facilities(message: types.Message, state: FSMContext):
    if str(message.chat.id) == OWNER_ID:
        await state.finish()
        result = await fl.update_facilities()
        await message.answer(result)


@dp.message_handler(commands=['delete'])
async def delete_own_message(message: types.Message):
    message_id = message.text.split('/delete')[-1].strip()
    await bot.delete_message(message_id=message_id)


@dp.message_handler(commands='time_in')
async def get_local_time(message: types.Message):
    location = message.text.split('/time_in')[-1].strip()
    result: dict = await TimeZone(location).get_time()
    await message.reply(
        f"""
<b>Local time:</b> {result.get('time')}
<b>Local date:</b> {result.get('date')}
<b>Time zone id:</b> {result.get('time_zone_id')}
<b>Time zone name:</b> {result.get('time_zone_name')}

<b>Source:</b> <u>Google Time Zone</u>©️
""" if result else "Invalid input format. Please provide a valid location name or coordinates.")


@dp.message_handler(commands='time_for')
async def get_local_time(message: types.Message):
    truck = message.text.split('/time_for')[-1].strip()
    res = await sw.get_truck_location(truck)
    if res == -1:
        await message.answer('Not found.')
    else:
        location = f"{res.get('lat')},{res.get('lng')}"
        city = res.get('city')
        result: dict = await TimeZone(location).get_time()
        await message.reply(
            f"""
<b>Region:</b> {city}
<b>Local time:</b> {result.get('time')}
<b>Local date:</b> {result.get('date')}
<b>Time zone id:</b> {result.get('time_zone_id')}
<b>Time zone name:</b> {result.get('time_zone_name')}

<b>Source:</b> <u>Google Time Zone</u>©️
""" if result else "Invalid input format. Please provide a valid location name or coordinates.")
