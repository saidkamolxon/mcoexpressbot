import base64, tracemalloc
# from utils.db_api.sqlite import CoreSQL
from utils.db_api.postgresql import CoreSQL
from urllib import parse as urlparse
from time import sleep
import requests
from datetime import datetime as dt, timedelta as td
from utils.common_functions import convert_date
from data.config import BING_API, GOOGLE_API, FLEET_LOGIN, FLEET_PASSWORD, FLEET_ACCOUNT_ID as ACCOUNT_ID, \
    SWIFTELD_TOKEN

USER = f'{FLEET_LOGIN}:{FLEET_PASSWORD}'.encode('ascii')
TRIES = 10  # for requests /* 1 request = 1 second */
tracemalloc.start()


# db = CoreSQL(path_to_db='data/main.db')
db = CoreSQL()

class Fleet:
    def __init__(self, user=USER, account_id=ACCOUNT_ID) -> None:
        self.api_url = 'https://api.us.spireon.com/api'
        self.__user = user
        self.__account_id = account_id
        self.__headers = {'Authorization': f'Basic {self.__get_auth_string()}', 'Account': self.__account_id}
        self.session = requests.Session()
        self.session.headers.update(self.__headers)

    def __get_auth_string(self):
        base64_bytes = base64.b64encode(self.__user)
        return base64_bytes.decode('ascii')

    async def __get_data(self, url, param=''):
        tries = TRIES
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

    async def update_facilities(self):
        try:
            await db.create_table_facilities()
            facilities = await self.__get_all_landmarks()
            if facilities == -1:
                return -1
            for facility in facilities:
                name = facility['name']
                address = f"{facility['address']}, {facility['city']}, {facility['state']} {facility['zip']}"
                await db.add_to_facilities(facility=name, address=address)
            return "Done."
        except:
            return -1

    def __get_trl_data(self, url, param=''):
        tries = TRIES
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
        assets = await self.__get_all_asset_status()
        lenth = len(assets)
        msg1, msg2, msg3 = '', '', ''
        n1, n2 = lenth // 3, lenth // 3 * 2
        # n = 1
        for asset in assets[:n1]:
            link = f"https://maps.google.com/maps?q={asset['lat']},{asset['lng']}"
            address = f"{asset['address']}, {asset['city']}, {asset['state']}" if not asset[
                'landmarkName'] else f"<b><u>{asset['landmarkName']}</u></b>"
            msg1 += f"{'🟢' if asset['moving'] else '🔴'} <code>{asset['name']:10}</code> - <a href='{link}'>{address}</a>\n"
            # n += 1
        for asset in assets[n1:n2]:
            link = f"https://maps.google.com/maps?q={asset['lat']},{asset['lng']}"
            address = f"{asset['address']}, {asset['city']}, {asset['state']}" if not asset[
                'landmarkName'] else f"<b><u>{asset['landmarkName']}</u></b>"
            msg2 += f"{'🟢' if asset['moving'] else '🔴'} <code>{asset['name']:10}</code> - <a href='{link}'>{address}</a>\n"
            # n += 1
        for asset in assets[n2:]:
            link = f"https://maps.google.com/maps?q={asset['lat']},{asset['lng']}"
            address = f"{asset['address']}, {asset['city']}, {asset['state']}" if not asset[
                'landmarkName'] else f"<b><u>{asset['landmarkName']}</u></b>"
            msg3 += f"{'🟢' if asset['moving'] else '🔴'} <code>{asset['name']:10}</code> - <a href='{link}'>{address}</a>\n"
            # n += 1
        return msg1, msg2, msg3

    async def get_asset_location(self, asset_name, source = 'google'):
        link = 'https://maps.google.com/maps?q='
        trl = await self.__get_assetstatus(asset_name)
        try:
            facilities = await self.__get_facilities()
            if trl['landmarkName'] in facilities.keys():
                location = facilities.get(trl['landmarkName'])['address']
            else:
                location = f"{trl['address']}, {trl['city']}, {trl['state']} {trl['zip']}"
        except:
            return -1
        else:
            coords = f"{trl['lat']},{trl['lng']}"
            if source == 'bing':
                photo_url = BingMap(coords)
            else:
                photo_url = GoogleMap(coords)
            caption = f'''Trailer#: <b>{trl['name']}</b> {'🟢' if trl['moving'] else '🔴'}
            
Coordinates: <code>{coords}</code>
Location: <b>{location}

👉 <a href="{link}{coords}">LINK</a></b> 👈'''

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
                coords = f"{lane['lat']},{lane['lng']}"
                caption = f"<b>{lane['name']}</b> - {location}"
                if lane['assetList']:
                    asset_coords = list()
                    caption += '\n\n<b>TRAILERS:</b>\n'
                    coord_dct = await self.__get_asset_coords(lane['name'])
                    n = 1
                    for trl in lane['assetList']:
                        asset_coords.append(coord_dct.get(trl['name']))
                        days = round(
                            (((dt.now() - dt.strptime(trl['dateEntered'], '%Y-%m-%d %H:%M:%S')) / td(days=1)) + 4 / 24),
                            1)
                        caption += f'''<b>{n}. </b><code>{trl['name']:10}</code> - {days}d. ➜ <code>{coord_dct.get(trl['name'])}</code>\n'''
                        n += 1
                    photo_url = GoogleMapLandmark(coords, asset_coords, lane['radius'])
                else:
                    photo_url = GoogleMap(coords)
                res.append((lane['name'], photo_url, caption))
        if res:
            return res
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
            trl: dict = await self.__get_assetstatus(trlNumber)
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

    async def __get_all_asset_status(self):
        url = self.api_url + '/assetStatus'
        data = await self.__get_data(url, 'data')
        if isinstance(data, list):
            data = list(filter(lambda x: isinstance(x['name'], str), data))
            return sorted(data, key=lambda x: x['name'])
        else:
            return -1

    async def __get_assetstatus(self, asset_name):
        url = self.api_url + '/assetStatus?name=' + asset_name
        try:
            data = await self.__get_data(url, 'data')
            return data[0]
        except:
            return -1

    async def __get_asset_coords(self, landmark_name: str):
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

    @staticmethod
    async def __get_facilities():
        facilities = dict()
        try:
            data = await db.execute("SELECT name, address FROM facilities;", fetchall=True)
        except:
            return -1
        else:
            for fac, add in data:
                facilities[fac] = {'address': add}
            return facilities


# endregion


class Swift:
    def __init__(self, TOKEN: str = SWIFTELD_TOKEN) -> None:
        self.api_url = 'https://swifteld.com/extapi'
        self.__token = TOKEN
        self.session = requests.Session()
        self.session.params = {'token': self.__token}

    async def get_truck_data(self, truckNumber: str):
        url = self.api_url + '/asset-position/truck-list'
        data = await self.__get_data(url)
        for truck in data:
            if truck['truckNumber'] == truckNumber:
                return truck
        return -1

    async def __get_data(self, url):
        tries = TRIES
        while tries > 0:
            r = self.session.get(url)
            print(f"_get_data({url}) => " + str(r))
            if r.status_code == 200:
                print("_get_data_json => " + str(r.json()))
                return r.json()
            sleep(1)
            tries -= 1
        else:
            return -1

    async def get_truck_location(self, truckNumber):
        try:
            truck = await self.get_truck_data(truckNumber)
            res = {'lat': truck['lat'], 'lng': truck['lng']}
            data = (GeoCode(truck['lat'], truck['lng']).reversed_geocode())
            res['city'] = data.get('compound_code').split(maxsplit=1)[1]
            res['address'] = f"{data.get('formatted_address')} ({convert_date(truck['formattedSignalTime'][:19])})"
        except:
            return -1
        else:
            # coords = f"{truck['lat']},{truck['lng']}"
            # photo_url = GoogleMap(coords)
            driver_id = truck.get('driverId')
            driver = await self.get_driver(driver_id)
            res['title'] = f"#{truckNumber} {driver}\nSpeed: {truck['speed']}"
            return res

    async def get_driver(self, driverId):
        #region From SwiftELD
        # url = self.api_url + '/drivers'
        # data = self.__get_data(url)
        # print("get_driver => " + str(data))
        # for driver in data:
        #     if driver['driverId'] == driverId:
        #         return f"{driver['firstName']} {driver['lastName']}"
        # return -1
        #endregion
        #region From Database
        sql = f"SELECT first_name, last_name FROM swift_drivers WHERE id = '{driverId}'"
        data = await db.execute(sql, fetchone=True)
        firstname, lastname = data
        if firstname and lastname:
            return f"{firstname} {lastname}"
        return -1
        #endregion

    def get_truck_numbers(self):
        data = dict()
        url = self.api_url + '/asset-position/truck-list'
        tries = TRIES
        while tries > 0:
            r = self.session.get(url)
            if r.status_code == 200:
                data = r.json()
            sleep(1)
            tries -= 1
        return [x['truckNumber'] for x in data]

    async def get_odomoters(self):
        url = self.api_url + '/asset-position/truck-list'
        data = await self.__get_data(url)
        data = list(filter(lambda x: x['odometer'] is not None, data))
        res = ''
        for truck in sorted(data, key=lambda x: x['truckNumber']):
            res += f"<code>#{truck['truckNumber']:6}</code> ➜ {truck['odometer']}\n"
        return res


class GoogleMap:
    def __init__(self, coordinates) -> None:
        self.api_url = 'https://maps.googleapis.com/maps/api/'
        self.coords = coordinates
        self.zoom = 17
        self.mark_as = 'red'
        self.size = '700x700'
        self.maptype = 'hybrid'
        self.get_image_loc()

    def get_image_loc(self):
        return f'{self.api_url}staticmap?center={self.coords}&scale=2&language=en&zoom={str(self.zoom)}' + \
            f'&markers=color:{self.mark_as}%7C{self.coords}&size={self.size}' + \
            f'&maptype={self.maptype}&format=jpg&key={GOOGLE_API}'

    def __str__(self) -> str:
        return self.get_image_loc()


class GoogleMapLandmark:
    def __init__(self, lane_cords: str, asset_coords: list, radius: int) -> None:
        self.api_url = 'https://maps.googleapis.com/maps/api/staticmap'
        self.center = lane_cords
        self.coords = asset_coords
        self.zoom = 17
        self.mark_as = ['red', 'blue', 'green', 'yellow', 'orange', 'black', 'white', 'pink', 'purple']
        self.size = '700x700'
        self.maptype = 'hybrid'
        self.get_image_loc()

    def get_image_loc(self):
        url = f'{self.api_url}?center={self.center}&scale=2&language=en&zoom={str(self.zoom)}&size={self.size}' + \
              f'&maptype={self.maptype}&format=jpg&key={GOOGLE_API}'
        for i in range(len(self.coords)):
            url += f"&markers=color:{self.mark_as[i % 9]}%7Clabel:{i + 1}%7C{self.coords[i]}"
        return url

    def __str__(self) -> str:
        return self.get_image_loc()


class BingMap:
    def __init__(self, coordinates) -> None:
        self.api_url = 'http://dev.virtualearth.net/REST/v1/Imagery/Map/AerialWithLabels/'
        self.coords = coordinates
        self.zoom = 17
        self.mark_as = '47'
        self.size = '1000,1000'
        self.maptype = 'hybrid'
        self.get_image_loc()

    def get_image_loc(self):
        return f'{self.api_url}{self.coords}/{str(self.zoom)}?mapSize={self.size}' + \
            f'&pp={self.coords};{self.mark_as};&key={BING_API}'

    def __str__(self) -> str:
        return self.get_image_loc()


class BingMapLandmark:
    def __init__(self, lane_cords: str, asset_coords: list, radius: int) -> None:
        self.api_url = 'http://dev.virtualearth.net/REST/v1/Imagery/Map/AerialWithLabels/'
        self.center = lane_cords
        self.coords = asset_coords
        self.zoom = 17
        self.mark_as = '47'
        self.size = '1000,1000'
        self.maptype = 'hybrid'
        self.get_image_loc()

    def get_image_loc(self):
        url = f"{self.api_url}{self.center}/{str(self.zoom)}?mapSize={self.size}&key={BING_API}"
        for i in range(len(self.coords)):
            url += f"&pp={self.coords[i]};{self.mark_as};{i + 1}"
        return url

    def __str__(self) -> str:
        return self.get_image_loc()


class GeoCode:
    def __init__(self, lat: str, lng: str) -> None:
        self.url = f'https://maps.google.com/maps/api/geocode/json?latlng={lat},{lng}'
        self.__api_key = GOOGLE_API
        self.session = requests.Session()
        self.session.params = {'key': self.__api_key}
        self.reversed_geocode()

    def reversed_geocode(self):
        r = self.session.get(self.url)
        if r.status_code == 200:
            data = r.json()
            return {
                'compound_code' : data['plus_code']['compound_code'],
                'formatted_address' : data['results'][0]['formatted_address']
            }

    def __str__(self):
        return self.reversed_geocode()

class Nominatim: # Geocoding API by Openstreetmap
    def __init__(self, lat: str, lng: str) -> None:
        # https://nominatim.openstreetmap.org/reverse?lat=34.901393&lon=-82.222551&format=json
        self.url = f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json'
        self.session = requests.Session()
        self.reversed_geocode()

    def reversed_geocode(self):
        r = self.session.get(self.url)
        if r.status_code == 200:
            data = r.json()
            a = data['display_name'].split(',')
            return ', '.join(x.strip() for x in a[:-1])
             #f"{a.get('house_number') or ''} {a['road']}, {a['city']}, {a['ISO3166-2-lvl4'][3:]} {a['postcode']}"

    def __str__(self):
        return self.reversed_geocode()

async def measure_distance(origin: str, destination: str) -> str: # SOURCE: GOOGLE MAPS
    url = f'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&key={GOOGLE_API}' + \
          f'&origins={origin}' + \
          f'&destinations={destination}'
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        try:
            return f"""<b>
From</b>: <i>{data['origin_addresses'][0]}</i><b>
To</b>: <i>{data['destination_addresses'][0]}</i><b>
Distance</b>: <i>{data['rows'][0]['elements'][0]['distance']['text']}</i><b>
Duration</b>: <i>{data['rows'][0]['elements'][0]['duration']['text']}</i><b>

Source</b>: <u>Google Maps©️</u>
"""
        except:
            return 'Error! Please enter correct adresses.'
