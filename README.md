🎵 Mood Music Assistant
An AI-powered chatbot that recommends music based on your emotional state

🌟 Features
Mood Detection: Analyzes your chat conversation to detect your current emotional state (Happy, Sad, Angry, Relaxed, etc.)

Personalized Recommendations: Suggests songs tailored to your mood

Interactive Chat Interface: Built with Streamlit for a seamless user experience

Music API Integration: Fetches recommendations from JioSaavn (Hindi songs) and mock data (international songs)

History Tracking: Remembers your past moods and recommendations

🛠️ Tech Stack
Backend: Python

AI: Google's Gemini API + NLTK for mood analysis

Database: MongoDB Atlas (or SQLite for local development)

Frontend: Streamlit

APIs: JioSaavn (music metadata)

🚀 Quick Start
Clone the repository

bash
git clone https://github.com/yourusername/mood-music-assistant.git
cd mood-music-assistant
Set up environment variables
Create a .env file:

env
GEMINI_API_KEY=your_gemini_api_key
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
Install dependencies

bash
pip install -r requirements.txt
Run the app

bash
streamlit run app.py
