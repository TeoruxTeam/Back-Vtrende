from geopy.geocoders import Nominatim


class GeocoderSingleton:
    # Реализован вне контейнера для исключения возможности создания нескольких экземпляров (в связи с несколькими контейнерами)
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeocoderSingleton, cls).__new__(cls)
            cls._instance.geolocator = Nominatim(user_agent="vivli")
        return cls._instance

    async def reverse_geocode(self, lat, lng, language="en"):
        location = self.geolocator.reverse(
            (lat, lng), exactly_one=True, language=language
        )

        if location:
            if "name:en" in location.raw.get("address", {}):
                return location.raw["address"]["name:en"]
            else:
                return location.address
        else:
            return "Unknown location"


geocoder = GeocoderSingleton()
