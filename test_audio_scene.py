"""
Test scene rendering with HTML preview and audio playback
"""
import json
import os
import logging
from agents.scene_renderer import SceneRenderer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_script():
    """Create a test script for scene rendering"""
    return {
        "title": "Audio Test Scene",
        "description": "A scene to test audio playback in HTML preview",
        "blocks": [
            {
                "type": "scene",
                "description": "Interior cafe, afternoon",
                "sound_effect": "cafe_ambience.mp3"
            },
            {
                "type": "dialogue",
                "character": "Alice",
                "text": "Hello there! How are you today?",
                "emotion": "happy"
            },
            {
                "type": "dialogue", 
                "character": "Bob",
                "text": "I'm doing well, thanks for asking!",
                "emotion": "friendly"
            },
            {
                "type": "action",
                "description": "Alice takes a sip of her coffee"
            },
            {
                "type": "dialogue",
                "character": "Alice", 
                "text": "This coffee is amazing. You should try it.",
                "emotion": "excited"
            },
            {
                "type": "environment",
                "description": "The afternoon sun streams through the window, creating warm shadows"
            },
            {
                "type": "dialogue",
                "character": "Bob",
                "text": "That sounds wonderful. I'll get one too.",
                "emotion": "agreeable"
            }
        ]
    }

def test_scene_with_audio():
    """Test scene rendering with audio playback"""
    logger.info("🚀 Starting Scene Rendering Test with Audio")
    
    # Create test script
    script = create_test_script()
    logger.info(f"📋 Created test script with {len(script['blocks'])} blocks")
    
    # Initialize scene renderer
    scene_renderer = SceneRenderer()
    
    # Create test project directory
    project_dir = os.path.join("test_results", "audio_test_scene")
    os.makedirs(project_dir, exist_ok=True)
    
    # Save script
    script_file = os.path.join(project_dir, "test_script.json")
    with open(script_file, 'w') as f:
        json.dump(script, f, indent=2)
    logger.info(f"💾 Saved script to: {script_file}")
    
    # Create mock audio files for dialogue blocks
    audio_files = {}
    audio_dir = os.path.join(project_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    dialogue_count = 0
    for i, block in enumerate(script['blocks']):
        if block.get('type') == 'dialogue':
            audio_filename = f"dialogue_{dialogue_count}.mp3"
            audio_path = os.path.join(audio_dir, audio_filename)
            # Create a small mock audio file (this would be real audio in production)
            with open(audio_path, 'wb') as f:
                f.write(b'MOCK_AUDIO_DATA_FOR_' + block['text'].encode()[:50])
            audio_files[f"block_{i}"] = audio_path
            logger.info(f"🎵 Created mock audio: {audio_filename} for '{block['text'][:30]}...'")
            dialogue_count += 1
    
    # Render scene
    logger.info("🎬 Rendering scene...")
    try:
        result = scene_renderer.render_scene(script, audio_files, project_dir)
        
        if result.get('status') == 'success':
            logger.info("✅ Scene rendered successfully!")
            logger.info(f"📁 Project directory: {project_dir}")
            logger.info(f"🎮 Ren'Py project: {result.get('renpy_project_path')}")
            
            # Get preview path and provide browser instructions
            preview_path = result.get('preview_path')
            if preview_path and os.path.exists(preview_path):
                abs_preview_path = os.path.abspath(preview_path)
                file_url = f"file:///{abs_preview_path.replace(chr(92), '/')}"
                logger.info(f"🌐 HTML preview created: {preview_path}")
                logger.info("=" * 60)
                logger.info("🎯 TO TEST AUDIO PLAYBACK:")
                logger.info(f"   Copy and paste this URL into your browser:")
                logger.info(f"   {file_url}")
                logger.info("=" * 60)
                logger.info("📋 Preview Features:")
                logger.info("   • Interactive scene player with controls")
                logger.info("   • Audio playback for dialogue blocks")
                logger.info("   • Visual indicators for audio files")
                logger.info("   • Scene statistics and Ren'Py script view")
                
                # List the audio files created
                logger.info("🎵 Audio files created:")
                for key, path in audio_files.items():
                    filename = os.path.basename(path)
                    logger.info(f"   • {filename}")
                
            else:
                logger.warning("⚠️ Preview file was not created")
                
        else:
            logger.error(f"❌ Scene rendering failed: {result}")
            
    except Exception as e:
        logger.error(f"❌ Scene rendering test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scene_with_audio()
