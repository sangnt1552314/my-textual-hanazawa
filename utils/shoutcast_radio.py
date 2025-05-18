import os
import asyncio
import httpx
import requests
import xmltodict
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from urllib.parse import quote

try:
    import vlc
    VLC_AVAILABLE = True
except (ImportError, FileNotFoundError):
    VLC_AVAILABLE = False

load_dotenv()

SHOUTCAST_BASE_URL = "https://api.shoutcast.com"
YP_SHOUTCAST_URL = "http://yp.shoutcast.com"
TIMEOUT_DEFAULT = 5

class AudioPlayer(ABC):
    @abstractmethod
    def play_stream_url(self, url: str) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

class VLCPlayer(AudioPlayer):
    def __init__(self):
        self.player = None
        self.instance = None
        try:
            import vlc
            import platform
            if platform.system() == 'Windows':
                os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')
            # self.instance = vlc.Instance(['--no-video', '--quiet'])
            self.is_available = True
        except (ImportError, FileNotFoundError):
            self.is_available = False

    def play_stream_url(self, url: str) -> None:
        if not self.is_available:
            raise RuntimeError("VLC is not available. Cannot play audio.")
        
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

    def stop(self) -> None:
        if self.player:
            self.player.stop()
            self.player.release()
            self.player = None

class PygamePlayer(AudioPlayer):
    def __init__(self):
        try:
            import pygame
            pygame.mixer.init()
            self.is_available = True
        except ImportError:
            self.is_available = False
        self.current_stream = None

    def play_stream_url(self, url: str) -> None:
        if not self.is_available:
            raise RuntimeError("Pygame mixer is not available")
        try:
            import pygame
            pygame.mixer.music.load(url)
            pygame.mixer.music.play()
            self.current_stream = url
        except Exception as e:
            raise RuntimeError(f"Failed to play stream: {str(e)}")

    def stop(self) -> None:
        if self.is_available:
            import pygame
            pygame.mixer.music.stop()
            self.current_stream = None

class ShoutcastRadioPlayer:
    def __init__(self):
        self.players = []
        self.current_player = None
        
        # Try to initialize VLC player
        vlc_player = VLCPlayer()
        if vlc_player.is_available:
            self.players.append(vlc_player)
            
        # Try to initialize Pygame player
        pygame_player = PygamePlayer()
        if pygame_player.is_available:
            self.players.append(pygame_player)
            
        self.is_available = len(self.players) > 0

    def play_stream_url(self, url: str) -> None:
        """Play station in background using first available player."""
        if not self.is_available:
            raise RuntimeError("No audio players available. Install VLC or pygame.")
        
        if self.current_player:
            self.current_player.stop()
            
        for player in self.players:
            try:
                player.play_stream_url(url)
                self.current_player = player
                return
            except Exception as e:
                continue
                
        raise RuntimeError("All available players failed to play the stream")

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
                response = await client.get(f"{SHOUTCAST_BASE_URL}/legacy/genrelist", params=params, timeout=TIMEOUT_DEFAULT)
        else:
            response = requests.get(f"{SHOUTCAST_BASE_URL}/legacy/genrelist", params=params, timeout=TIMEOUT_DEFAULT)

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
                response = await client.get(f"{SHOUTCAST_BASE_URL}/legacy/Top500", params=params, timeout=TIMEOUT_DEFAULT)
        else:
            response = requests.get(f"{SHOUTCAST_BASE_URL}/legacy/Top500", params=params, timeout=TIMEOUT_DEFAULT)

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