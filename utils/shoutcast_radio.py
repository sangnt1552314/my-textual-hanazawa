from dotenv import load_dotenv
import os
import requests 
from urllib.parse import quote
from .constants import *

load_dotenv()

class ShoutcastRadio:
    def __init__(self, api_key = ''):
        self.api_key = os.getenv("SHOUTCAST_API_KEY") if api_key == '' else api_key

    def get_now_playing_stations(self, **kwargs):
        """
        Get the list of now playing stations.
        """
        ct = kwargs.get("ct", "")
        limit = kwargs.get("limit", 25)
        mt = kwargs.get("mt", "audio/mpeg")
        format = kwargs.get("format", "json")

        is_convert_to_textual = kwargs.get("is_convert_to_textual", True)
        
        params = {
            "ct": ct,
            "k": self.api_key,
            "limit": limit,
            "mt": mt,
            "f": format,
        }

        response = requests.get(f"{SHOUTCAST_BASE_URL}/station/nowplaying", params=params)

        if response.status_code != 200:
            raise Exception(f"Error fetching now playing stations: {response.status_code} - {response.text}")
        
        data = response.json()

        tunin = data.get("response", {}).get("data", {}).get("stationlist", {}).get("tunein", {})

        stations = data.get("response", {}).get("data", {}).get("stationlist", {}).get("station", {})
    
        if not stations:
            raise Exception("No stations found")
        
        station_options = [
            {
                "id": str(station["id"]),
                "name": f"""{station["name"]} - {station['genre']}""",
                "value": str(station["id"]),
                "genre": station["genre"],
                "stream_url": self._get_station_stream_url(station["id"], tunin),
            }
            for station in stations
        ]

        if is_convert_to_textual:
            textual_station_options = []
            textual_station_options.append(
                (
                    "ID", 
                    "Name", 
                    "Genre", 
                    "Stream URL",
                )
            )
            for station in station_options:
                textual_station_options.append(
                    (
                        station["id"], 
                        station["name"], 
                        station["genre"], 
                        station["stream_url"],
                    )
                )

            return textual_station_options

        return station_options

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