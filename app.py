import streamlit as st
from datetime import datetime, timedelta
import time
from mood_analyzer import MoodAnalyzer
from music_recommender import MusicRecommender
import os
from dotenv import load_dotenv
import random
import logging

load_dotenv()

# Set page config
st.set_page_config(
    page_title="Moodify",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
mood_analyzer = MoodAnalyzer()
music_recommender = MusicRecommender(gemini_client=mood_analyzer.client)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"  # In a real app, you'd have user authentication
if "page" not in st.session_state:
    st.session_state.page = "home"  # Default to homepage

# Function to navigate between pages
def navigate_to(page):
    st.session_state.page = page

# Custom CSS
st.markdown("""
    <style>
    /* Base styles */
    body {
        font-family: 'Montserrat', sans-serif;
        color: #E8E9F3;
        background-color: #121212;
    }
    
    /* Override Streamlit's default background */
    .stApp {
        background-color: #121212;
    }
    
    .stChatInput {
        position: fixed;
        bottom: 20px;
        width: 70%;
    }
    
    .stChatMessage {
        padding: 12px;
        border-radius: 15px;
        margin: 5px 0;
    }
    
    .user-message {
        background-color: #2D3047;
    }
    
    .assistant-message {
        background-color: #1A1A2E;
    }
    
    /* Homepage styling */
    .homepage {
        text-align: center;
        padding: 30px;
        max-width: 1000px;
        margin: 0 auto;
    }
    
    .hero-title {
        font-size: 4.5rem;
        font-weight: 800;
        margin-bottom: 20px;
        background: linear-gradient(90deg, #4F46E5, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }
    
    .hero-subtitle {
        font-size: 1.8rem;
        font-weight: 300;
        margin-bottom: 40px;
        color: #B8C1EC;
    }
    
    .enter-button {
        display: inline-block;
        background: linear-gradient(90deg, #4F46E5, #EC4899);
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        padding: 15px 30px;
        border-radius: 50px;
        text-decoration: none;
        margin-top: 20px;
        transition: transform 0.3s, box-shadow 0.3s;
        box-shadow: 0 10px 15px rgba(79, 70, 229, 0.2);
    }
    
    .enter-button:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 20px rgba(79, 70, 229, 0.3);
    }
    
    .feature-container {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        margin-top: 60px;
    }
    
    .feature-card {
        background: #232333;
        border-radius: 15px;
        padding: 25px;
        width: 100%;
        min-height: 260px;
        margin: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        transition: transform 0.3s;
        color: #E8E9F3;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
    }
    
    .feature-icon {
        font-size: 40px;
        margin-bottom: 15px;
    }
    
    .feature-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 10px;
        color: #E8E9F3;
    }
    
    .feature-card p {
        color: #B8C1EC;
        font-size: 1rem;
        line-height: 1.5;
    }
    
    /* Mood display */
    .mood-display {
        font-size: 24px;
        font-weight: bold;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    /* Song recommendations */
    .song-card {
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        margin: 15px 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        background: #232333;
        color: #E8E9F3;
    }
    
    .song-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.25);
    }
    
    .song-card h4 {
        margin: 0 0 10px 0;
        color: #E8E9F3;
    }
    
    .song-card p {
        margin: 0 0 10px 0;
        color: #B8C1EC;
    }
    
    .song-card a {
        display: inline-block;
        background: linear-gradient(90deg, #4F46E5, #EC4899);
        color: white;
        padding: 8px 15px;
        border-radius: 30px;
        text-decoration: none;
        font-weight: 500;
        margin-top: 8px;
        transition: transform 0.2s ease;
    }
    
    .song-card a:hover {
        transform: translateY(-2px);
    }
    
    /* Sidebar styling */
    .sidebar-title {
        background: linear-gradient(90deg, #4F46E5, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    .mood-history-card {
        padding: 12px;
        margin: 10px 0;
        border-radius: 10px;
        background: #232333;
        border-left: 4px solid;
        transition: transform 0.2s;
        color: #E8E9F3;
    }
    
    .mood-history-card:hover {
        transform: translateX(5px);
    }
    
    /* Return to home button */
    .return-home {
        display: inline-block;
        padding: 8px 15px;
        background-color: #232333;
        color: #4F46E5;
        border-radius: 50px;
        text-decoration: none;
        font-size: 0.9rem;
        transition: background-color 0.2s;
        margin-bottom: 20px;
    }
    
    .return-home:hover {
        background-color: #2D3047;
    }
    
    /* Streamlit button styling */
    .stButton > button {
        background: linear-gradient(90deg, #4F46E5, #EC4899);
        color: white;
        font-weight: 600;
        border: none;
        padding: 12px 20px;
        border-radius: 50px;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 5px 15px rgba(79, 70, 229, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(79, 70, 229, 0.4);
    }
    
    /* Improve text visibility in sidebar */
    .css-1544g2n {
        color: #B8C1EC;
    }
    
    </style>
""", unsafe_allow_html=True)

# Sidebar content
with st.sidebar:
    st.markdown('<h1 class="sidebar-title">🎵 Moodify</h1>', unsafe_allow_html=True)
    st.markdown("Music recommendations powered by your mood")
    
    if st.session_state.page == "chat":
        if st.button("← Return to Home"):
            navigate_to("home")
    
    if st.session_state.analysis_done and "recommendations" in st.session_state:
        st.success("Mood analysis completed!")
        st.markdown("### Your Music Recommendations")
        
        # Create an expandable section to keep sidebar clean
        with st.expander("Expand to play songs", expanded=False):
            for i, song in enumerate(st.session_state.recommendations[:4]):  # Limit to top 4 songs for sidebar
                st.markdown(f"""
                <div class="song-card">
                    <b>{song['title']}</b><br>
                    <i>{song['artist']}</i>
                </div>
                """, unsafe_allow_html=True)
                
                # Show song image if available
                if 'image' in song and song['image']:
                    st.image(song['image'], width=150)
                
                # Try to play audio
                audio_played = False
                
                # First try direct streaming URL
                if 'stream_url' in song and song['stream_url']:
                    try:
                        st.audio(song['stream_url'], format='audio/mp3')
                        audio_played = True
                    except Exception as e:
                        pass
                
                # If no direct streaming or it failed, add YouTube button
                if not audio_played and 'youtube_search' in song:
                    youtube_search_url = song['youtube_search']
                    st.markdown(f"""
                    <div style="display:flex; justify-content:center; margin: 8px 0;">
                        <a href="{youtube_search_url}" target="_blank" style="text-decoration:none;">
                            <button style="background: linear-gradient(90deg, #4F46E5, #EC4899); color: white; 
                            border: none; padding: 8px 12px; border-radius: 50px; display: flex; align-items: center; font-size: 0.8rem;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white" style="margin-right: 6px;">
                                    <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm-3 17v-10l9 5.146-9 4.854z"/>
                                </svg>
                                Play on YouTube
                            </button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                
                # For sidebar, show a more compact version - just a mini YouTube player
                if not audio_played:
                    embed_url = music_recommender.saavn_service.get_youtube_embed_url(song['title'], song['artist'])
                    st.markdown(f"""
                    <div style="position:relative; padding-bottom:40%; height:0; overflow:hidden; max-width:100%; border-radius:8px; margin-bottom:15px;">
                        <iframe src="{embed_url}" 
                            style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;" 
                            allowfullscreen title="{song['title']} by {song['artist']}">
                        </iframe>
                    </div>
                    """, unsafe_allow_html=True)
                
                if i < len(st.session_state.recommendations) - 1:
                    st.markdown("<hr style='margin: 15px 0; opacity: 0.3;'>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Your Mood History")
    history = db.get_user_history(st.session_state.user_id)
    
    mood_border_colors = {
        "Happy": "#4CAF50",
        "Sad": "#2196F3",
        "Angry": "#F44336",
        "Anxious": "#FF9800",
        "Relaxed": "#009688",
        "Neutral": "#9E9E9E"
    }
    
    if not history:
        st.markdown("No mood history yet. Start chatting!")
    else:
        for item in history[:5]:  # Show last 5 recommendations
            border_color = mood_border_colors.get(item['mood'], "#9E9E9E")
            st.markdown(f"""
            <div class="mood-history-card" style="border-left-color: {border_color};">
                <b>{item['mood']}</b> - {item['timestamp'].strftime('%b %d, %Y %H:%M')}
            </div>
            """, unsafe_allow_html=True)

# Main content area - Homepage or Chat page
if st.session_state.page == "home":
    # Homepage
    st.markdown('<h1 class="hero-title">Welcome to Moodify</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Discover music that matches how you feel</p>', unsafe_allow_html=True)
    
    # Using st.image with use_container_width instead of deprecated use_column_width
    st.image("https://images.unsplash.com/photo-1470225620780-dba8ba36b745?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80", 
             use_container_width=True)
    
    # Using a Streamlit button instead of HTML/JS button
    if st.button("Start Chatting", key="homepage_chat_button", use_container_width=True):
        navigate_to("chat")
    
    # Feature cards using Streamlit columns for better layout control
    st.markdown('<div class="feature-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('''
        <div class="feature-card">
            <div class="feature-icon">🗣️</div>
            <h3 class="feature-title">Chat Analysis</h3>
            <p>Chat for just one minute, and our AI will analyze your mood from your conversation.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="feature-card">
            <div class="feature-icon">🎭</div>
            <h3 class="feature-title">Mood Detection</h3>
            <p>Our advanced AI detects your emotional state - happy, sad, angry, anxious, or relaxed.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown('''
        <div class="feature-card">
            <div class="feature-icon">🎵</div>
            <h3 class="feature-title">Music Recommendations</h3>
            <p>Get personalized music recommendations that match your current mood.</p>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

else:  # Chat page
    st.title("Chat with Moodify")
    st.markdown("Tell me how you're feeling for 1 minute, and I'll recommend music that matches your mood.")
    
    # Progress bar if timer is active and analysis not done
    if st.session_state.start_time and not st.session_state.analysis_done:
        elapsed_time = (datetime.now() - st.session_state.start_time).total_seconds()
        total_time = 60  # 1 minute in seconds
        remaining_time = max(0, total_time - elapsed_time)
        progress = min(1.0, elapsed_time / total_time)
        
        st.progress(progress)
        st.write(f"Time remaining: {int(remaining_time)} seconds")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input - Only show if analysis is not done
    if not st.session_state.analysis_done:
        if prompt := st.chat_input("How are you feeling today?"):
            # Start timer if not already started
            if st.session_state.start_time is None:
                st.session_state.start_time = datetime.now()
            
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Use Gemini AI for chat responses
            try:
                chat_prompt = f"""
                You are an empathetic AI assistant named Moodify, who is collecting information about the user's mood and recommending Indian music based on their emotional state. Respond to the following message with a short (1-3 sentences), conversational reply that encourages the user to share more about their feelings. Ask follow-up questions to help understand their mood, and recommend Indian songs or playlists with meaningful lyrics that reflect or uplift the user's current emotions. Be supportive and ensure the songs you suggest resonate with the cultural and emotional context of the user’s mood.
                User's message: "{prompt}"
                """
                
                # Use the mood_analyzer's client to generate a response
                ai_response = mood_analyzer.client.models.generate_content(
                    model=mood_analyzer.model_name,
                    contents=chat_prompt
                )
                response = ai_response.text.strip()
                
            except Exception as e:
                # Fallback responses if Gemini API fails
                responses = [
                    "Tell me more about how you're feeling.",
                    "I see. What else is on your mind?",
                    "Interesting. How does that make you feel?",
                    "I'm listening. Please continue.",
                    "That's good to know. What else would you like to share?"
                ]
                response = random.choice(responses)
                logging.error(f"Failed to generate AI response: {e}")
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
            
            # Check if 1 minute has passed
            if datetime.now() - st.session_state.start_time >= timedelta(minutes=1) and not st.session_state.analysis_done:
                st.session_state.analysis_done = True
                
                # Join all messages for analysis
                conversation = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                
                # Analyze mood
                with st.spinner("Analyzing your mood..."):
                    mood = mood_analyzer.analyze_mood(conversation)
                    st.session_state.mood = mood
                    
                    # Get recommendations
                    recommendations = music_recommender.recommend_songs(mood)
                    st.session_state.recommendations = recommendations
                    
                    # Save to database
                    db.save_conversation(st.session_state.user_id, st.session_state.messages)
                    db.save_recommendation(st.session_state.user_id, mood, recommendations)
                
                # Display mood and recommendations
                mood_colors = {
                    "Happy": "#4CAF50",
                    "Sad": "#2196F3",
                    "Angry": "#F44336",
                    "Anxious": "#FF9800",
                    "Relaxed": "#009688",
                    "Neutral": "#9E9E9E"
                }
                
                st.markdown(f"""
                <div class="mood-display" style="background-color: {mood_colors.get(mood, '#9E9E9E')}; color: white;">
                    Detected Mood: {mood}
                </div>
                """, unsafe_allow_html=True)
                
                st.success("Here are some music recommendations based on your mood:")
                
                col1, col2, col3 = st.columns(3)
                
                for i, song in enumerate(recommendations[:6]):
                    col = [col1, col2, col3][i % 3]
                    with col:
                        # Display song image if available
                        if 'image' in song and song['image']:
                            st.image(song['image'], use_container_width=True)
                        
                        st.markdown(f"""
                        <div class="song-card">
                            <h4>{song['title']}</h4>
                            <p><i>{song['artist']}</i></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Try to play audio
                        audio_played = False
                        
                        # 1. Try direct streaming URL first
                        if 'stream_url' in song and song['stream_url']:
                            try:
                                st.audio(song['stream_url'], format='audio/mp3')
                                audio_played = True
                            except Exception as e:
                                st.warning("Native audio player unavailable. Using YouTube fallback.")
                        
                        # 2. If no direct streaming URL or it failed, use YouTube embed
                        if not audio_played:
                            # Create a YouTube embed URL
                            if 'youtube_search' in song:
                                youtube_search_url = song['youtube_search']
                                st.markdown(f"""
                                <div style="display:flex; justify-content:center;">
                                    <a href="{youtube_search_url}" target="_blank" style="text-decoration:none;">
                                        <button style="background: linear-gradient(90deg, #4F46E5, #EC4899); color: white; 
                                        border: none; padding: 10px 15px; border-radius: 50px; display: flex; align-items: center;">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white" style="margin-right: 8px;">
                                                <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm-3 17v-10l9 5.146-9 4.854z"/>
                                            </svg>
                                            Play on YouTube
                                        </button>
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Create a YouTube embed directly in the page
                            embed_url = music_recommender.saavn_service.get_youtube_embed_url(song['title'], song['artist'])
                            st.markdown(f"""
                            <div style="position:relative; padding-bottom:56.25%; height:0; overflow:hidden; max-width:100%; border-radius:8px;">
                                <iframe src="{embed_url}" 
                                    style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;" 
                                    allowfullscreen title="{song['title']} by {song['artist']}">
                                </iframe>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Always show external link to song
                        st.markdown(f"<a href='{song['url']}' target='_blank'>View on JioSaavn</a>", unsafe_allow_html=True)
                
                # Force a rerun to update the sidebar
                st.rerun()
    else:
        # Show a message that chat is disabled after analysis
        st.info("Chat has ended. Your mood has been analyzed and music recommendations are provided.")
                
        # Add a reset button
        if st.button("Start New Chat"):
            st.session_state.messages = []
            st.session_state.start_time = None
            st.session_state.analysis_done = False
            st.rerun()
