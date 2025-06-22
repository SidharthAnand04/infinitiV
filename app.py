from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import logging
import uuid
from datetime import datetime
import re

# Import our custom modules
from agents.script_generator import ScriptGenerator
from agents.voice_generator import VoiceGenerator
from agents.scene_renderer import SceneRenderer


# Load environment variables
load_dotenv('.env')

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize our AI agents
script_gen = ScriptGenerator()
voice_gen = VoiceGenerator()
scene_renderer = SceneRenderer()

def generate_folder_name(prompt: str) -> str:
    """Generate a clean folder name from the prompt"""
    # Take first 50 characters and clean them
    clean_prompt = re.sub(r'[^\w\s-]', '', prompt[:50]).strip()
    clean_prompt = re.sub(r'[-\s]+', '_', clean_prompt)
    
    # Add timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate unique ID
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{clean_prompt}_{timestamp}_{unique_id}"

def create_project_folder(folder_name: str) -> str:
    """Create a project folder under results directory"""
    results_dir = os.path.join(os.getcwd(), "results")
    project_dir = os.path.join(results_dir, folder_name)
    
    # Create directories if they don't exist
    os.makedirs(project_dir, exist_ok=True)
    
    # Create subdirectories for organization
    subdirs = ["scripts", "audio", "scenes", "assets"]
    for subdir in subdirs:
        os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)
    
    logger.info(f"Created project folder: {project_dir}")
    return project_dir

@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "∞-V API is running",
        "version": "1.0.0"
    })

@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    """Generate a structured script from a user prompt"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        reference_materials = data.get('references', [])
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        logger.info(f"Generating script for prompt: {prompt}")
        
        # Create project folder
        folder_name = generate_folder_name(prompt)
        project_dir = create_project_folder(folder_name)
        
        # Generate script using our agent pipeline
        script = script_gen.generate_script(prompt, reference_materials, project_dir)
        
        # Save script to file
        script_path = os.path.join(project_dir, "scripts", "script.json")
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "script": script,
            "prompt": prompt,
            "project_folder": folder_name,
            "project_path": project_dir,
            "script_file": script_path
        })
        
    except Exception as e:
        logger.error(f"Error generating script: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-voice', methods=['POST'])
def generate_voice():
    """Generate voice audio for script dialogue blocks"""
    try:
        data = request.get_json()
        script = data.get('script', [])
        project_folder = data.get('project_folder', '')
        
        if not script:
            return jsonify({"error": "Script is required"}), 400
        
        logger.info("Generating voice audio for script")
        
        # Determine project directory
        if project_folder:
            project_dir = os.path.join(os.getcwd(), "results", project_folder)
        else:
            # Create new folder if none provided
            folder_name = generate_folder_name("voice_generation")
            project_dir = create_project_folder(folder_name)
            project_folder = folder_name
        
        # Generate voice audio using Vapi
        audio_files = voice_gen.generate_voices(script, project_dir)
        
        return jsonify({
            "success": True,
            "audio_files": audio_files,
            "project_folder": project_folder,
            "project_path": project_dir
        })
        
    except Exception as e:
        logger.error(f"Error generating voice: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/render-scene', methods=['POST'])
def render_scene():
    """Render the final scene using Ren'Py"""
    try:
        data = request.get_json()
        script = data.get('script', [])
        audio_files = data.get('audio_files', {})
        project_folder = data.get('project_folder', '')
        
        if not script:
            return jsonify({"error": "Script is required"}), 400
        
        logger.info("Rendering scene with Ren'Py")
        
        # Determine project directory
        if project_folder:
            project_dir = os.path.join(os.getcwd(), "results", project_folder)
        else:
            # Create new folder if none provided
            folder_name = generate_folder_name("scene_rendering")
            project_dir = create_project_folder(folder_name)
            project_folder = folder_name
        
        # Render scene
        scene_output = scene_renderer.render_scene(script, audio_files, project_dir)
        
        return jsonify({
            "success": True,
            "scene_output": scene_output,
            "project_folder": project_folder,
            "project_path": project_dir
        })
        
    except Exception as e:
        logger.error(f"Error rendering scene: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-full-scene', methods=['POST'])
def generate_full_scene():
    """Complete pipeline: prompt → script → voice → scene"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        reference_materials = data.get('references', [])
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        logger.info(f"Starting full pipeline for prompt: {prompt}")
        
        # Create project folder
        folder_name = generate_folder_name(prompt)
        project_dir = create_project_folder(folder_name)
        
        # Step 1: Generate script
        script = script_gen.generate_script(prompt, reference_materials, project_dir)
        
        # Save script to file
        script_path = os.path.join(project_dir, "scripts", "script.json")
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
        
        # Step 2: Generate voices
        audio_files = voice_gen.generate_voices(script, project_dir)
        
        # Step 3: Render scene
        scene_output = scene_renderer.render_scene(script, audio_files, project_dir)
        
        # Save project metadata
        metadata = {
            "prompt": prompt,
            "created_at": datetime.now().isoformat(),
            "folder_name": folder_name,
            "script_length": len(script),
            "audio_files_count": len(audio_files),
            "reference_materials": reference_materials
        }
        
        metadata_path = os.path.join(project_dir, "project_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "script": script,
            "audio_files": audio_files,
            "scene_output": scene_output,
            "prompt": prompt,
            "project_folder": folder_name,
            "project_path": project_dir,
            "metadata": metadata
        })
        
    except Exception as e:
        logger.error(f"Error in full pipeline: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/list-projects', methods=['GET'])
def list_projects():
    """List all generated projects"""
    try:
        results_dir = os.path.join(os.getcwd(), "results")
        
        if not os.path.exists(results_dir):
            return jsonify({"projects": []})
        
        projects = []
        for folder_name in os.listdir(results_dir):
            folder_path = os.path.join(results_dir, folder_name)
            if os.path.isdir(folder_path):
                metadata_path = os.path.join(folder_path, "project_metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    projects.append({
                        "folder_name": folder_name,
                        "metadata": metadata
                    })
                else:
                    projects.append({
                        "folder_name": folder_name,
                        "metadata": {"prompt": "Unknown", "created_at": "Unknown"}
                    })
        
        # Sort by creation date
        projects.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)
        
        return jsonify({"projects": projects})
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
