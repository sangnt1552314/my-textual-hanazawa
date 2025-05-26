import os
import logging
import requests
import json
from io import BytesIO
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytubefix.contrib.search import Search, Filter
from pytubefix import YouTube, Channel
import yt_dlp

logging.basicConfig(
    filename=f"dev.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='w'  # a = append, w = overwrite
)
logger = logging.getLogger(__name__)

def image_to_ascii(url, width=40):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img = img.resize((width, int(img.height * width / img.width)))
    img = img.convert("L")  # Convert to grayscale
    pixels = img.getdata()
    ascii_chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@", "8"]
    new_pixels = [ascii_chars[pixel // 25] for pixel in pixels]
    new_image = "".join(
        ["".join(new_pixels[index : index + width]) + "\n"
            for index in range(0, len(new_pixels), width)]
    )
    return new_image

class BaseYoutubeService:
    def __init__(self, is_debug: bool = False):
        self.is_debug = is_debug

    def search_video(self, query: str, max_results: int = 10, filters: dict = None) -> list:
        """
        Search for videos on YouTube.

        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.

        Returns:
            list: A list of video objects matching the search query.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


class YoutubeServiceGoogleAPIClient(BaseYoutubeService):
    def __init__(self, api_key: str = None, is_debug: bool = False):
        self.api_key = api_key if api_key else os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YouTube API key is required")
        self.is_debug = is_debug
        self.youtube_build = build("youtube", "v3", developerKey=self.api_key)

    def search_video(self, query: str, max_results: int = 10, filters: dict = None) -> list:
        """
        Search for videos on YouTube using the Google API.

        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.

        Returns:
            list: A list of video objects matching the search query.
        """
        if not self.youtube_build:
            raise RuntimeError("YouTube API client is not available. Check your API key.")

        try:
            search_params = {
                "q": query,
                "part": "id,snippet",
                "maxResults": min(max_results, 50),
                "type": "video",
            }

            if filters:
                search_params.update(filters)

            request = self.youtube_build.search().list(**search_params)
            response = request.execute()

            videos = []

            for item in response.get("items", []):
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                description = item["snippet"]["description"]
                channel_title = item["snippet"]["channelTitle"]
                channel_id = item["snippet"]["channelId"]
                thumbnails = item["snippet"]["thumbnails"]
                watch_url = f"https://www.youtube.com/watch?v={video_id}"
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                views = 0  # Placeholder, as views are not available in search results
                length = 0  # Placeholder, as length is not available in search results

                videos.append({
                    "video_id": video_id,
                    "title": title,
                    "description": description,
                    "channel_title": channel_title,
                    "channel_id": channel_id,
                    "thumbnails": thumbnails,
                    "watch_url": watch_url,
                    "embed_url": embed_url,
                    "title": title,
                    "views": views,
                    "length": length,
                })

            if self.is_debug:
                logger.debug(f"Search results: {json.dumps(videos, indent=2)}")

            return videos

        except HttpError as e:
            logger.error(f"An error occurred in YoutubeVideoGoogleAPIClient: {e}")
            return []


class YoutubeServicePyTube(BaseYoutubeService):
    def __init__(self, is_debug: bool = False):
        self.is_debug = is_debug

    def search_video(self, query: str, max_results: int = 10, filters: dict = None) -> list:
        """
        Search for videos on YouTube using the pytubefix library.

        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.

        Returns:
            list: A list of video objects matching the search query.
        """
        s = Search(query, filters=self.build_filters(filters))
        videos = s.videos
        videos = videos[:max_results]

        data = []

        for video in videos:
            yt_video = YouTube(url=video.watch_url)
            channel_data = {}
            try:
                channel = Channel(url=yt_video.channel_url)
                channel_data = {
                    "channel_title": channel.title,
                }
            except Exception as e:
                channel_data = {
                    "channel_title": "",
                }

            data.append({
                "video_id": yt_video.video_id,
                "title": yt_video.title,
                "description": yt_video.description,
                "channel_id": yt_video.channel_id,
                "thumbnails": {
                    "default": {
                        "url": yt_video.thumbnail_url,
                    },
                },
                "watch_url": yt_video.watch_url,
                "embed_url": yt_video.embed_url,
                "views": yt_video.views,
                "length": int(yt_video.length),
                **channel_data
            })

        if self.is_debug:
            logger.debug(f"Search results: {json.dumps(data, indent=2)}")

        return data

    def get_video_audio_url(self, video_id: str) -> str:
        """
        Build the stream URL for a YouTube video using pytubefix.

        Args:
            video_id (str): The ID of the YouTube video.

        Returns:
            str: The stream URL for the video.
        """
        yt_video = YouTube(url=f"https://www.youtube.com/watch?v={video_id}")

        if not yt_video:
            raise RuntimeError("YouTube video is not available. Check the video ID.")

        stream = yt_video.streams.filter(only_audio=True).first()

        if not stream:
            raise RuntimeError("No audio stream available for this video.")

        return stream.url
    
    def get_video_duration(self, video_id: str) -> int:
        """
        Get the duration of a video in seconds.
        """
        yt_video = YouTube(url=f"https://www.youtube.com/watch?v={video_id}")
        return int(yt_video.length)

    def build_filters(self, filters: dict) -> dict:
        """
        Build filters for pytubefix search.

        Args:
            filters (dict): A dictionary of filters to apply.

        Returns:
            list: A list of Filter objects.
        """
        processed_filter = {}

        #TODO: Add more filters and build later

        return processed_filter


class YoutubeServiceYTDLP(BaseYoutubeService):
    def __init__(self, is_debug: bool = False):
        self.is_debug = is_debug

    def search_video(self, query: str, max_results: int = 10, filters: dict = None) -> list:
        """
        Search for videos on YouTube using yt-dlp.

        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.

        Returns:
            list: A list of video objects matching the search query.
        """

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'max_downloads': max_results,
        }

        if filters:
            ydl_opts.update(filters)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                result = ydl.extract_info(query, download=False)
                if 'entries' in result:
                    return result['entries']
                else:
                    return [result]
            except Exception as e:
                logger.error(f"Error searching videos with yt-dlp: {str(e)}")
                return []

    def get_video_audio_url(self, video_id: str, start_time: int = None, end_time: int = None) -> str:
        """
        Build the stream URL for a YouTube video using yt-dlp, optionally with time constraints.

        Args:
            video_id (str): The ID of the YouTube video.
            start_time (int, optional): Start time in seconds.
            end_time (int, optional): End time in seconds.

        Returns:
            str: The direct audio stream URL for the video, with time constraints if specified.
        """

        url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            'format': 'bestaudio',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        # Add timestamp constraints if provided
        if start_time is not None or end_time is not None:
            download_range = ''
            if start_time is not None:
                download_range += str(start_time)
            download_range += '-'
            if end_time is not None:
                download_range += str(end_time)
            
            ydl_opts.update({
                'download_ranges': lambda info: [[download_range]],
                'force_keyframes_at_cuts': True,
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'url' in info:
                    base_url = info['url']
                    # Add timestamp parameters to URL if specified
                    if start_time is not None:
                        base_url += f"&begin={start_time}"
                    return base_url
                else:
                    raise RuntimeError("Could not extract audio URL from video")
        except Exception as e:
            logger.error(f"Error getting audio URL with yt-dlp: {str(e)}")
            raise RuntimeError(f"Failed to get audio URL: {str(e)}")

    def get_video_duration(self, video_id: str) -> int:
        """
        Get the duration of a video in seconds.

        Args:
            video_id (str): The ID of the YouTube video.

        Returns:
            int: Duration of the video in seconds.
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('duration', 0)
        except Exception as e:
            logger.error(f"Error getting video duration: {str(e)}")
            return 0


class YoutubeVideoService(BaseYoutubeService):
    def __init__(self, is_debug: bool = False):
        self.is_debug = is_debug
        self.services = []

        # Initialize services
        self.services.append(YoutubeServiceGoogleAPIClient(is_debug=self.is_debug))
        self.services.append(YoutubeServiceYTDLP(is_debug=self.is_debug))
        self.services.append(YoutubeServicePyTube(is_debug=self.is_debug))

    def search_video(self, query: str, max_results: int = 10, filters: dict = None) -> list:
        """
        Search for videos on YouTube using the Google API or pytubefix library.

        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.

        Returns:
            list: A list of video objects matching the search query.
        """
        for service in self.services:
            try:
                return service.search_video(query, max_results, filters)
            except Exception as e:
                logger.error(f"Error searching videos with {service.__class__.__name__}: {str(e)}")
                continue
        raise RuntimeError("All services failed to search videos.")

    def get_video_audio_url(self, video_id: str, start_time: int = None, end_time: int = None) -> str:
        """
        Build the audio URL for a YouTube video with optional time constraints.
        Will try the preferred method first, then fall back to others if it fails.

        Args:
            video_id (str): The ID of the YouTube video.
            start_time (int, optional): Start time in seconds.
            end_time (int, optional): End time in seconds.

        Returns:
            str: The direct audio stream URL for the video.

        Raises:
            RuntimeError: If all services fail to get the audio URL.
        """
        # If timestamps are provided, use YT-DLP service first as it has the best timestamp support
        if start_time is not None or end_time is not None:
            ytdlp_service = next((s for s in self.services if isinstance(s, YoutubeServiceYTDLP)), None)
            if ytdlp_service:
                try:
                    return ytdlp_service.get_video_audio_url(video_id, start_time, end_time)
                except Exception as e:
                    logger.error(f"Error getting audio URL with YT-DLP: {str(e)}")

        # Try other services as fallback (without timestamp support)
        for service in self.services:
            try:
                return service.get_video_audio_url(video_id)
            except Exception as e:
                logger.error(f"Error getting audio URL with {service.__class__.__name__}: {str(e)}")
                continue
        raise RuntimeError("All services failed to get audio URL.")

    def get_video_duration(self, video_id: str) -> int:
        """
        Get the duration of a video in seconds.

        Args:
            video_id (str): The ID of the YouTube video.

        Returns:
            int: Duration of the video in seconds.
        """
        # Try YT-DLP service first as it's more reliable
        ytdlp_service = next((s for s in self.services if isinstance(s, YoutubeServiceYTDLP)), None)
        if ytdlp_service:
            try:
                return ytdlp_service.get_video_duration(video_id)
            except Exception as e:
                logger.error(f"Error getting video duration with YT-DLP: {str(e)}")

        # Try other services as fallback
        for service in self.services:
            try:
                return service.get_video_duration(video_id)
            except Exception as e:
                logger.error(f"Error getting video duration with {service.__class__.__name__}: {str(e)}")
                continue
        raise RuntimeError("All services failed to get video duration.")
