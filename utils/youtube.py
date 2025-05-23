import os
import logging
import requests
from io import BytesIO
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytubefix.contrib.search import Search, Filter
from pytubefix import YouTube, Channel
import json

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

class YoutubeVideoService:
    def __init__(self, api_key: str = None, use_google_api: bool = True):
        self.api_key = api_key if api_key else os.getenv("YOUTUBE_API_KEY")
        self.use_google_api = use_google_api
        self.ascii_art_thumbnail_size = 20
        self.is_debug = False

    def search_video(self, query: str, max_results: int = 10, filters: dict = None) -> list:
        """
        Search for videos on YouTube using the Google API or pytubefix library.
        
        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.
            
        Returns:
            list: A list of video objects matching the search query.
        """
        if self.api_key and self.use_google_api:
            return self.search_video_googleapiclient(query=query, max_results=max_results, filters=filters)
        
        return self.search_video_pytube(query=query, max_results=max_results, filters=filters)

    def search_video_googleapiclient(self, query: str, max_results: int = 10, filters: dict = None) -> list:
        """
        Search for videos on YouTube using the Google API.
        
        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.
            
        Returns:
            list: A list of video objects matching the search query.
        """
        youtube = build("youtube", "v3", developerKey=self.api_key)
        if not youtube:
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

            request = youtube.search().list(**search_params)
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
                ascii_art_thumbnail = image_to_ascii(thumbnails.get("default", {}).get("url", ""), width=self.ascii_art_thumbnail_size)
                # todo: Add stream_url if needed
                
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
                    "ascii_art_thumbnail": ascii_art_thumbnail,
                })

            if self.is_debug:
                logger.debug(f"Search results: {json.dumps(videos, indent=2)}")
            
            return videos
        
        except HttpError as e:
            print(f"An error occurred: {e}")
            return []

    def search_video_pytube(self, query: str, max_results: int = 10, filters: dict = None) -> list:
        """
        Search for videos on YouTube using the pytubefix library.
        
        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.
            
        Returns:
            list: A list of video objects matching the search query.
        """
        s = Search(query, filters=self.build_filters_pytube(filters))
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
                "ascii_art_thumbnail": image_to_ascii(yt_video.thumbnail_url, width=self.ascii_art_thumbnail_size),
                # "stream_url": YouTube(yt_video.watch_url).streams.filter(only_audio=True).first().url
                **channel_data
            })

        if self.is_debug:
            logger.debug(f"Search results: {json.dumps(data, indent=2)}")

        return data
    
    def build_filters_pytube(self, filters: dict) -> dict:
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