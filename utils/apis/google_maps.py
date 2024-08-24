from datetime import datetime, timedelta

import requests, re

from data.config import GOOGLE_API


class DistanceMatrix:
    def __init__(self, origin: str, destination: str) -> None:
        self.url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'
        self.origin = origin
        self.destination = destination
        self.measure_distance()

    def measure_distance(self) -> str:  # SOURCE: GOOGLE MAPS
        url = f'{self.url}units=imperial&key={GOOGLE_API}' + \
              f'&origins={self.origin}' + \
              f'&destinations={self.destination}'
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
                return 'Error! Please enter correct addresses.'

    def __str__(self) -> str:
        return self.measure_distance()


class Geocoding:
    def __init__(self) -> None:
        self.url = f'https://maps.google.com/maps/api/geocode/json?'
        self.session = requests.Session()
        self.session.params = {'key': GOOGLE_API}

    async def reverse_geocode(self, coordinates: str):
        url = f'{self.url}latlng={coordinates}'
        r = self.session.get(url)
        if r.status_code == 200:
            data = r.json()
            return {
                'compound_code': data['plus_code']['compound_code'],
                'formatted_address': data['results'][0]['formatted_address']
            }
        return None

    async def true_geocode(self, address):
        url = f'{self.url}address={address}'
        r = self.session.get(url)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                location = results[0].get("geometry", {}).get("location", {})
                return f'{location.get("lat")},{location.get("lng")}'
            return 'Error!'


class StaticMap:
    def __init__(self, center: str, objects: list = None) -> None:
        self.api_url = 'https://maps.googleapis.com/maps/api/staticmap?'
        self.center = center
        self.objects = objects
        self.zoom = 17
        self.mark_as = ['red', 'blue', 'green', 'yellow', 'orange', 'black', 'white', 'pink', 'purple']
        self.size = '700x700'
        self.maptype = 'hybrid'
        self.get_image_loc()

    def get_image_loc(self):  # get image of the given location
        if self.objects:    # if there are objects' coordinates
            url = f'{self.api_url}center={self.center}&scale=2&language=en&zoom={str(self.zoom)}' + \
                  f'&size={self.size}' + f'&maptype={self.maptype}&format=jpg&key={GOOGLE_API}'
            for i in range(len(self.objects)):
                url += f"&markers=color:{self.mark_as[i % 9]}%7Clabel:{i + 1}%7C{self.objects[i]}"
            return url
        # if there is not any object coordinates then return for center coordinates
        return f'{self.api_url}center={self.center}&scale=2&language=en&zoom={str(self.zoom)}' + \
            f'&markers=color:{self.mark_as[0]}%7C{self.center}&size={self.size}' + \
            f'&maptype={self.maptype}&format=jpg&key={GOOGLE_API}'

    def __str__(self) -> str:
        return self.get_image_loc()


class TimeZone:
    def __init__(self, location: str):
        self.api_url = 'https://maps.googleapis.com/maps/api/timezone/json?'
        self.location = location
        self.api_key = GOOGLE_API
        self.__coordinates_pattern = re.compile(r'^\s*(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)\s*$')

    async def get_time(self):
        result = None
        if self.__coordinates_pattern.match(self.location):
            is_ok = await self.get_local_time(self.location)
            if is_ok:
                result = is_ok
        else:
            geocoding = Geocoding()
            coordinates = await geocoding.true_geocode(address=self.location)
            if coordinates:
                result = await self.get_local_time(coordinates)
        return result

    async def get_local_time(self, coordinates, timestamp='1377853200'):
        url = f"{self.api_url}location={coordinates}&timestamp={timestamp}&key={self.api_key}"
        response = requests.get(url)
        data = response.json()
        if data.get("status") == "OK":
            raw_offset = data.get("rawOffset", 0)
            dst_offset = data.get("dstOffset", 0)
            current_utc_time = datetime.utcnow()
            local_time = current_utc_time + timedelta(seconds=(raw_offset + dst_offset))
            return {
                "time": local_time.strftime('%H:%M'),
                "date": local_time.strftime('%d %b %Y'),
                "time_zone_id": data.get("timeZoneId"),
                "time_zone_name": data.get("timeZoneName")
                }
        else:
            return None
