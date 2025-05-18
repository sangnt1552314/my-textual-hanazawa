import httpx
from dotenv import load_dotenv
import os
import requests 
import vlc
from urllib.parse import quote
from .constants import *

load_dotenv()

class ShoutcastRadioPlayer:
    def __init__(self):
        self.player = None
        self.instance = None

    def play_stream_url(self, url: str) -> None:
        """Play station in background."""
        if self.player is not None:
            self.player.stop()
            self.player.release()
        if self.instance is not None:
            self.instance.release()

        self.instance = vlc.Instance(['--no-video', '--quiet'])
        self.player = self.instance.media_player_new()
        media = self.instance.media_new(url)
        self.player.set_media(media)
        self.player.play()

class ShoutcastRadio:
    def __init__(self, api_key = ''):
        self.api_key = api_key or os.getenv("SHOUTCAST_API_KEY")
        if not self.api_key:
            raise ValueError("Shoutcast API key is required")


    async def get_now_playing_stations(self, **kwargs):
        """
        Get the list of now playing stations. Supports both async and sync operations.
        """
        params = {
            "ct": kwargs.get("ct", ""),
            "k": self.api_key,
            "limit": kwargs.get("limit", 25),
            "mt": kwargs.get("mt", "audio/mpeg"),
            "f": kwargs.get("format", "json"),
        }

        # Handle both async and sync requests
        if kwargs.get("async_request", False):
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{SHOUTCAST_BASE_URL}/station/nowplaying", params=params)
        else:
            response = requests.get(f"{SHOUTCAST_BASE_URL}/station/nowplaying", params=params)

        if response.status_code != 200:
            raise Exception(f"Error fetching now playing stations: {response.status_code} - {response.text}")

        data = response.json()
        tunin = data.get("response", {}).get("data", {}).get("stationlist", {}).get("tunein", {})
        stations = data.get("response", {}).get("data", {}).get("stationlist", {}).get("station", {})

        if not stations:
            return []

        return [
            {
                "id": str(station["id"]),
                "name": f"""{station["name"]} - {station['genre']}""",
                "value": str(station["id"]),
                "genre": station["genre"],
                "stream_url": self._get_station_stream_url(station["id"], tunin),
            }
            for station in stations
        ]

    def _get_station_stream_url(self, station_id="", tunin = {}):
        """
        Get the stream URL for a given station ID.
        """
        if station_id == "":
            return ''

        if not tunin:
            return ''

        tunin_base = tunin.get("base", "")
        # tunin_base_m3u = tunin.get("base-m3u", "")
        # tunin_base_xspf = tunin.get("base-xspf", "")

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

if __name__ == "__main__":
    # Example usage
    radio = ShoutcastRadio()
    stations = radio.get_now_playing_stations(ct="uk", limit=10)
    for station in stations:
        print(f"Station ID: {station['id']}")
        print(f"Station Name: {station['name']}")
        print(f"Station Genre: {station['genre']}")
        print(f"Stream URL: {station['stream_url']}")
        print()