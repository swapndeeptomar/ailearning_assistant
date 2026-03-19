import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def fetch_youtube_videos(search_query, max_results=3):
    """Hits the YouTube Data API and returns exactly 3 embeddable videos."""
    api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
    if not api_key:
        logger.error("YOUTUBE_API_KEY is missing from settings!")
        return []

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': search_query,
        'type': 'video',
        'videoEmbeddable': 'true', # CRITICAL: Ensures video plays in your app
        'maxResults': max_results,
        'key': api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            videos.append({
                'video_id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                # We pre-format the embed URL so React can just drop it into an iframe
                'embed_url': f"https://www.youtube.com/embed/{item['id']['videoId']}"
            })
            
        return videos
    except Exception as e:
        logger.error(f"YouTube API error: {e}")
        return []