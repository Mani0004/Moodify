from datetime import datetime
import json
import os
import time

class Database:
    def __init__(self):
        try:
            # Create data directory if it doesn't exist
            self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            self.conversations_file = os.path.join(self.data_dir, "conversations.json")
            self.recommendations_file = os.path.join(self.data_dir, "recommendations.json")
            
            # Initialize data storage
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Initialize empty files if they don't exist
            if not os.path.exists(self.conversations_file):
                with open(self.conversations_file, "w") as f:
                    json.dump([], f)
            
            if not os.path.exists(self.recommendations_file):
                with open(self.recommendations_file, "w") as f:
                    json.dump([], f)
                    
            print("Local file database initialized at", self.data_dir)
        except Exception as e:
            print(f"Error initializing database: {e}")

    def _read_json_file(self, file_path):
        """Helper method to read JSON file"""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []

    def _write_json_file(self, file_path, data):
        """Helper method to write JSON file"""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, default=str)
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False

    def save_conversation(self, user_id, messages):
        """Save conversation history to file"""
        try:
            conversations = self._read_json_file(self.conversations_file)
            conversations.append({
                "user_id": user_id,
                "messages": messages,
                "timestamp": datetime.now().isoformat()
            })
            return self._write_json_file(self.conversations_file, conversations)
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False

    def save_recommendation(self, user_id, mood, recommendations):
        """Save music recommendations to file"""
        try:
            recs = self._read_json_file(self.recommendations_file)
            recs.append({
                "user_id": user_id,
                "mood": mood,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            })
            return self._write_json_file(self.recommendations_file, recs)
        except Exception as e:
            print(f"Error saving recommendation: {e}")
            return False

    def get_user_history(self, user_id, limit=5):
        """Get user's mood history"""
        try:
            recs = self._read_json_file(self.recommendations_file)
            # Filter by user_id
            user_recs = [r for r in recs if r["user_id"] == user_id]
            # Sort by timestamp (newest first)
            user_recs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            # Convert timestamps back to datetime objects
            for rec in user_recs[:limit]:
                if isinstance(rec["timestamp"], str):
                    try:
                        rec["timestamp"] = datetime.fromisoformat(rec["timestamp"])
                    except ValueError:
                        # If parsing fails, create a datetime object
                        rec["timestamp"] = datetime.now()
            return user_recs[:limit]
        except Exception as e:
            print(f"Error getting user history: {e}")
            return []

    def get_conversation_history(self, user_id, limit=1):
        """Get user's conversation history"""
        try:
            conversations = self._read_json_file(self.conversations_file)
            # Filter by user_id
            user_convos = [c for c in conversations if c["user_id"] == user_id]
            # Sort by timestamp (newest first)
            user_convos.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            # Return limited number of conversations
            return user_convos[:limit]
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    def close_connection(self):
        """No connection to close in file-based storage"""
        pass

# Create database instance
try:
    db = Database()
except Exception as e:
    print(f"Failed to initialize database: {e}")
    # Provide a fallback database that doesn't crash the application
    class FallbackDatabase:
        def get_user_history(self, user_id, limit=5):
            print("Using fallback database - unable to get history")
            return []
        
        def save_conversation(self, user_id, messages):
            print("Using fallback database - unable to save conversation")
            return False
        
        def save_recommendation(self, user_id, mood, recommendations):
            print("Using fallback database - unable to save recommendation")
            return False
        
        def get_conversation_history(self, user_id, limit=1):
            print("Using fallback database - unable to get conversation history")
            return []
        
        def close_connection(self):
            pass
    
    db = FallbackDatabase()
