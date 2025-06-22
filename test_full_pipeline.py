"""
Test the full pipeline: Script generation → Scene rendering → HTML preview
"""
import json
import os
import logging
from agents.script_generator import ScriptGenerator
from agents.scene_renderer import SceneRenderer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_pipeline():
    """Test the complete script-to-scene pipeline"""
    logger.info("🚀 Starting Full Pipeline Test")
    
    # Initialize agents
    script_gen = ScriptGenerator()
    scene_renderer = SceneRenderer()
    
    # Generate a script
    prompt = "A romantic dinner scene between two characters"
    logger.info(f"📝 Generating script for: {prompt}")
    
    try:
        script = script_gen.generate_script(prompt)
        logger.info(f"✅ Generated script with {len(script.get('blocks', []))} blocks")
        
        # Create test project directory
        project_dir = os.path.join("test_results", "full_pipeline_test")
        os.makedirs(project_dir, exist_ok=True)
        
        # Save script
        script_file = os.path.join(project_dir, "generated_script.json")
        with open(script_file, 'w') as f:
            json.dump(script, f, indent=2)
        logger.info(f"💾 Saved script to: {script_file}")
        
        # Create mock audio files for dialogue blocks
        audio_files = {}
        audio_dir = os.path.join(project_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        for i, block in enumerate(script.get('blocks', [])):
            if block.get('type') == 'dialogue':
                audio_filename = f"dialogue_{i}.mp3"
                audio_path = os.path.join(audio_dir, audio_filename)
                # Create a small mock audio file
                with open(audio_path, 'wb') as f:
                    f.write(b'Mock audio data')
                audio_files[f"block_{i}"] = audio_path
                logger.info(f"🎵 Created mock audio: {audio_filename}")
        
        # Render scene
        logger.info("🎬 Rendering scene...")
        result = scene_renderer.render_scene(script, audio_files, project_dir)
        
        if result.get('status') == 'success':
            logger.info("✅ Scene rendered successfully!")
            logger.info(f"📁 Project directory: {project_dir}")
            logger.info(f"🎮 Ren'Py project: {result.get('renpy_project_path')}")
            logger.info(f"🌐 HTML preview: {result.get('preview_path')}")
            
            # Print instructions for viewing
            preview_path = result.get('preview_path')
            if preview_path and os.path.exists(preview_path):
                abs_preview_path = os.path.abspath(preview_path)
                logger.info(f"🎯 Open this file in your browser to test audio playback:")
                logger.info(f"   file:///{abs_preview_path.replace(chr(92), '/')}")
        else:
            logger.error(f"❌ Scene rendering failed: {result}")
            
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_pipeline()
