from mood_analyzer import MoodAnalyzer

def test_mood_analysis():
    try:
        analyzer = MoodAnalyzer()
        
        # Test with a happy conversation
        happy_text = "I'm so excited! I just got my dream job and I can't wait to start!"
        happy_mood = analyzer.analyze_mood(happy_text)
        print(f"Happy text mood: {happy_mood}")
        
        # Test with a sad conversation
        sad_text = "I'm feeling really down today. Everything seems to be going wrong."
        sad_mood = analyzer.analyze_mood(sad_text)
        print(f"Sad text mood: {sad_mood}")
        
        # Test with a neutral conversation
        neutral_text = "The weather is cloudy today. I might go for a walk later."
        neutral_mood = analyzer.analyze_mood(neutral_text)
        print(f"Neutral text mood: {neutral_mood}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_mood_analysis()