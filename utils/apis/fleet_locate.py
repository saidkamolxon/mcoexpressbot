import base64
import requests
from asyncio import sleep
from urllib import parse as urlparse
from datetime import datetime, timedelta

from data.config import FLEET_LOGIN, FLEET_PASSWORD, FLEET_ACCOUNT_ID
from utils.apis import bing_maps, google_maps
from utils.common_functions import get_current_time, convert_date
from utils.db_api.postgresql import CoreSQL

USER = f'{FLEET_LOGIN}:{FLEET_PASSWORD}'.encode('ascii')


class FleetLocate:
    def __init__(self, user=USER, account_id=FLEET_ACCOUNT_ID, database=None) -> None:
        self.api_url = 'https://api.us.spireon.com/api'
        self.__user = user
        self.__account_id = account_id
        self.__headers = {'Authorization': f'Basic {self.__get_auth_string()}', 'Account': self.__account_id}
        self.session = requests.Session()
        self.session.headers.update(self.__headers)
        self.db: CoreSQL = database

    def __get_auth_string(self):
        base64_bytes = base64.b64encode(self.__user)
        return base64_bytes.decode('ascii')

    async def __get_data(self, url, param=''):
        tries = 10
        while tries > 0:
            r = self.session.get(url)
            try:
                if r.json()['success']:
                    return r.json()[param]
            except:
                pass
            await sleep(1)
            tries -= 1
        else:
            return -1

    async def update_facilities(self):
        # try:
        await self.db.create_table_facilities()
        facilities = await self.__get_all_landmarks()
        if facilities == -1:
            return -1
        for facility in facilities:
            name = facility['name']
            city = facility['city']
            state = facility['state']
            zip_code = facility['zip']
            address = f"{facility['address']}, {city}, {state} {zip_code}"
            points = facility['points']
            coordinates = f"{facility['lat']},{facility['lng']}"
            await self.db.add_to_facilities(facility=name, address=address,
                                            points=points, city=city, state=state,
                                            zip_code=zip_code, coordinates=coordinates)
        return "Done."

    # except:
    #     return -1

    def __get_trl_data(self, url, param=''):
        tries = 10
        while tries > 0:
            r = self.session.get(url)
            try:
                if r.json()['success']:
                    return r.json()[param]
            except:
                pass
            sleep(1)
            tries -= 1
        else:
            return -1

    def get_assets(self):
        url = self.api_url + '/asset'
        data = self.__get_trl_data(url, 'data')
        data = list(filter(lambda x: x['name'][:8] != 'INACTIVE', data))
        names = [x['name'] for x in data]
        return sorted(names)

    async def get_all_assets_info(self):
        assets = await self.db.get_all_trailers()
        length = len(assets)
        msg1, msg2, msg3 = '', '', ''
        n1, n2 = length // 3, length // 3 * 2
        # n = 1
        for asset in assets[:n1]:
            link = f"https://maps.google.com/maps?q={asset['coordinates']}"
            address = f"{asset['location']}" if not asset['landmark'] else f"{asset['landmark']}"
            msg1 += f"{'🟢' if asset['is_moving'] else '🔴'} <code>{asset['name']:10}</code> - <a href='{link}'>{address}</a>\n"
            # n += 1
        for asset in assets[n1:n2]:
            link = f"https://maps.google.com/maps?q={asset['coordinates']}"
            address = f"{asset['location']}" if not asset['landmark'] else f"{asset['landmark']}"
            msg2 += f"{'🟢' if asset['is_moving'] else '🔴'} <code>{asset['name']:10}</code> - <a href='{link}'>{address}</a>\n"
            # n += 1
        for asset in assets[n2:]:
            link = f"https://maps.google.com/maps?q={asset['coordinates']}"
            address = f"{asset['location']}" if not asset['landmark'] else f"{asset['landmark']}"
            msg3 += f"{'🟢' if asset['is_moving'] else '🔴'} <code>{asset['name']:10}</code> - <a href='{link}'>{address}</a>\n"
            # n += 1
        return msg1, msg2, msg3

    async def get_asset_location(self, asset_name, source='google'):
        link = 'https://maps.google.com/maps?q='
        trl = await self.__get_asset_status(asset_name)
        try:
            facilities = await self.__get_facilities()
            if trl['landmarkName'] in facilities.keys():
                location = facilities.get(trl['landmarkName'])['address']
            else:
                location = f"{trl['address']}, {trl['city']}, {trl['state']} {trl['zip']}"
        except:
            return -1
        else:
            coordinates = f"{trl['lat']},{trl['lng']}"
            last_event = trl['last_event']
            if source == 'bing':
                photo_url = bing_maps.StaticMap(center=coordinates)
            else:
                photo_url = google_maps.StaticMap(center=coordinates)
            caption = f'''Trailer#: <b>{trl['name']}</b> {'🟢' if trl['moving'] else '🔴'}

Coordinates: <code>{coordinates}</code>
Location: <b>{location}

👉 <a href="{link}{coordinates}">LINK</a></b> 👈
<span class="tg-spoiler"><i>Last GPS update: {convert_date(last_event, "%Y-%m-%d %H:%M:%S")} EST</i></span>
'''

            return trl['name'], photo_url, caption

    async def get_updated_lanes(self):
        data = await self.__get_all_landmark_status()
        if data == -1:
            return -1
        else:
            return [{x['name']: [asset['name'] for asset in x['assetList']]} for x in data]

    async def get_landmark_info(self, landmark_name):
        res = []
        lanes = await self.__get_landmark_status(landmark_name)
        for lane in lanes:
            try:
                location = f"{lane['address']}, {lane['city']}, {lane['state']} {lane['zip']}"
            except:
                continue
            else:
                coordinates = f"{lane['lat']},{lane['lng']}"
                caption = f"<b>{lane['name']}</b> - {location}"
                if lane['assetList']:
                    asset_coordinates = list()
                    caption += '\n\n<b>TRAILERS:</b>\n'
                    coord_dct = await self.__get_asset_coordinates(lane['name'])
                    n = 1
                    for trl in lane['assetList']:
                        asset_coordinates.append(coord_dct.get(trl['name']))
                        days = round(
                            (((datetime.now() - datetime.strptime(trl['dateEntered'], '%Y-%m-%d %H:%M:%S')) / timedelta(
                                days=1)) + 4 / 24),
                            1)
                        caption += f'''<b>{n}. </b><code>{trl['name']:10}</code> - {days}d. ➜ <code>{coord_dct.get(trl['name'])}</code>\n'''
                        n += 1
                    photo_url = google_maps.StaticMap(center=coordinates, objects=asset_coordinates)
                else:
                    photo_url = google_maps.StaticMap(center=coordinates)
                res.append((lane['name'], photo_url, caption))
        if res:
            return res
        return -1

    async def load_trailers_data(self):
        url = self.api_url + "/assetStatus"
        data = await self.__get_data(url, param='data')
        if data != -1:
            last_update = await get_current_time(timezone='US/Eastern')  # eastern time
            for trl in data:
                name = trl['name']
                if not name:
                    continue
                coordinates = f"{trl['lat']},{trl['lng']}"
                location = f"{trl['address']}, {trl['city']}, {trl['state']} {trl['zip']}"
                landmark = trl.get('landmarkName') or ''  # if returns error then value is empty string
                is_moving = trl.get('moving', False)  # if returns error then value is False
                last_event = await get_current_time(time_in_utc=trl['eventDateTime'], timezone='US/Eastern')
                await self.db.update_trailers(name=name, coordinates=coordinates,
                                              location=location, landmark=landmark, is_moving=is_moving,
                                              last_event=last_event, last_update=last_update)
            return "Done."
        return -1

    # region Encapsulated methods --->>>

    async def __get_all_landmarks(self):
        url = self.api_url + '/landmark'
        data = await self.__get_data(url, 'data')
        if isinstance(data, list):
            return sorted(data, key=lambda x: x['name'])
        else:
            return -1

    async def __get_all_landmark_status(self):
        url = self.api_url + '/landmarkStatus'
        data = await self.__get_data(url, 'data')
        if isinstance(data, list):
            data = list(filter(lambda x: isinstance(x['assetList'], list), data))
            return sorted(data, key=lambda x: x['name'])
        else:
            return -1

    async def get_trl_location(self, trlNumber):
        try:
            trl: dict = await self.__get_asset_status(trlNumber)
            res = {'lat': trl['lat'], 'lng': trl['lng']}
            facilities = await self.__get_facilities()
            if trl['landmarkName'] in facilities.keys():
                location = f"{trl['landmarkName']} ➜ {facilities.get(trl['landmarkName'])['address']}"
            else:
                location = f"{trl['address']}, {trl['city']}, {trl['state']} {trl['zip']}"
            res['address'] = location
        except:
            return -1
        else:
            res['title'] = f"Trailer# {trl['name']} {'🟢' if trl['moving'] else '🔴'}"
            return res

    async def __get_landmark_status(self, landmark_name):
        url = self.api_url + '/landmarkStatus'
        data = await self.__get_data(url, 'data')
        lanes = []
        try:
            for lane in data:
                if landmark_name.upper() in lane['name'].upper():
                    lanes.append(lane)
            return lanes
        except:
            return -1

    async def get_all_asset_status(self):
        url = self.api_url + '/assetStatus'
        data = await self.__get_data(url, 'data')
        if isinstance(data, list):
            data = list(filter(lambda x: isinstance(x['name'], str), data))
            return sorted(data, key=lambda x: x['name'])
        else:
            return -1

    async def __get_asset_status(self, asset_name):
        # From FleetLocate
        # url = self.api_url + '/assetStatus?name=' + asset_name
        # try:
        #     data = await self.__get_data(url, 'data')
        #     return data[0]
        # except:
        #     return -1

        # From database
        current_time = await get_current_time()
        sql = f"""
                SELECT
                    name, coordinates, location, landmark, is_moving, last_event
                FROM 
                    trailers
                WHERE
                    name LIKE '%{asset_name}%'
                    AND
                    CAST(last_update AS TIMESTAMP) + INTERVAL '40 minutes' <= CAST('{current_time}' AS TIMESTAMP)
        """
        trl = dict()
        trl['name'], trl['coordinates'], trl['location'], trl['landmark'], trl['is_moving'], trl['last_event'] = \
            await self.db.execute(sql, fetchone=True)
        return trl

    async def __get_asset_coordinates(self, landmark_name: str):
        enc = urlparse.quote_plus(landmark_name) if '(' not in landmark_name else landmark_name.split()[0]
        url = self.api_url + f'/assetStatus?landmarkName={enc}'
        try:
            data = await self.__get_data(url, 'data')
        except:
            return -1
        else:
            dct = dict()
            for trl in data:
                dct[trl['name']] = f"{trl['lat']},{trl['lng']}"
            return dct

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
