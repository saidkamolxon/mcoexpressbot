from datetime import datetime, timedelta
from data.config import GOOGLE_API
import requests, re


class GoogleTimeZone:
    def __init__(self, location : str, api_key = GOOGLE_API):
        self.location = location
        self.api_key = api_key
        self.api_url = 'https://maps.googleapis.com/maps/api/timezone/json?'

    async def get_time(self):
        result = None
        coordinates_pattern = re.compile(r'^\s*(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)\s*$')
        if coordinates_pattern.match(self.location):
            is_ok = await self.get_local_time_from_google(self.location)
            if is_ok: result = is_ok
        else:
            coordinates = await self.get_coordinates_from_address(self.location)
            if coordinates: result = await self.get_local_time_from_google(coordinates)
        return result

    async def get_coordinates_from_address(self, address):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={self.api_key}"
        response = requests.get(url)
        data = response.json()

        if data.get("status") == "OK":
            results = data.get("results", [])
            if results:
                location = results[0].get("geometry", {}).get("location", {})
                return f'{location.get("lat")},{location.get("lng")}'
        return None

    async def get_local_time_from_google(self, coordinates, timestamp = '1377853200'):
        url = f"{self.api_url}location={coordinates}&timestamp={timestamp}&key={self.api_key}"
        response = requests.get(url)
        data = response.json()
        if data.get("status") == "OK":
            raw_offset = data.get("rawOffset", 0)
            dst_offset = data.get("dstOffset", 0)
            current_utc_time = datetime.utcnow()
            local_time = current_utc_time + timedelta(seconds=(raw_offset + dst_offset))
            # formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
            return {
                "time" : local_time.strftime('%H:%M'),
                "date" : local_time.strftime('%d %b %Y'),
                "time_zone_id" : data.get("timeZoneId"),
                "time_zone_name" : data.get("timeZoneName")
                }
        else:
            return None
