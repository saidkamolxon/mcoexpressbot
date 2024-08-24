import requests
from shapely.geometry import Point, Polygon

from data.config import ROADREADY_TOKEN
from utils.apis import bing_maps, google_maps
from utils.common_functions import get_current_time, convert_date


class RoadReady:
    def __init__(self, TOKEN: str = ROADREADY_TOKEN, database=None) -> None:
        self.api_url = 'https://api.roadreadysystem.com/jsonapi'
        self.__token = TOKEN
        self.__headers = {'x-api-key': ROADREADY_TOKEN}
        self.session = requests.Session()
        self.session.headers.update(self.__headers)
        self.db = database

    async def __get_data(self, url):
        r = self.session.get(url)
        if r.status_code == 200:
            return r.json()['data']
        return -1

    async def __get_facilities(self):
        facilities = dict()
        try:
            data = await self.db.execute("SELECT name, address FROM facilities;", fetchall=True)
        except:
            return -1
        else:
            for fac, add in data:
                facilities[fac] = {'address': add}
            return facilities

    async def get_landmark(self, coordinates: str, zip_code: str, state: str):  # getting landmark by coordinates
        sql = f'''
        SELECT
            name, points
        FROM 
            facilities
        WHERE
            zip = '{zip_code}'
'''
        landmarks = await self.db.execute(sql, fetchall=True)
        for landmark in landmarks:
            points = [x.split() for x in landmark[1].split(',')]
            landmark_area = Polygon(points)  # landmark[1] = points
            unit_point = Point(coordinates.split(','))
            if landmark_area.contains(unit_point):
                return landmark[0]  # landmark[0] = landmark name

        sql = sql.replace(f"zip = '{zip}'", f"state = '{state}'")
        landmarks = await self.db.execute(sql, fetchall=True)
        for landmark in landmarks:
            points = [x.split() for x in landmark[1].split(',')]
            landmark_area = Polygon(points)  # landmark[1] = points
            unit_point = Point(coordinates.split(','))
            if landmark_area.contains(unit_point):
                return landmark[0]  # landmark[0] = landmark name
        return ''

    async def load_trailers_data(self):
        url = self.api_url + "/fleet_trailer_states"
        data = await self.__get_data(url)
        if data != -1:
            last_update = await get_current_time(timezone='US/Eastern')  # eastern time
            for trl in data:
                tdata = trl['attributes']
                name = tdata['trailerName']
                coordinates = f"{tdata['latitude']},{tdata['longitude']}"
                location = tdata['location']
                landmark = await self.get_landmark(coordinates=coordinates, zip_code=location[-10:-5],
                                                   state=location[-13:-11])
                is_moving = tdata.get('landmarkTrailerState') == 'InMotion'
                last_event = tdata['lastEvent']['messageDate']  # eastern time
                await self.db.update_trailers(name=name, coordinates=coordinates,
                                              location=location, landmark=landmark, is_moving=is_moving,
                                              last_event=last_event, last_update=last_update)
            return "Done."
        return -1

    async def get_asset_location(self, asset_name, source='google'):
        link = 'https://maps.google.com/maps?q='
        trl = await self.__get_asset_status(asset_name)
        last_event = trl['last_event']
        try:
            facilities = await self.__get_facilities()
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
<span class="tg-spoiler"><i>Last GPS update: {convert_date(last_event, "%Y-%m-%d %H:%M:%S")} EST</i></span>
'''

        return trl['name'], photo_url, caption

    async def __get_asset_status(self, asset_name):
        sql = f"""
        SELECT
            name, coordinates, location, landmark, is_moving, last_event
        FROM 
            trailers
        WHERE
            name LIKE '%{asset_name}%'
"""
        trl = dict()
        trl['name'], trl['coordinates'], trl['location'], trl['landmark'], trl['is_moving'], trl['last_event'] = \
            await self.db.execute(sql, fetchone=True)

        return trl
