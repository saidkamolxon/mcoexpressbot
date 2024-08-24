import requests


class Nominatim:    # Geocoding API by Openstreetmap
    def __init__(self, lat: str, lng: str) -> None:
        self.url = f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json'
        self.session = requests.Session()
        self.reversed_geocode()

    def reversed_geocode(self):
        r = self.session.get(self.url)
        if r.status_code == 200:
            data = r.json()
            a = data['display_name'].split(',')
            return ', '.join(x.strip() for x in a[:-1])

    def __str__(self):
        return self.reversed_geocode()
