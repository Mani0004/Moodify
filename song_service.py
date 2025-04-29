import requests
import logging
import re
import urllib.parse
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SaavnService:
    """Service to interact with the JioSaavn API for retrieving songs based on mood."""
    
    BASE_URL = "https://saavn.dev/api"
    
    def __init__(self):
        self.session = requests.Session()
    
    def search_songs_by_mood(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for songs using JioSaavn API with focus on finding playable songs
        
        Args:
            query: The search query - can be a mood or a specific song/artist combination
            limit: Maximum number of songs to retrieve
            
        Returns:
            List of song objects with title, artist, image, and streaming URL
        """
        # Map moods to search queries if the query is a simple mood word
        mood_queries = {
            "Happy": ["upbeat happy songs", "feel good indian songs", "cheerful bollywood hits"],
            "Sad": ["sad emotional songs", "heartbreak bollywood", "melancholy hindi songs"],
            "Angry": ["powerful indian songs", "intense hindi tracks", "energetic bollywood"],
            "Anxious": ["calming indian songs", "peaceful hindi music", "soothing bollywood"],
            "Relaxed": ["chill relaxing songs", "peaceful indian classical", "soft bollywood melodies"],
            "Neutral": ["popular hindi songs", "trending indian music", "top bollywood hits"]
        }
        
        # If the query is just a mood keyword, use the first expanded query
        search_query = query
        if query in mood_queries:
            search_query = mood_queries[query][0]
        
        logger.info(f"Searching for songs with query: {search_query}")
        
        # We'll try up to 3 search queries to find playable songs
        all_queries = [search_query]
        
        # If this is a mood query, add alternate queries
        if query in mood_queries and len(mood_queries[query]) > 1:
            all_queries.extend(mood_queries[query][1:])
        
        # Store all found songs
        all_found_songs = []
        
        # Try each query until we have enough playable songs
        for current_query in all_queries:
            if len(all_found_songs) >= limit:
                break
                
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/search/songs",
                    params={"query": current_query, "limit": limit * 2}  # Request more than needed to filter
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("success") and "data" in data and "results" in data["data"]:
                    songs = data["data"]["results"]
                    formatted_songs = self._format_songs(songs)
                    
                    # Check each song for streamability
                    for song in formatted_songs:
                        # Get direct stream URLs for songs that don't have one
                        if not song.get("stream_url") and song.get("id"):
                            details = self.get_song_details(song["id"])
                            if details and "downloadUrl" in details and details["downloadUrl"]:
                                for url_obj in details["downloadUrl"]:
                                    if url_obj.get("quality") and url_obj.get("url"):
                                        song["stream_url"] = url_obj["url"]
                                        song["quality"] = url_obj["quality"]
                                        break
                        
                        # Only add songs that have stream URLs
                        if song.get("stream_url"):
                            # Add YouTube search URL as fallback
                            song["youtube_search"] = f"https://www.youtube.com/results?search_query={urllib.parse.quote(f'{song['title']} {song['artist']}')}"
                            
                            # Add a direct Saavn search link
                            song["saavn_search"] = f"https://www.jiosaavn.com/search/{urllib.parse.quote(f'{song['title']} {song['artist']}')}"
                            
                            # Add this song to our results
                            all_found_songs.append(song)
                            
                            # Break if we have enough songs
                            if len(all_found_songs) >= limit:
                                break
            
            except requests.exceptions.RequestException as e:
                logger.error(f"JioSaavn API request failed: {e}")
                continue
        
        # If we still don't have enough songs, we can try a more generic query
        if len(all_found_songs) < limit:
            try:
                generic_query = "popular bollywood songs"
                logger.info(f"Trying generic query: {generic_query}")
                
                response = self.session.get(
                    f"{self.BASE_URL}/search/songs",
                    params={"query": generic_query, "limit": limit * 2}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("success") and "data" in data and "results" in data["data"]:
                    songs = data["data"]["results"]
                    formatted_songs = self._format_songs(songs)
                    
                    # Get details for each song
                    for song in formatted_songs:
                        # Skip if we already have enough songs
                        if len(all_found_songs) >= limit:
                            break
                            
                        # Skip if this song is already in our list (check by title + artist)
                        song_key = f"{song.get('title', '')} {song.get('artist', '')}".lower()
                        if any(f"{s.get('title', '')} {s.get('artist', '')}".lower() == song_key for s in all_found_songs):
                            continue
                            
                        # Get stream URL if missing
                        if not song.get("stream_url") and song.get("id"):
                            details = self.get_song_details(song["id"])
                            if details and "downloadUrl" in details and details["downloadUrl"]:
                                for url_obj in details["downloadUrl"]:
                                    if url_obj.get("quality") and url_obj.get("url"):
                                        song["stream_url"] = url_obj["url"]
                                        song["quality"] = url_obj["quality"]
                                        break
                        
                        # Only add if it has a stream URL
                        if song.get("stream_url"):
                            song["youtube_search"] = f"https://www.youtube.com/results?search_query={urllib.parse.quote(f'{song['title']} {song['artist']}')}"
                            song["saavn_search"] = f"https://www.jiosaavn.com/search/{urllib.parse.quote(f'{song['title']} {song['artist']}')}"
                            all_found_songs.append(song)
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Generic query to JioSaavn API failed: {e}")
        
        return all_found_songs[:limit]
    
    def get_song_details(self, song_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific song
        
        Args:
            song_id: The JioSaavn ID of the song
            
        Returns:
            Song details including streaming URLs
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/songs/{song_id}")
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                return data["data"]
            else:
                logger.error(f"Error in API response structure: {data}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"JioSaavn API request failed: {e}")
            return {}
    
    def _format_songs(self, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format the raw API response into a cleaner structure for the application"""
        formatted_songs = []
        
        for song in songs:
            # Extract primary artist name(s)
            artists = []
            if "artists" in song and "primary" in song["artists"]:
                artists = [artist["name"] for artist in song["artists"]["primary"]]
            
            # Get the highest quality image URL
            image_url = ""
            if "image" in song and len(song["image"]) > 0:
                # Try to get the highest quality image
                for img in song["image"]:
                    if img.get("quality") == "500x500":
                        image_url = img.get("url", "")
                        break
                
                # If no 500x500 image found, use the first one
                if not image_url and len(song["image"]) > 0:
                    image_url = song["image"][0].get("url", "")
            
            # Get download URL for streaming
            stream_url = ""
            if "downloadUrl" in song and len(song["downloadUrl"]) > 0:
                # Try to get the highest quality audio
                for url in song["downloadUrl"]:
                    if url.get("quality") == "320kbps":
                        stream_url = url.get("url", "")
                        break
                
                # If no 320kbps found, use the first one
                if not stream_url and len(song["downloadUrl"]) > 0:
                    stream_url = song["downloadUrl"][0].get("url", "")
            
            formatted_songs.append({
                "id": song.get("id", ""),
                "title": song.get("name", "Unknown Title"),
                "artist": ", ".join(artists) if artists else "Unknown Artist",
                "image": image_url,
                "url": song.get("url", ""),  # JioSaavn web page URL
                "stream_url": stream_url,    # Direct streaming URL
                "duration": song.get("duration", 0)
            })
        
        return formatted_songs
        
    def get_youtube_embed_url(self, song_title: str, artist: str) -> str:
        """
        Create a YouTube embed URL for a song when direct streaming isn't available
        
        Args:
            song_title: Title of the song
            artist: Name of the artist
            
        Returns:
            YouTube embed URL for the song
        """
        search_query = f"{song_title} {artist} official audio"
        return f"https://www.youtube.com/embed?listType=search&list={urllib.parse.quote(search_query)}"