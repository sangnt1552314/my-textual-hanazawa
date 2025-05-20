import os
import logging
import asyncio
import httpx
import requests
import xmltodict
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

SHOUTCAST_BASE_URL = "http://api.shoutcast.com"
YP_SHOUTCAST_URL = "http://yp.shoutcast.com"
TIMEOUT_DEFAULT = 5

logging.basicConfig(
    filename=f"dev.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='w'  # a = append, w = overwrite
)
logger = logging.getLogger(__name__)


class ShoutcastRadio:
    def __init__(self, api_key=''):
        self.api_key = api_key or os.getenv("SHOUTCAST_API_KEY")

        if not self.api_key:
            raise ValueError("Shoutcast API key is required")

    async def get_all_genres(self):
        """
        Get the list of all genres asynchronously.
        """
        params = {
            "k": self.api_key,
        }

        response = await self._shoutcast_request_async("legacy/genrelist", params)

        return self._process_genres_response(response)

    def get_all_genres_sync(self):
        """
        Get the list of all genres synchronously.
        """
        params = {
            "k": self.api_key,
        }

        response = self._shoutcast_request_sync("legacy/genrelist", params)

        return self._process_genres_response(response)

    async def get_primary_genres(self, **kwargs):
        """
        Get the list of primary genres asynchronously.
        """
        params = {
            "k": self.api_key,
            "f": kwargs.get("format", "json"),
        }

        response = await self._shoutcast_request_async("genre/primary", params)

        return self._process_primary_genres_response(response)

    def get_primary_genres_sync(self, **kwargs):
        """
        Get the list of all genres synchronously.
        """
        params = {
            "k": self.api_key,
            "f": kwargs.get("format", "json"),
        }

        response = self._shoutcast_request_sync("genre/primary", params)

        return self._process_primary_genres_response(response)

    async def get_secondary_genres(self, **kwargs):
        """
        Get the list of secondary genres asynchronously.
        """
        params = {
            "k": self.api_key,
            "f": kwargs.get("format", "json"),
            "parentid": kwargs.get("parentid", ""),
        }

        response = await self._shoutcast_request_async("genre/secondary", params)

        return self._process_primary_genres_response(response)

    def get_secondary_genres_sync(self, **kwargs):
        """
        Get the list of secondary genres synchronously.
        """
        params = {
            "k": self.api_key,
            "f": kwargs.get("format", "json"),
            "parentid": kwargs.get("parentid", ""),
        }

        response = self._shoutcast_request_sync("genre/secondary", params)

        return self._process_primary_genres_response(response)

    async def get_top_500_stations(self, **kwargs):
        """
        Get the list of top 500 stations asynchronously.
        """
        params = {
            "k": self.api_key,
            "limit": kwargs.get("limit", (50, 0)),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
        }

        response = await self._shoutcast_request_async("legacy/Top500", params)

        return self._process_top_stations_response(response)

    def get_top_500_stations_sync(self, **kwargs):
        """
        Get the list of top 500 stations synchronously.
        """
        params = {
            "k": self.api_key,
            "limit": kwargs.get("limit", (50, 0)),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
        }

        response = self._shoutcast_request_sync("legacy/Top500", params)

        return self._process_top_stations_response(response)

    async def get_now_playing_stations(self, **kwargs):
        """
        Get the list of now playing stations asynchronously.
        """
        params = {
            "ct": kwargs.get("ct", ""),
            "k": self.api_key,
            "limit": kwargs.get("limit", (20, 0)),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
        }

        response = await self._shoutcast_request_async("station/nowplaying", params)

        return self._process_station_response(response)

    def get_now_playing_stations_sync(self, **kwargs):
        """
        Get the list of now playing stations synchronously.
        """
        params = {
            "ct": kwargs.get("ct", ""),
            "k": self.api_key,
            "limit": kwargs.get("limit", (20, 0)),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
        }

        response = self._shoutcast_request_sync("station/nowplaying", params)

        return self._process_station_response(response)

    async def get_stations_by_genre_or_bitrate(self, **kwargs):
        """
        Get the list of stations by genre or bitrate asynchronously.
        """
        params = {
            "k": self.api_key,
            "limit": kwargs.get("limit", (20, 0)),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
            "br": kwargs.get("br", "128"),
            "genre_id": kwargs.get("genre_id", ""),
        }

        response = await self._shoutcast_request_async("station/advancedsearch", params)

        return self._process_station_response(response)

    def get_stations_by_genre_or_bitrate_sync(self, **kwargs):
        """
        Get the list of stations by genre or bitrate synchronously.
        """
        params = {
            "k": self.api_key,
            "limit": kwargs.get("limit", (20, 0)),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
            "br": kwargs.get("br", "128"),
            "genre_id": kwargs.get("genre_id", ""),
        }

        response = self._shoutcast_request_sync(
            "station/advancedsearch", params)

        return self._process_station_response(response)

    def get_station_stream_url(self, station_id="", tunin={}):
        """
        Get the stream URL for a given station ID.
        """
        if station_id == "":
            return ''

        if not tunin:
            tunin = {
                'base': '/sbin/tunein-station.pls',
                'base-m3u': '/sbin/tunein-station.m3u',
                'base-xspf': '/sbin/tunein-station.xspf'
            }

        tunin_base = tunin.get("base", "") or tunin.get("@base", "")
        # tunin_base_m3u = tunin.get("base-m3u", "") or tunin.get("@base-m3u", "")
        # tunin_base_xspf = tunin.get("base-xspf", "") or tunin.get("@base-xspf", "")

        tunin_base_url = f"{YP_SHOUTCAST_URL}/{tunin_base}?id={station_id}"
        # tunin_base_m3u_url = f"{YP_SHOUTCAST_URL}/{tunin_base_m3u}?id={station_id}"
        # tunin_base_xspf_url = f"{YP_SHOUTCAST_URL}/{tunin_base_xspf}?id={station_id}"

        tunin_response = requests.get(tunin_base_url)

        if tunin_response.status_code != 200:
            return ''

        try:
            tunin_content_data = tunin_response.content
            stream_url = tunin_content_data.decode("utf-8").strip()
            stream_url = stream_url.split("File1=")[1].split("Title1")[0]
            stream_url = quote(stream_url, safe=":/")
        except Exception as e:
            print(f"Error parsing stream URL: {e}")
            return ''

        return stream_url

    def _shoutcast_request_sync(self, endpoint, params):
        """
        Helper function to make a GET request to the Shoutcast API synchronously.
        """
        try:
            response = requests.get(
                f"{SHOUTCAST_BASE_URL}/{endpoint}", params=params, timeout=TIMEOUT_DEFAULT)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Please try again later.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching data: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

        if response.status_code != 200:
            raise Exception(
                f"Error fetching data: {response.status_code} - {response.text} - {endpoint} - {params}")

        return response

    async def _shoutcast_request_async(self, endpoint, params):
        """
        Helper function to make a GET request to the Shoutcast API asynchronously.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{SHOUTCAST_BASE_URL}/{endpoint}", params=params, timeout=TIMEOUT_DEFAULT)
                response.raise_for_status()
            except httpx.TimeoutException:
                raise Exception("Request timed out. Please try again later.")
            except httpx.RequestError as e:
                raise Exception(f"Error fetching data: {e}")
            except Exception as e:
                raise Exception(f"An unexpected error occurred: {e}")

        if response.status_code != 200:
            raise Exception(
                f"Error fetching data: {response.status_code} - {response.text} - {endpoint} - {params}")

        return response

    def _process_genres_response(self, response):
        """
        Helper method to process the genres response.
        """
        xml_data = xmltodict.parse(response.content)
        genre_list = xml_data.get("genrelist", {}).get("genre", {})

        if not genre_list:
            return []

        return [{
            "name": genre["@name"],
            "count": genre["@count"],
        } for genre in genre_list if isinstance(genre, dict)]

    def _process_primary_genres_response(self, response):
        """
        Helper method to process the genres response.
        """
        data = response.json()
        genre_list = data.get("response", {}).get(
            "data", {}).get("genrelist", {}).get("genre", {})

        if not genre_list:
            return []

        return [
            {
                "id": genre["id"],
                "name": genre["name"],
                "count": genre.get("count", 0),
                "haschildren": genre["haschildren"],
                "parentid": genre.get("parentid", 0),
            }
            for genre in genre_list
        ]

    def _process_top_stations_response(self, response):
        xml_data = xmltodict.parse(response.content)
        stations = xml_data.get("stationlist", {}).get("station", {})

        if not stations:
            return []

        return [
            {
                "id": str(station["@id"]),
                "name": f"""{station["@name"]}""",
                "value": str(station["@id"]),
                "genre": station["@genre"],
            }
            for station in stations
        ]

    def _process_station_response(self, response):
        """
        Helper method to process the station response.
        """
        data = response.json()
        stations = data.get("response", {}).get("data", {}).get(
            "stationlist", {}).get("station", {})

        if not stations:
            return []

        return [
            {
                "id": str(station["id"]),
                "name": f"""{station["name"]} - {station['genre']}""",
                "value": str(station["id"]),
                "genre": station["genre"],
            }
            for station in stations
        ]


async def main():
    # Example usage
    radio = ShoutcastRadio()
    genres = await radio.get_stations_by_genre_or_bitrate(genre_id="1")
    print("Asynchronous Call - Genres:", genres)

if __name__ == "__main__":
    # Run example
    radio = ShoutcastRadio()
    genres = radio.get_stations_by_genre_or_bitrate_sync(genre_id="1")
    print("Synchronous Call - Genres:", genres)

    asyncio.run(main())
