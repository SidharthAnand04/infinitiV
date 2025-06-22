#!/usr/bin/env python3
"""
Simple test for the Flask API endpoints to ensure scene rendering works through the web API
"""

import requests
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_flask_scene_rendering():
    """Test the Flask scene rendering endpoint"""
    
    # Sample script data
    test_script = [
        {
            "id": "scene_start",
            "type": "scene",
            "setting": "Dark warehouse",
            "description": "A dimly lit warehouse with rain streaking down the windows."
        },
        {
            "id": "dialogue_1",
            "type": "dialogue",
            "character": "Detective Sarah",
            "text": "I still don't understand why you brought me here. This place gives me the creeps.",
            "emotion": "unease",
            "traits": {
                "gender": "female",
                "age_range": "adult",
                "voice_style": "cautious",
                "accent": "neutral"
            }
        },
        {
            "id": "dialogue_2",
            "type": "dialogue",
            "character": "Suspect Mike",
            "text": "Don't play coy. We both know you were involved. Just tell me what happened.",
            "emotion": "firm_determination",
            "traits": {
                "gender": "male",
                "age_range": "adult",
                "voice_style": "direct",
                "accent": "neutral"
            }
        }
    ]
    
    # Mock audio files
    mock_audio_files = {
        "dialogue_1": "audio/detective_sarah_dialogue_1.mp3",
        "dialogue_2": "audio/suspect_mike_dialogue_2.mp3"
    }
    
    base_url = "http://localhost:5000"
    
    try:
        # Test scene rendering endpoint
        logger.info("🎬 Testing scene rendering endpoint...")
        
        payload = {
            "script": test_script,
            "audio_files": mock_audio_files,
            "project_folder": "api_test_scene"
        }
        
        response = requests.post(f"{base_url}/api/render-scene", 
                               json=payload, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Scene rendering API test successful!")
            logger.info(f"📊 Response: {json.dumps(result, indent=2)}")
            
            if result.get("scene_output", {}).get("preview_file"):
                logger.info(f"🌐 Preview file created: {result['scene_output']['preview_file']}")
            
            return True
        else:
            logger.error(f"❌ Scene rendering API failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except requests.ConnectionError:
        logger.error("❌ Cannot connect to Flask app. Make sure to run: python app.py")
        return False
    except Exception as e:
        logger.error(f"❌ API test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Testing Flask API Scene Rendering")
    logger.info("📝 Make sure Flask app is running: python app.py")
    logger.info("⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    success = test_flask_scene_rendering()
    
    if success:
        logger.info("✅ Flask API scene rendering test passed!")
    else:
        logger.info("❌ Flask API scene rendering test failed!")
        logger.info("💡 To test manually:")
        logger.info("   1. Run: python app.py")
        logger.info("   2. Run: python test_flask_api.py")
