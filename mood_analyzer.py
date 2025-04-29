from google import genai
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure Gemini API with safety settings
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

class MoodAnalyzer:
    def __init__(self):
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment variables")
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            logger.info("Configuring Gemini API...")
            
            # Initialize the Gemini client using the new google-genai package
            self.client = genai.Client(api_key=api_key)
            
            # Set the default model
            self.model_name = "gemini-2.0-flash"
            logger.info(f"Using model: {self.model_name}")
            
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            self.client = None
    
    def analyze_mood(self, conversation):
        # Default mood if Gemini fails
        default_mood = "Neutral"
        
        # Only try Gemini if it was initialized successfully
        if self.client:
            try:
                prompt = f"""
                Analyze the mood of the following conversation and respond with ONLY ONE of these moods:
                - Happy
                - Sad
                - Angry
                - Anxious
                - Relaxed
                - Neutral
                
                Conversation:
                {conversation}
                """
                
                # Generate response using the client.models.generate_content method
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt
                    )
                    gemini_mood = response.text.strip()
                    logger.info(f"Using Gemini mood: {gemini_mood}")
                    return gemini_mood
                except Exception as e:
                    logger.error(f"Model generation error: {e}, returning default mood")
                
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
        
        # Return default mood if Gemini fails
        logger.info(f"Using default mood: {default_mood}")
        return default_mood
