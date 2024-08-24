from data.config import BING_API


class StaticMap:
    def __init__(self, center: str, objects: list = None) -> None:
        self.api_url = 'http://dev.virtualearth.net/REST/v1/Imagery/Map/AerialWithLabels/'
        self.center = center
        self.objects = objects
        self.zoom = 17
        self.mark_as = '47'
        self.size = '1000,1000'
        self.map_type = 'hybrid'
        self.get_image_loc()

    def get_image_loc(self):
        if self.objects:    # if there are objects' coordinates
            url = f"{self.api_url}{self.center}/{str(self.zoom)}?mapSize={self.size}&key={BING_API}"
            for i in range(len(self.objects)):
                url += f"&pp={self.objects[i]};{self.mark_as};{i + 1}"
            return url
        # if there is not any object coordinates then return for center coordinates
        return f'{self.api_url}{self.center}/{str(self.zoom)}?mapSize={self.size}' + \
            f'&pp={self.center};{self.mark_as};&key={BING_API}'

    def __str__(self) -> str:
        return self.get_image_loc()
