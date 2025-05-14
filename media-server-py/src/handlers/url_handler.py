from typing import Literal
from urllib.parse import urlparse
import yt_dlp

MediaType = Literal['youtube-music', 'youtube-video', 'invalid']

SUPPORTED_DOMAINS = {
    'youtube.com',
    'youtu.be',
    'music.youtube.com',
    'www.youtube.com'  # Adding www subdomain which is common
}

async def identify_url(url: str) -> MediaType:
    """
    Identifies and validates a URL to determine its media type.
    """
    try:
        print(f"Identifying URL: {url}")
        media_type = determine_media_type(url)
        if media_type == 'invalid':
            return media_type

        # Validate URL using yt-dlp
        # try:
        #     ydl_opts = {'quiet': True}
        #     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #         ydl.extract_info(url, download=False)
        #     return media_type
        # except yt_dlp.utils.DownloadError:
        #     print(f"Unable to validate URL with yt-dlp: {url}")
        #     return 'invalid'
        # except Exception as e:
        #     print(f"Unexpected error validating URL: {e}")
        #     return 'invalid'
        return media_type
    except Exception as e:
        print(f"Error in identify_url: {e}")
        return 'invalid'

def determine_media_type(url: str) -> MediaType:
    """
    Determines the media type based on the URL structure.
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc.lower()
        
        if hostname not in SUPPORTED_DOMAINS:
            return 'invalid'
        
        # Check if it's a music URL
        if (hostname == 'music.youtube.com' or 
            ('list' in parsed_url.query and 
             any(domain in hostname for domain in ['youtube.com', 'www.youtube.com']))):
            return 'youtube-music'
        
        return 'youtube-video'
    except Exception:
        return 'invalid' 