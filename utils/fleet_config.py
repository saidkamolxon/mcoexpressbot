from datetime import datetime, timedelta

from utils.apis import bing_maps, google_maps
from utils.common_functions import get_current_time
from utils.db_api.postgresql import CoreSQL


async def get_trailer(db, trailer_name, source='google'):
    # name, coordinates, location, landmark, is_moving, last_event, last_update
    link = 'https://maps.google.com/maps?q='
    trl = await db.get_trailer(trailer_name)
    if trl == -1: return trl  # if returned an error

    now_string = await get_current_time()  # in US/Eastern timezone
    now = await get_converted_date(now_string)
    last_event = trl['last_event']
    if last_event + timedelta(hours=24) < now:
        return -1
    else:  # if the last update was within 24 hours
        try:
            facilities = await db.get_landmarks()
            if trl['landmark'] in facilities.keys():
                location = facilities.get(trl['landmark'])['address']
            else:
                location = trl['location']
        except:
            return -1

        coordinates = trl['coordinates']
        if source == 'bing':
            photo_url = bing_maps.StaticMap(center=coordinates)
        else:
            photo_url = google_maps.StaticMap(center=coordinates)
        caption = f'''Trailer#: <b>{trl['name']}</b> {'🟢' if trl['is_moving'] else '🔴'}

Coordinates: <code>{coordinates}</code>
Location: <b>{location}

👉 <a href="{link}{coordinates}">LINK</a></b> 👈
<span class="tg-spoiler"><i>Last GPS update: {last_event.strftime('%d-%b %H:%M')} EST</i></span>
'''
        return trl['name'], photo_url, caption


async def get_landmark_info(db: CoreSQL, landmark_name: str, source='google'):
    res = []
    lanes = await db.get_landmark(landmark_name=landmark_name.upper())
    for lane in lanes:
        name = lane['name']
        address = lane['address']
        coordinates = lane['coordinates']
        caption = f"<b>{name}</b> - {address}"
        trailers = await db.get_trailers_by_landmark(name)
        if trailers:
            asset_coordinates = list()
            caption += '\n\n<b>TRAILERS:</b>\n'
            n = 1
            for trl in trailers:
                asset_coordinates.append(trl['coordinates'])  # trl[1] is equal to coordinates of the trailer
                caption += f'''<b>{n}. </b><code>{trl['name']:10}</code> ➜ <code>{trl['coordinates']}</code>\n'''
                n += 1
            photo_url = google_maps.StaticMap(center=coordinates, objects=asset_coordinates)
        else:
            photo_url = google_maps.StaticMap(center=coordinates)
        res.append((name, photo_url, caption))
    if res:
        return res
    return -1


async def get_converted_date(date_string):
    format = "%m-%d-%Y %H:%M:%S"
    return datetime.strptime(date_string, format)

# import asyncio
# from utils.db_api.postgresql import CoreSQL
#
# async def runC():
#     db = CoreSQL()
#     await db.create()
#     fl = Fleet(database=db)
#     result = await fl.get_updated_lanes()
# rr = RoadReady(database=db)
# print(await fl.load_trailers_data())
# print(await rr.load_trailers_data())

# asyncio.run(runC())
