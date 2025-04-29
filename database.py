from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Database:
    def __init__(self):
        try:
            # Properly escape credentials
            username = quote_plus(os.getenv("MONGO_USERNAME"))
            password = quote_plus(os.getenv("MONGO_PASSWORD"))
            cluster = os.getenv("MONGO_CLUSTER")
            
            self.uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
            
            self.client = MongoClient(
                self.uri,
                connectTimeoutMS=30000,
                serverSelectionTimeoutMS=50000,
                srvServiceName='mongodb'
            )
            
            # Test connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            
            self.db = self.client["mood_music_db"]
            self.conversations = self.db["conversations"]
            self.recommendations = self.db["recommendations"]
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            raise

    def save_conversation(self, user_id, messages):
        """Save conversation history to database"""
        try:
            self.conversations.insert_one({
                "user_id": user_id,
                "messages": messages,
                "timestamp": datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False

    def save_recommendation(self, user_id, mood, recommendations):
        """Save music recommendations to database"""
        try:
            self.recommendations.insert_one({
                "user_id": user_id,
                "mood": mood,
                "recommendations": recommendations,
                "timestamp": datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error saving recommendation: {e}")
            return False

    def get_user_history(self, user_id, limit=5):
        """Get user's mood history"""
        try:
            return list(self.recommendations.find(
                {"user_id": user_id},
                {"_id": 0, "mood": 1, "timestamp": 1, "recommendations": 1}
            ).sort("timestamp", -1).limit(limit))
        except Exception as e:
            print(f"Error getting user history: {e}")
            return []

    def get_conversation_history(self, user_id, limit=1):
        """Get user's conversation history"""
        try:
            return list(self.conversations.find(
                {"user_id": user_id},
                {"_id": 0, "messages": 1, "timestamp": 1}
            ).sort("timestamp", -1).limit(limit))
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    def close_connection(self):
        """Close database connection"""
        try:
            self.client.close()
            print("Database connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")

# Create database instance
db = Database()