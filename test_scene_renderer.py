#!/usr/bin/env python3
"""
Test script for the enhanced Ren'Py scene renderer
This demonstrates the full pipeline with voice generation and scene rendering
"""

import os
import json
import sys
import logging
from agents.scene_renderer import SceneRenderer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_sample_script():
    """Load the sample script for testing"""
    sample_path = os.path.join("voice_gen", "sample.json")
    if os.path.exists(sample_path):
        with open(sample_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Create a simple test script if sample doesn't exist
        return [
            {
                "id": "scene_start",
                "type": "scene",
                "setting": "Dark warehouse",
                "description": "A dimly lit warehouse with rain streaking down the windows."
            },
            {
                "id": "env_1",
                "type": "environment",
                "description": "Rain streaks down the grimy windows, creating an oppressive atmosphere.",
                "environmental_impact": {
                    "sound_implications": ["rain", "drip_sound"],
                    "atmosphere_shift": "tension_increase"
                }
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
                "id": "action_1",
                "type": "movement", 
                "character": "Detective Sarah",
                "description": "Detective Sarah slowly enters the warehouse, scanning the room with a wary expression.",
                "environmental_impact": {
                    "sound_implications": ["footsteps"]
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
            },
            {
                "id": "dialogue_3",
                "type": "dialogue",
                "character": "Detective Sarah",
                "text": "I have no idea what you're talking about. You're making a mistake.",
                "emotion": "defensive",
                "traits": {
                    "gender": "female",
                    "age_range": "adult",
                    "voice_style": "defensive",
                    "accent": "neutral"
                }
            }
        ]

def create_mock_audio_files(script, project_dir):
    """Create mock audio files for testing scene rendering"""
    logger.info("🎙️ Creating mock audio files for testing...")
    
    audio_files = {}
    audio_dir = os.path.join(project_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    for block in script:
        if block.get("type") == "dialogue":
            block_id = block.get("id", "")
            character = block.get("character", "Unknown")
            text = block.get("text", "")
            
            # Create a mock audio file (text placeholder)
            audio_filename = f"{character}_{block_id}.txt"
            audio_path = os.path.join(audio_dir, audio_filename)
            
            with open(audio_path, 'w', encoding='utf-8') as f:
                f.write(f"Mock Audio File\n")
                f.write(f"Character: {character}\n")
                f.write(f"Text: {text}\n")
                f.write(f"Block ID: {block_id}\n")
            
            audio_files[block_id] = audio_path
    
    logger.info(f"✅ Created {len(audio_files)} mock audio files:")
    for block_id, audio_path in audio_files.items():
        logger.info(f"  - {block_id}: {audio_path}")
    
    return audio_files

def test_scene_rendering(script, audio_files, project_dir):
    """Test scene rendering with the enhanced Ren'Py support"""
    logger.info("🎬 Testing scene rendering...")
    
    scene_renderer = SceneRenderer()
    result = scene_renderer.render_scene(script, audio_files, project_dir)
    
    logger.info(f"✅ Scene rendering result: {result.get('status', 'unknown')}")
    
    if result.get("preview_file"):
        logger.info(f"📄 HTML Preview: {result['preview_file']}")
        logger.info(f"🌐 Open in browser: {result.get('preview_url', '')}")
    
    if result.get("script_file"):
        logger.info(f"📜 Ren'Py Script: {result['script_file']}")
    
    return result

def main():
    """Run the complete test"""
    logger.info("🚀 Starting ∞-V Scene Renderer Test")
    
    # Create test project directory
    project_dir = os.path.join("test_results", "scene_renderer_test")
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(os.path.join(project_dir, "scripts"), exist_ok=True)
    
    try:
        # Load sample script
        logger.info("📋 Loading sample script...")
        script = load_sample_script()
        logger.info(f"✅ Loaded script with {len(script)} blocks")
        
        # Save script to project directory for reference
        script_file = os.path.join(project_dir, "scripts", "script.json")
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
        logger.info(f"📁 Saved script to: {script_file}")
        
        # Create mock audio files for testing scene rendering
        audio_files = create_mock_audio_files(script, project_dir)
        
        # Test scene rendering
        scene_result = test_scene_rendering(script, audio_files, project_dir)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("🎯 TEST SUMMARY:")
        logger.info(f"📋 Script blocks: {len(script)}")
        logger.info(f"🎙️ Audio files: {len(audio_files)}")
        logger.info(f"🎬 Scene status: {scene_result.get('status', 'unknown')}")
        
        if scene_result.get("preview_file"):
            preview_path = os.path.abspath(scene_result["preview_file"])
            logger.info(f"🌐 Preview ready: file://{preview_path}")
            logger.info("   Open this file in your browser to see the interactive scene!")
        
        if scene_result.get("script_file"):
            script_path = os.path.abspath(scene_result["script_file"])
            logger.info(f"📜 Ren'Py script: {script_path}")
            logger.info("   This can be used with Ren'Py SDK to create a full visual novel!")
        
        logger.info("=" * 60)
        logger.info("✅ Test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
