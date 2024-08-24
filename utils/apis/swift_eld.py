import requests
from time import sleep

from data.config import SWIFTELD_TOKEN
from utils.apis.google_maps import Geocoding
from utils.common_functions import convert_date


class SwiftELD:
    def __init__(self, TOKEN: str = SWIFTELD_TOKEN, database=None) -> None:
        self.api_url = 'https://swifteld.com/extapi'
        self.__token = TOKEN
        self.session = requests.Session()
        self.session.params = {'token': self.__token}
        self.db = database

    async def get_truck_data(self, truckNumber: str):
        url = self.api_url + '/asset-position/truck-list'
        data = await self.__get_data(url)
        for truck in data:
            if truck['truckNumber'] == truckNumber:
                return truck
        return -1

    async def __get_data(self, url):
        tries = 10
        while tries > 0:
            r = self.session.get(url)
            if r.status_code == 200:
                return r.json()
            sleep(1)
            tries -= 1
        else:
            return -1

    async def get_truck_location(self, truckNumber):
        try:
            truck = await self.get_truck_data(truckNumber)
            res = {'lat': truck['lat'], 'lng': truck['lng']}
            coordinates = f"{truck['lat']},{truck['lng']}"
            geocoding = Geocoding()
            data = await geocoding.reverse_geocode(coordinates=coordinates)
            res['city'] = data.get('compound_code').split(maxsplit=1)[1]
            res['address'] = f"{data.get('formatted_address')} ({convert_date(truck['formattedSignalTime'][:19])})"
        except:
            return -1
        else:
            driver_id = truck.get('driverId')
            driver = await self.get_driver(driver_id)
            res['title'] = f"#{truckNumber} {driver}\nSpeed: {truck['speed']}"
            return res

    async def get_driver(self, driverId):
        # region From SwiftELD
        # url = self.api_url + '/drivers'
        # data = self.__get_data(url)
        # print("get_driver => " + str(data))
        # for driver in data:
        #     if driver['driverId'] == driverId:
        #         return f"{driver['firstName']} {driver['lastName']}"
        # return -1
        # endregion
        # region From Database
        sql = f"SELECT first_name, last_name FROM swift_drivers WHERE id = '{driverId}'"
        data = await self.db.execute(sql, fetchone=True)
        try:
            firstname, lastname = data
            if firstname and lastname:
                return f"{firstname} {lastname}"
        except:
            return "None"
        return -1
        # endregion

    def get_truck_numbers(self):
        data = dict()
        url = self.api_url + '/asset-position/truck-list'
        tries = 10
        while tries > 0:
            r = self.session.get(url)
            if r.status_code == 200:
                data = r.json()
            sleep(1)
            tries -= 1
        return [x['truckNumber'] for x in data]

    async def get_odometers(self):
        url = self.api_url + '/asset-position/truck-list'
        data = await self.__get_data(url)
        data = list(filter(lambda x: x['odometer'] is not None, data))
        res = ''
        for truck in sorted(data, key=lambda x: x['truckNumber']):
            res += f"<code>#{truck['truckNumber']:6}</code> ➜ {truck['odometer']}\n"
        return res
