import os
import asyncio
import httpx
import requests
import xmltodict
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

SHOUTCAST_BASE_URL = "https://api.shoutcast.com"
YP_SHOUTCAST_URL = "http://yp.shoutcast.com"
TIMEOUT_DEFAULT = 5

class ShoutcastRadio:
    def __init__(self, api_key = ''):
        self.api_key = api_key or os.getenv("SHOUTCAST_API_KEY")
        if not self.api_key:
            raise ValueError("Shoutcast API key is required")

    async def get_all_genres(self, **kwargs):
        """
        Get the list of all genres. Supports both async and sync operations.
        """
        params = {
            "k": self.api_key,
        }

        if kwargs.get("async_request", False):
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{SHOUTCAST_BASE_URL}/legacy/genrelist", params=params, timeout=TIMEOUT_DEFAULT)
                except httpx.TimeoutException:
                    raise Exception("Request timed out. Please try again later.")
        else:
            try:
                response = requests.get(f"{SHOUTCAST_BASE_URL}/legacy/genrelist", params=params, timeout=TIMEOUT_DEFAULT)
            except requests.exceptions.Timeout:
                raise Exception("Request timed out. Please try again later.")

        if response.status_code != 200:
            raise Exception(f"Error fetching genres: {response.status_code} - {response.text}")
        
        xml_data = xmltodict.parse(response.content)
        genre_list = xml_data.get("genrelist", {}).get("genre", {})
        
        if not genre_list:
            return []
        
        return [{
            "name": genre["@name"],
            "count": genre["@count"],
        } for genre in genre_list if isinstance(genre, dict)]
    
    async def get_top_500_stations(self, **kwargs):
        """
        Get the list of top 500 stations. Supports both async and sync operations.
        """
        params = {
            "k": self.api_key,
            "limit": kwargs.get("limit", 50),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
        }

        # Handle both async and sync requests
        if kwargs.get("async_request", False):
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{SHOUTCAST_BASE_URL}/legacy/Top500", params=params, timeout=TIMEOUT_DEFAULT)
                except httpx.TimeoutException:
                    raise Exception("Request timed out. Please try again later.")
        else:
            try:
                response = requests.get(f"{SHOUTCAST_BASE_URL}/legacy/Top500", params=params, timeout=TIMEOUT_DEFAULT)
            except requests.exceptions.Timeout:
                raise Exception("Request timed out. Please try again later.")

        if response.status_code != 200:
            raise Exception(f"Error fetching top stations: {response.status_code} - {response.text}")

        xml_data = xmltodict.parse(response.content)
        # tunin = xml_data.get("stationlist", {}).get("tunein", {})
        stations = xml_data.get("stationlist", {}).get("station", {})

        if not stations:
            return []

        return [
            {
                "id": str(station["@id"]),
                "name": f"""{station["@name"]}""",
                "value": str(station["@id"]),
                "genre": station["@genre"],
                # "stream_url": self.get_station_stream_url(station["@id"], tunin),
            }
            for station in stations
        ]

    async def get_now_playing_stations(self, **kwargs):
        """
        Get the list of now playing stations. Supports both async and sync operations.
        """
        params = {
            "ct": kwargs.get("ct", ""),
            "k": self.api_key,
            "limit": kwargs.get("limit", 10),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
        }

        # Handle both async and sync requests
        if kwargs.get("async_request", False):
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{SHOUTCAST_BASE_URL}/station/nowplaying", params=params, timeout=TIMEOUT_DEFAULT)
        else:
            response = requests.get(f"{SHOUTCAST_BASE_URL}/station/nowplaying", params=params, timeout=TIMEOUT_DEFAULT)

        if response.status_code != 200:
            raise Exception(f"Error fetching now playing stations: {response.status_code} - {response.text}")

        data = response.json()
        # tunin = data.get("response", {}).get("data", {}).get("stationlist", {}).get("tunein", {})
        stations = data.get("response", {}).get("data", {}).get("stationlist", {}).get("station", {})

        if not stations:
            return []

        return [
            {
                "id": str(station["id"]),
                "name": f"""{station["name"]} - {station['genre']}""",
                "value": str(station["id"]),
                "genre": station["genre"],
                # "stream_url": self.get_station_stream_url(station["id"], tunin),
            }
            for station in stations
        ]

    def get_station_stream_url(self, station_id="", tunin = {}):
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

async def main():
    radio = ShoutcastRadio()
    stations = await radio.get_top_500_stations(async_request=True)

if __name__ == "__main__":
    # Run example
    asyncio.run(main())