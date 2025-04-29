import requests
import logging
import random
import json
import urllib.parse
from typing import List, Dict, Any
from song_service import SaavnService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MusicRecommender:
    def __init__(self, gemini_client=None):
        # Initialize song service
        self.saavn_service = SaavnService()
        
        # Store Gemini client for AI-generated recommendations
        self.gemini_client = gemini_client
        self.model_name = "gemini-2.0-flash"
        
        # Mock data for fallback
        self._initialize_mock_data()
    
    def recommend_songs(self, mood: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Recommend songs based on the provided mood using a combination of approaches to ensure playable songs.
        
        Args:
            mood: The detected mood (Happy, Sad, Angry, Anxious, Relaxed, Neutral)
            limit: Maximum number of songs to recommend
            
        Returns:
            List of song recommendations that are guaranteed to be playable
        """
        logger.info(f"Finding personalized music recommendations for mood: {mood}")
        
        # Try to get recommendations from Gemini first for personalization
        if self.gemini_client:
            try:
                gemini_songs = self._generate_song_recommendations_with_gemini(mood, limit)
                if gemini_songs and len(gemini_songs) >= limit:
                    logger.info(f"Using Gemini AI personalized recommendations for {mood} mood")
                    return gemini_songs
                elif gemini_songs:
                    # If we got some songs but not enough, we'll use them and supplement with direct songs
                    logger.info(f"Got {len(gemini_songs)} Gemini recommendations, supplementing with direct search")
                    remaining = limit - len(gemini_songs)
                    direct_songs = self._get_direct_playable_songs(mood, remaining)
                    
                    # Combine both sets, ensuring no duplicates
                    existing_titles = set(f"{song['title']} {song['artist']}".lower() for song in gemini_songs)
                    combined_songs = gemini_songs.copy()
                    
                    for song in direct_songs:
                        song_key = f"{song['title']} {song['artist']}".lower()
                        if song_key not in existing_titles:
                            combined_songs.append(song)
                            existing_titles.add(song_key)
                            
                            # Stop when we have enough songs
                            if len(combined_songs) >= limit:
                                break
                                
                    return combined_songs
            except Exception as e:
                logger.error(f"Failed to get Gemini recommendations: {e}")
        
        # If Gemini approach failed or not available, try direct Saavn search
        direct_songs = self._get_direct_playable_songs(mood, limit)
        if direct_songs:
            logger.info(f"Using direct Saavn search for {mood} mood")
            return direct_songs
            
        # Last resort: Get generic songs by mood from Saavn
        logger.info(f"Falling back to basic mood search for {mood}")
        saavn_songs = self.saavn_service.search_songs_by_mood(mood, limit=limit)
        
        # Filter to ensure we only return songs with stream URLs
        playable_songs = [song for song in saavn_songs if song.get("stream_url")]
        
        return playable_songs
    
    def _generate_song_recommendations_with_gemini(self, mood: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Generate song recommendations using Gemini AI with guaranteed playable songs"""
        # Request more songs than needed to ensure we get enough playable ones
        request_limit = limit * 3
        
        prompt = f"""
        Generate {request_limit} song recommendations for someone feeling {mood}.
        
        FOCUS ON:
        1. ONLY songs that are DEFINITELY available on JioSaavn streaming service
        2. Popular Indian songs in Hindi, Tamil, Telugu, and other Indian languages
        3. Songs that perfectly match the {mood} mood with appropriate lyrics and tone
        4. A mix of latest hits and some timeless classics
        5. Diverse artists and music styles
        6. Each recommendation should be personalized and unique
        
        Respond ONLY with a JSON array of songs in the following format:
        [
            {{
                "title": "Song Title",
                "artist": "Artist Name",
                "language": "Hindi/Tamil/English/etc.",
                "album": "Album Name",
                "year": "Release Year",
                "mood_match": "Brief explanation of why this song fits the {mood} mood"
            }}
        ]
        
        IMPORTANT: 
        1. Include all fields for every song
        2. Choose ONLY songs that are popular and definitely available on JioSaavn
        3. NO obscure or niche songs that might not be available
        4. Respond ONLY with the JSON array - no text before or after
        """
        
        try:
            # Get recommendations from Gemini
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            response_text = response.text.strip()
            
            # Parse JSON from the response
            try:
                # Find JSON content in the response
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
                
                songs = json.loads(response_text)
                
                # Process songs and verify they're playable on Saavn
                verified_songs = []
                unique_titles = set()  # Track unique song titles to avoid duplicates
                
                # Process each recommended song
                for song in songs:
                    # Skip if we already have enough verified songs
                    if len(verified_songs) >= limit:
                        break
                    
                    # Create a well-formatted search query for Saavn
                    search_query = f"{song['title']} {song['artist']}"
                    
                    # Skip duplicate songs
                    normalized_title = search_query.lower()
                    if normalized_title in unique_titles:
                        continue
                    
                    # Search for the song on Saavn
                    saavn_results = self.saavn_service.search_songs_by_mood(search_query, limit=2)
                    
                    # Only add songs that are found on Saavn and have stream_url
                    for result in saavn_results:
                        if result.get("stream_url") and result.get("title"):
                            # Add mood context from Gemini to the result
                            if 'mood_match' in song:
                                result['mood_match'] = song['mood_match']
                                
                            verified_songs.append(result)
                            unique_titles.add(normalized_title)
                            break
                
                # If we don't have enough songs, try a broader search
                if len(verified_songs) < limit:
                    # Try searching directly with mood-based queries for the remaining slots
                    mood_queries = {
                        "Happy": ["popular happy songs indian", "upbeat bollywood songs", "cheerful hindi songs"],
                        "Sad": ["emotional bollywood songs", "sad hindi songs", "melancholy indian music"],
                        "Angry": ["intense indian songs", "powerful bollywood tracks", "aggressive hindi music"],
                        "Anxious": ["calming indian songs", "soothing bollywood music", "peaceful hindi tracks"],
                        "Relaxed": ["chill bollywood songs", "relaxing indian music", "peaceful hindi songs"],
                        "Neutral": ["popular bollywood hits", "trending indian songs", "classic hindi tracks"]
                    }
                    
                    # Get queries for the current mood
                    queries = mood_queries.get(mood, ["popular indian songs"])
                    
                    # Try each query until we have enough songs
                    for query in queries:
                        if len(verified_songs) >= limit:
                            break
                            
                        additional_songs = self.saavn_service.search_songs_by_mood(query, limit=3)
                        for song in additional_songs:
                            if song.get("stream_url") and song.get("title"):
                                normalized_title = f"{song.get('title')} {song.get('artist')}".lower()
                                if normalized_title not in unique_titles:
                                    verified_songs.append(song)
                                    unique_titles.add(normalized_title)
                                    
                                    if len(verified_songs) >= limit:
                                        break
                
                return verified_songs[:limit]
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}\nResponse was: {response_text}")
                return self._get_direct_playable_songs(mood, limit)
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return self._get_direct_playable_songs(mood, limit)
            
    def _get_direct_playable_songs(self, mood: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Get playable songs directly from Saavn without using fallback mock data"""
        # These queries are designed to return playable songs on Saavn
        mood_specific_queries = {
            "Happy": ["popular happy songs indian", "upbeat bollywood hits", "cheerful hindi songs", "feel good tamil songs"],
            "Sad": ["emotional bollywood songs", "sad hindi hits", "melancholy indian music", "heartbreak songs tamil"],
            "Angry": ["powerful bollywood tracks", "intense hindi songs", "aggressive indian music", "rap hindi songs"],
            "Anxious": ["calming indian songs", "soothing bollywood music", "peaceful hindi tracks", "meditation music india"],
            "Relaxed": ["chill bollywood songs", "relaxing indian music", "peaceful hindi songs", "soft tamil melodies"],
            "Neutral": ["trending bollywood songs", "top hindi hits", "popular indian songs 2024", "viral indian music"]
        }
        
        # Get relevant queries for the current mood
        queries = mood_specific_queries.get(mood, ["popular bollywood songs"])
        
        # Track unique songs
        verified_songs = []
        unique_titles = set()
        
        # Try each query until we have enough songs
        for query in queries:
            if len(verified_songs) >= limit:
                break
                
            results = self.saavn_service.search_songs_by_mood(query, limit=5)
            for song in results:
                if song.get("stream_url") and song.get("title"):
                    normalized_title = f"{song.get('title')} {song.get('artist')}".lower()
                    if normalized_title not in unique_titles:
                        verified_songs.append(song)
                        unique_titles.add(normalized_title)
                        
                        if len(verified_songs) >= limit:
                            break
        
        return verified_songs

    def _initialize_mock_data(self):
        """Initialize mock song recommendations for each mood"""
        self.mock_data = {
            "Happy": [
                {"title": "Happy", "artist": "Pharrell Williams", "url": "https://open.spotify.com/track/1z6WtY7X4HQJvzxC4UgkSf", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273f9208c46cef5d5695a8b8394"},
                {"title": "Can't Stop the Feeling!", "artist": "Justin Timberlake", "url": "https://open.spotify.com/track/1WkMMavIMc4JZ8cfMmxHkI", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273ca4d52e81604d5fb37b907f7"},
                {"title": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "url": "https://open.spotify.com/track/32OlwWuMpZ6b0aN2RZOeMS", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2736accf4971a1f334c68e9e044"},
                {"title": "Good as Hell", "artist": "Lizzo", "url": "https://open.spotify.com/track/6KgBpzTuTRPebChN0VTyzV", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2739d9771f82c63ddb907b8d18e"},
                {"title": "Don't Stop Me Now", "artist": "Queen", "url": "https://open.spotify.com/track/5T8EDUDqKcs6OSOwEsfqG7", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2737c39dd9ad2f5e7fdee513547"},
                {"title": "Walking On Sunshine", "artist": "Katrina & The Waves", "url": "https://open.spotify.com/track/05wIrZSwuaVWhcv5FfqeH0", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273920dc1b272e5e4afd755b04b"}
            ],
            "Sad": [
                {"title": "Someone Like You", "artist": "Adele", "url": "https://open.spotify.com/track/4qoBlK4GEBzF7pfUeId5vq", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273d3d53760259c6b19b72464b9"},
                {"title": "Hurt", "artist": "Johnny Cash", "url": "https://open.spotify.com/track/28cnXtME493VX9NOw9cIUh", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2735f4e5482e934e31d52e6f39c"},
                {"title": "Fix You", "artist": "Coldplay", "url": "https://open.spotify.com/track/7LVHVU3tWfcxj5aiPFEW4Q", 
                 "image": "https://i.scdn.co/image/ab67616d0000b27309fd83d32aee93dceba78517"},
                {"title": "When the Party's Over", "artist": "Billie Eilish", "url": "https://open.spotify.com/track/43zdsphuZLzwA9k4DJhU0I", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2737005885df706891a3c182a57"},
                {"title": "All I Want", "artist": "Kodaline", "url": "https://open.spotify.com/track/7q2rPv1xYBuyhDOZqPwkQ5", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273f5dac9ef7300c786bda7d955"},
                {"title": "Everybody Hurts", "artist": "R.E.M.", "url": "https://open.spotify.com/track/1quRQmg5KH5WF2PcK3y6Cr", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273e488f16b4631c41c8dda2bae"}
            ],
            "Angry": [
                {"title": "Break Stuff", "artist": "Limp Bizkit", "url": "https://open.spotify.com/track/5cZqsjJeZO7Z4hxHJuTgah", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273f0d2d02dafe49eec2cfa54b1"},
                {"title": "Killing in the Name", "artist": "Rage Against the Machine", "url": "https://open.spotify.com/track/59WN2psjkt1tyaxjspN8fp", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2737ba56b2e23f0c6886de08e97"},
                {"title": "Last Resort", "artist": "Papa Roach", "url": "https://open.spotify.com/track/5W8YXBz6MTQnj4qXzR6eVR", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273cb81eb3c1238d50b7acbb79f"},
                {"title": "Numb", "artist": "Linkin Park", "url": "https://open.spotify.com/track/2nLtzopw4rPReszdYBJU6h", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2736a450a9ca93c1d1c10d2f0df"},
                {"title": "Down with the Sickness", "artist": "Disturbed", "url": "https://open.spotify.com/track/40rvBMQizxkIqnjPdEWY1v", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273689ef07e0830d1b3fb22440b"},
                {"title": "I Hate Everything About You", "artist": "Three Days Grace", "url": "https://open.spotify.com/track/0M955bMOoilikPXwKLYpoi", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273ed75ea4d6b295adb36fb169d"}
            ],
            "Anxious": [
                {"title": "Breathe Me", "artist": "Sia", "url": "https://open.spotify.com/track/5rX6C5QVvvZB7XckETNych", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273b8b7594c979cd0c367489256"},
                {"title": "Weightless", "artist": "Marconi Union", "url": "https://open.spotify.com/track/0gZQWi4P7fJkWcC9lca9WJ", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2733610a0c193690951dcfc4c59"},
                {"title": "Intro", "artist": "The xx", "url": "https://open.spotify.com/track/2DnJjbjNTV9Nd5NOa1KGba", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273ada101c2e9e97feb8fae37a9"},
                {"title": "Mad World", "artist": "Gary Jules", "url": "https://open.spotify.com/track/3JOVTQ5h8HGFnDdp4VT3MP", 
                 "image": "https://i.scdn.co/image/ab67616d0000b27363e77bc1700f3bf803a22aea"},
                {"title": "Chasing Cars", "artist": "Snow Patrol", "url": "https://open.spotify.com/track/11bD1JtSjlIgKgZG2134DZ", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2735f0f7895b5dea2e13161bccc"},
                {"title": "The Scientist", "artist": "Coldplay", "url": "https://open.spotify.com/track/75JFxkI2RXiU7L9VXzMkle", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273f0493b4a5314c0c891e93432"}
            ],
            "Relaxed": [
                {"title": "Dreams", "artist": "Fleetwood Mac", "url": "https://open.spotify.com/track/0ofHAoxe9vBkTCp2UQIavz", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273e52a59a28efa4773dd2bfe1b"},
                {"title": "Clair de Lune", "artist": "Claude Debussy", "url": "https://open.spotify.com/track/5QTxFnGygVM4jFQiBovmRo", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273906d11c397c98725d6cba474"},
                {"title": "Gymnopédie No.1", "artist": "Erik Satie", "url": "https://open.spotify.com/track/5NGtFXVpXSvwunfCZzbV8b", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273161ed4beedc761e729573b88"},
                {"title": "The Girl from Ipanema", "artist": "Stan Getz & Astrud Gilberto", "url": "https://open.spotify.com/track/5kTyKj4tKKs7a75ErmiPZl", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273ef16c15ac30f14ff195b6d55"},
                {"title": "River Flows in You", "artist": "Yiruma", "url": "https://open.spotify.com/track/20iCRJgi3IK7O25rq7YPI8", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2738ec71d8a129beca9cb315043"},
                {"title": "Watermark", "artist": "Enya", "url": "https://open.spotify.com/track/0GBQ8OH1vLlGgHOKYjKqEO", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273546d02f29bc520ea49b2393f"}
            ],
            "Neutral": [
                {"title": "Starboy", "artist": "The Weeknd ft. Daft Punk", "url": "https://open.spotify.com/track/7MXVkk9YMctZqd1Srtv4MB", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273a048415db06a5b6fa7ec4e1a"},
                {"title": "Shape of You", "artist": "Ed Sheeran", "url": "https://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96"},
                {"title": "Don't Start Now", "artist": "Dua Lipa", "url": "https://open.spotify.com/track/3PfIrDoz19wz7qK7tYeu62", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273d4daf28d55fe5050a26cf730"},
                {"title": "bad guy", "artist": "Billie Eilish", "url": "https://open.spotify.com/track/2Fxmhks0bxGSBdJ92vM42m", 
                 "image": "https://i.scdn.co/image/ab67616d0000b2732a038d3bf875d23e4aeaa84e"},
                {"title": "Sunflower", "artist": "Post Malone, Swae Lee", "url": "https://open.spotify.com/track/0RiRZpuVDfi9ytboZQXbo0", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273e2e352d89826aef6dbd5ff8f"},
                {"title": "Blinding Lights", "artist": "The Weeknd", "url": "https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b", 
                 "image": "https://i.scdn.co/image/ab67616d0000b273b5d7fd7a54e7ffc047347369"}
            ]
        }
    
    def _get_mock_recommendations(self, mood: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Get mock recommendations for the given mood"""
        if mood in self.mock_data:
            return self.mock_data[mood][:limit]
        else:
            # Default to neutral mood if the provided mood is not found
            return self.mock_data["Neutral"][:limit]