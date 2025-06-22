import os
import json
import logging
from typing import List, Dict, Any, Union
import shutil
import subprocess

logger = logging.getLogger(__name__)

class SceneRenderer:
    """Scene rendering agent using Ren'Py engine"""
    
    def __init__(self):
        self.renpy_sdk_path = os.getenv('RENPY_SDK_PATH', '')
        self.output_dir = "rendered_scenes"
        self.project_dir = "renpy_projects"
        
        # Create necessary directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.project_dir, exist_ok=True)

    def render_scene(self, script: Union[Dict, List[Dict]], audio_files: Dict[str, str], project_dir: str = None) -> Dict[str, Any]:
        """
        Render the scene using Ren'Py engine
        Returns information about the rendered scene
        """
        try:
            logger.info("Starting scene rendering with Ren'Py")
              # Normalize script format
            if isinstance(script, dict):
                script_blocks = script.get('blocks', [])
                script_dict = script
            else:
                script_blocks = script
                script_dict = {'blocks': script}
            
            # Create project name based on script content
            project_name = self._generate_project_name(script_dict)
            
            # Use provided project_dir or create new one
            if project_dir:
                project_path = os.path.join(project_dir, "renpy_project", project_name)
            else:
                project_path = os.path.join(self.project_dir, project_name)
            
            # Create Ren'Py project structure
            self._create_renpy_project(project_path, script_blocks, audio_files)
            
            # Generate Ren'Py script
            renpy_script = self._generate_renpy_script(script_blocks, audio_files)
            
            # Write script file
            script_file = os.path.join(project_path, "game", "script.rpy")
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(renpy_script)
              # Try to build/export the scene
            scene_output = self._build_scene(project_path, project_name)
            
            return {
                "project_name": project_name,
                "project_path": project_path,
                "script_file": script_file,
                "scene_output": scene_output,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error in scene rendering: {str(e)}")
            return self._create_fallback_scene(script_blocks, audio_files)

    def _generate_project_name(self, script: Dict) -> str:
        """Generate a unique project name based on script content"""
        
        # Extract some text from the script for naming
        text_parts = []
        blocks = script.get('blocks', []) if isinstance(script, dict) else script
        for block in blocks[:3]:  # Use first 3 blocks
            if block.get("type") == "dialogue":
                text = block.get("text", "")
                words = text.split()[:3]  # First 3 words
                text_parts.extend(words)
        
        if text_parts:
            project_name = "_".join(text_parts).lower()
            # Clean the name
            project_name = "".join(c for c in project_name if c.isalnum() or c == "_")
            return project_name[:20]  # Limit length
        
        return "infiniti_v_scene"
    
    def _create_renpy_project(self, project_path: str, script: List[Dict], audio_files: Dict[str, str]):
        """Create the basic Ren'Py project structure with enhanced asset support"""
        
        # Create directory structure
        game_dir = os.path.join(project_path, "game")
        images_dir = os.path.join(game_dir, "images")
        audio_dir = os.path.join(game_dir, "audio")
        
        os.makedirs(game_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        
        # Copy audio files to project
        for block_id, audio_file in audio_files.items():
            if os.path.exists(audio_file):
                target_file = os.path.join(audio_dir, f"voice_{block_id}.mp3")
                try:
                    if audio_file.endswith('.txt'):
                        # For simulated audio files, create a placeholder
                        with open(target_file.replace('.mp3', '.txt'), 'w') as f:
                            f.write(f"Audio placeholder for block {block_id}")
                    else:
                        shutil.copy2(audio_file, target_file)
                        # Also copy with original filename for voice commands
                        original_name = os.path.basename(audio_file)
                        shutil.copy2(audio_file, os.path.join(audio_dir, original_name))
                except Exception as e:
                    logger.warning(f"Could not copy audio file {audio_file}: {str(e)}")
        
        # Create placeholder sound effects
        self._create_sound_effects(audio_dir)
        
        # Create placeholder character images
        self._create_character_images(images_dir, script)
        
        # Create placeholder backgrounds
        self._create_background_images(images_dir)
        
        # Create basic options.rpy
        options_content = '''
        ## This file contains options that can be changed to customize your game.

        ## Graphics ################################################################

        ## These options control the width and height of the screen.
        define config.screen_width = 1920
        define config.screen_height = 1080

        ## The title of the game.
        define config.name = _("∞-V Generated Scene")

        ## The version of the game.
        define config.version = "1.0"

        ## Text that is placed on the game's about screen.
        define gui.about = _p("""
        Generated by ∞-V (Infiniti-V)
        AI-Powered Animated Video Generator
        """)

        ## A short name for the game used for executables and directories.
        define build.name = "infiniti_v_scene"

        ## Sounds and music ########################################################

        ## These three variables control which mixers are shown to the player by
        ## default. Setting one of these to False will hide the appropriate mixer.

        define config.has_sound = True
        define config.has_music = True
        define config.has_voice = True

        ## Uncomment the following line to set up a main menu music.
        # define config.main_menu_music = "music/main_menu.ogg"

        ## Transitions #############################################################

        ## These variables set transitions that are used when certain events occur.

        define config.enter_transition = dissolve
        define config.exit_transition = dissolve
        define config.intra_transition = dissolve
        define config.after_load_transition = None
        define config.end_game_transition = None

        ## Window management #######################################################

        define config.window = "auto"
        define config.window_show_transition = Dissolve(.2)
        define config.window_hide_transition = Dissolve(.2)

        ## Preference defaults #####################################################

        default preferences.text_cps = 30
        default preferences.auto_forward_time = 15

        ## Save directory ##########################################################

        define config.save_directory = "infiniti_v_scene"
        '''
        
        with open(os.path.join(game_dir, "options.rpy"), "w", encoding="utf-8") as f:
            f.write(options_content)
        
        # Create basic GUI configuration
        gui_content = '''
        ## GUI Configuration ######################################################

        ## Colors ##################################################################
        define gui.accent_color = '#0066cc'
        define gui.idle_color = '#888888'
        define gui.hover_color = '#66b3ff'
        define gui.selected_color = '#ffffff'
        define gui.insensitive_color = '#8888887f'

        ## Fonts ###################################################################
        define gui.default_font = "DejaVuSans.ttf"
        define gui.name_font = "DejaVuSans-Bold.ttf"
        define gui.interface_font = "DejaVuSans.ttf"

        ## Text #####################################################################
        define gui.text_size = 22
        define gui.name_text_size = 30
        define gui.interface_text_size = 22
        '''

        with open(os.path.join(game_dir, "gui.rpy"), "w", encoding="utf-8") as f:
            f.write(gui_content)
    
    def _create_sound_effects(self, audio_dir: str):
        """Create placeholder sound effect files"""
        sound_effects = {
            "sfx_rain.mp3": "Rain sound effect placeholder",
            "sfx_footsteps.mp3": "Footsteps sound effect placeholder", 
            "sfx_door.mp3": "Door sound effect placeholder",
            "sfx_ambient.mp3": "Ambient sound effect placeholder"
        }
        
        for filename, description in sound_effects.items():
            placeholder_file = os.path.join(audio_dir, filename.replace('.mp3', '.txt'))
            with open(placeholder_file, 'w') as f:
                f.write(f"{description}\n")
                f.write("This is a placeholder. Replace with actual audio file for full functionality.\n")
    
    def _create_character_images(self, images_dir: str, script: List[Dict]):
        """Create placeholder character image files"""
        characters = set()
        emotions = set()
        
        # Extract characters and emotions from script
        for block in script:
            if block.get("type") == "dialogue":
                character = block.get("character", "")
                emotion = block.get("emotion", "neutral")
                if character and character != "narrator":
                    characters.add(character)
                    emotions.add(emotion)
        
        # Add default emotions
        emotions.update(["neutral", "happy", "sad", "angry", "surprised", "concerned", "serious"])
        
        # Create placeholder images for each character and emotion
        for character in characters:
            char_name = character.lower().replace(" ", "_").replace("character_", "char_")
            for emotion in emotions:
                filename = f"{char_name}_{emotion}.png"
                placeholder_file = os.path.join(images_dir, filename.replace('.png', '.txt'))
                with open(placeholder_file, 'w') as f:
                    f.write(f"Character image placeholder: {character} - {emotion}\n")
                    f.write("Replace with actual character image for full functionality.\n")
    
    def _create_background_images(self, images_dir: str):
        """Create placeholder background image files"""
        backgrounds = {
            "warehouse.jpg": "Dark warehouse background",
            "dark_room.jpg": "Dark interrogation room background", 
            "office.jpg": "Office background",
            "street.jpg": "Street background"
        }
        
        for filename, description in backgrounds.items():
            placeholder_file = os.path.join(images_dir, filename.replace('.jpg', '.txt'))
            with open(placeholder_file, 'w') as f:
                f.write(f"Background placeholder: {description}\n")
                f.write("Replace with actual background image for full functionality.\n")
    
    def _generate_renpy_script(self, script: List[Dict], audio_files: Dict[str, str]) -> str:
        """Generate the Ren'Py script content with full support for actions, dialogue, and sound effects"""
        
        renpy_script = '''# ∞-V Generated Scene Script
            # This script was automatically generated by Infiniti-V

            # Define transforms for character movement and positioning
            transform left_enter:
                xalign 0.3 yalign 1.0
                alpha 0.0
                ease 1.0 alpha 1.0

            transform right_enter:
                xalign 0.7 yalign 1.0
                alpha 0.0
                ease 1.0 alpha 1.0

            transform center_focus:
                xalign 0.5 yalign 1.0
                ease 0.5 zoom 1.1

            transform fade_out:
                alpha 1.0
                ease 1.0 alpha 0.0

            # Sound effects
            define audio.rain = "audio/sfx_rain.mp3"
            define audio.footsteps = "audio/sfx_footsteps.mp3"
            define audio.door = "audio/sfx_door.mp3"
            define audio.ambient = "audio/sfx_ambient.mp3"

            # Background definitions
            image bg warehouse = "images/warehouse.jpg"
            image bg dark_room = "images/dark_room.jpg"
            image bg black = "#000000"

            # Character images (placeholders)
            image character_a neutral = "images/character_a_neutral.png"
            image character_a concerned = "images/character_a_concerned.png"
            image character_b serious = "images/character_b_serious.png"
            image character_b angry = "images/character_b_angry.png"

            # Define characters
            '''
        
        # Extract unique characters from script
        characters = set()
        character_emotions = {}

        for block in script:
            if block.get("type") == "dialogue":
                character = block.get("character", "narrator")
                emotion = block.get("emotion", "neutral")
                characters.add(character)
                if character not in character_emotions:
                    character_emotions[character] = set()
                character_emotions[character].add(emotion)
        
        # Define characters in Ren'Py format with colors
        character_colors = {
            "Character A": "#66b3ff",
            "Character B": "#ff6b6b", 
            "Detective": "#4ecdc4",
            "Suspect": "#ffe66d"
        }
        
        for character in characters:
            char_name = character.lower().replace(" ", "_").replace("character_", "char_")
            if char_name == "narrator":
                renpy_script += f'define {char_name} = Character(None, kind=nvl)\n'
            else:
                color = character_colors.get(character, "#ffffff")
                renpy_script += f'define {char_name} = Character("{character}", color="{color}")\n'
        
        renpy_script += '\n# Main scene\nlabel start:\n\n'
        
        # Initialize scene
        current_background = "black"
        scene_initialized = False
        character_positions = {}
        
        # Process script blocks in order
        for i, block in enumerate(script):
            block_id = block.get("id", "")
            block_type = block.get("type", "")
            
            if block_type == "scene":
                # Scene setup
                setting = block.get("setting", "Unknown location")
                description = block.get("description", "")
                
                # Determine background from setting
                if "warehouse" in setting.lower():
                    current_background = "warehouse"
                elif "dark" in setting.lower() or "room" in setting.lower():
                    current_background = "dark_room"
                else:
                    current_background = "black"
                
                renpy_script += f'    # Scene: {setting}\n'
                renpy_script += f'    # {description}\n'
                renpy_script += f'    scene bg {current_background}\n'
                renpy_script += '    with fade\n\n'
                scene_initialized = True
                
            elif block_type == "environment":
                # Environmental actions and atmosphere
                description = block.get("description", "")
                sound_implications = block.get("environmental_impact", {}).get("sound_implications", [])
                
                renpy_script += f'    # Environment: {description}\n'
                
                # Add sound effects based on environmental sounds
                for sound in sound_implications:
                    if "rain" in sound:
                        renpy_script += '    play sound audio.rain loop\n'
                    elif "footstep" in sound:
                        renpy_script += '    play sound audio.footsteps\n'
                    elif "drip" in sound or "thunder" in sound:
                        renpy_script += '    play sound audio.ambient loop\n'
                
                # Add visual effects
                visual_elements = block.get("visual_elements", {})
                if visual_elements.get("lighting_change"):
                    renpy_script += '    with dissolve\n'
                
                renpy_script += '\n'
                
            elif block_type == "movement":
                # Character movement and positioning
                character = block.get("character", "")
                description = block.get("description", "")
                sound_implications = block.get("environmental_impact", {}).get("sound_implications", [])
                
                if character:
                    char_name = character.lower().replace(" ", "_").replace("character_", "char_")
                    char_image = char_name + "_neutral"
                    
                    renpy_script += f'    # Movement: {description}\n'
                    
                    # Add footstep sounds
                    if any("footstep" in sound for sound in sound_implications):
                        renpy_script += '    play sound audio.footsteps\n'
                    
                    # Show character entering
                    if char_name not in character_positions:
                        if "A" in character or "Detective" in character:
                            renpy_script += f'    show {char_image} at left_enter\n'
                            character_positions[char_name] = "left"
                        else:
                            renpy_script += f'    show {char_image} at right_enter\n'
                            character_positions[char_name] = "right"
                    
                    renpy_script += '    with dissolve\n\n'
                else:
                    renpy_script += f'    # Action: {description}\n\n'
                    
            elif block_type == "dialogue":
                if not scene_initialized:
                    renpy_script += f'    scene bg {current_background}\n'
                    renpy_script += '    with fade\n\n'
                    scene_initialized = True
                
                character = block.get("character", "narrator")
                text = block.get("text", "")
                emotion = block.get("emotion", "neutral")
                
                # Clean character name for Ren'Py
                char_name = character.lower().replace(" ", "_").replace("character_", "char_")
                
                # Handle character images and emotions
                if char_name != "narrator" and character != "narrator":
                    char_image = f"{char_name}_{emotion}" if emotion != "neutral" else f"{char_name}_neutral"
                    
                    # Show character if not already shown
                    if char_name not in character_positions:
                        if "A" in character or "Detective" in character:
                            renpy_script += f'    show {char_image} at left_enter\n'
                            character_positions[char_name] = "left"
                        else:
                            renpy_script += f'    show {char_image} at right_enter\n'
                            character_positions[char_name] = "right"
                    else:
                        # Change expression
                        renpy_script += f'    show {char_image}\n'
                    
                    # Focus on speaking character
                    renpy_script += f'    show {char_image} at center_focus\n'
                
                # Add voice file if available
                if block_id in audio_files:
                    audio_file = audio_files[block_id]
                    audio_filename = os.path.basename(audio_file)
                    if not audio_filename.endswith('.txt'):
                        renpy_script += f'    voice "audio/{audio_filename}"\n'
                
                # Add the dialogue with proper character
                if char_name == "narrator":
                    renpy_script += f'    "{text}"\n\n'
                else:
                    # Add emotional context as a comment
                    if emotion != "neutral":
                        renpy_script += f'    # Emotion: {emotion}\n'
                    renpy_script += f'    {char_name} "{text}"\n\n'
                
            elif block_type == "action":
                # Generic actions
                description = block.get("description", "")
                renpy_script += f'    # Action: {description}\n'
                renpy_script += '    with dissolve\n\n'
        
        # End the scene
        renpy_script += '    # Scene complete\n'
        renpy_script += '    "Scene complete! Thank you for watching this ∞-V generated scene."\n'
        renpy_script += '    return\n'
        
        return renpy_script
    
    def _build_scene(self, project_path: str, project_name: str) -> Dict[str, Any]:
        """Attempt to build the Ren'Py scene"""
        
        try:
            if self.renpy_sdk_path and os.path.exists(self.renpy_sdk_path):
                # Try to build with Ren'Py SDK
                return self._build_with_renpy_sdk(project_path, project_name)
            else:
                # Create a simple HTML preview instead
                return self._create_html_preview(project_path, project_name)
                
        except Exception as e:
            logger.error(f"Error building scene: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _build_with_renpy_sdk(self, project_path: str, project_name: str) -> Dict[str, Any]:
        """Build the scene using Ren'Py SDK"""
        
        try:
            # This would call the Ren'Py SDK to build the project
            # For now, we'll create a placeholder
            logger.info("Ren'Py SDK build would happen here")
            
            return {
                "type": "renpy_project",
                "project_path": project_path,
                "playable": True,
                "preview_url": f"file://{project_path}/index.html"
            }
              except Exception as e:
            logger.error(f"Ren'Py SDK build failed: {str(e)}")
            return self._create_html_preview(project_path, project_name)

    def _create_html_preview(self, project_path: str, project_name: str) -> Dict[str, Any]:
        """Create an enhanced HTML preview of the scene with script visualization"""
        
        try:
            # Read the generated script
            script_file = os.path.join(project_path, "game", "script.rpy")
            with open(script_file, "r", encoding="utf-8") as f:
                script_content = f.read()
                
            # Parse the original script data for interactive preview
            script_data_file = None
            script_blocks = []
            
            # Try to find script.json in multiple locations
            possible_paths = [
                os.path.join(project_path, "..", "..", "scripts", "script.json"),
                os.path.join(project_path, "scripts", "script.json"),
                os.path.join(os.path.dirname(project_path), "scripts", "script.json")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    script_data_file = path
                    break
            
            if script_data_file:
                try:
                    with open(script_data_file, "r", encoding="utf-8") as f:
                        script_blocks = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load script data: {e}")
                    script_blocks = []
            
            # Create enhanced HTML preview
            html_content = f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>∞-V Scene Preview: {project_name}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                        background: linear-gradient(135deg, #1a1a2e, #16213e);
                        color: #ffffff;
                        line-height: 1.6;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 40px;
                        padding: 30px;
                        background: rgba(0, 102, 204, 0.1);
                        border-radius: 15px;
                        border: 1px solid rgba(102, 179, 255, 0.3);
                    }}
                    .header h1 {{
                        background: linear-gradient(45deg, #66b3ff, #0066cc);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        font-size: 2.5em;
                        margin-bottom: 10px;
                    }}
                    .scene-player {{
                        background: rgba(42, 42, 42, 0.8);
                        border-radius: 15px;
                        padding: 30px;
                        margin: 30px 0;
                        border: 1px solid rgba(102, 179, 255, 0.2);
                    }}
                    .scene-controls {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .btn {{
                        background: linear-gradient(45deg, #0066cc, #66b3ff);
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        margin: 0 10px;
                        border-radius: 25px;
                        cursor: pointer;
                        font-size: 16px;
                        transition: transform 0.2s;
                    }}
                    .btn:hover {{
                        transform: translateY(-2px);
                    }}
                    .scene-display {{
                        min-height: 400px;
                        background: rgba(0, 0, 0, 0.8);
                        border-radius: 10px;
                        padding: 30px;
                        position: relative;
                        border: 2px solid rgba(102, 179, 255, 0.3);
                    }}
                    .dialogue-box {{
                        position: absolute;
                        bottom: 20px;
                        left: 20px;
                        right: 20px;
                        background: rgba(42, 42, 60, 0.95);
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid rgba(102, 179, 255, 0.5);
                        display: none;
                    }}
                    .character-name {{
                        font-weight: bold;
                        font-size: 18px;
                        margin-bottom: 10px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }}
                    .dialogue-text {{
                        font-size: 16px;
                        line-height: 1.8;
                    }}
                    .character-a {{ color: #66b3ff; }}
                    .character-b {{ color: #ff6b6b; }}
                    .detective {{ color: #4ecdc4; }}
                    .suspect {{ color: #ffe66d; }}
                    .action-display {{
                        text-align: center;
                        font-style: italic;
                        color: #cccccc;
                        margin: 20px 0;
                        padding: 15px;
                        background: rgba(64, 64, 64, 0.5);
                        border-radius: 8px;
                        border-left: 4px solid #66b3ff;
                    }}
                    .environment-display {{
                        text-align: center;
                        color: #99ccff;
                        font-size: 14px;
                        margin: 15px 0;
                        padding: 12px;
                        background: rgba(25, 50, 100, 0.3);
                        border-radius: 6px;
                    }}
                    .progress-bar {{
                        background: rgba(102, 179, 255, 0.2);
                        height: 4px;
                        border-radius: 2px;
                        margin: 20px 0;
                    }}
                    .progress-fill {{
                        background: linear-gradient(90deg, #66b3ff, #0066cc);
                        height: 100%;
                        border-radius: 2px;
                        width: 0%;
                        transition: width 0.3s ease;
                    }}
                    .script-container {{
                        background: rgba(30, 30, 30, 0.9);
                        border-radius: 10px;
                        padding: 25px;
                        margin: 30px 0;
                        border: 1px solid rgba(102, 179, 255, 0.2);
                    }}
                    .renpy-script {{
                        background: rgba(16, 16, 16, 0.9);
                        padding: 20px;
                        border-radius: 8px;
                        white-space: pre-wrap;
                        font-family: 'Courier New', monospace;
                        font-size: 14px;
                        overflow-x: auto;
                        max-height: 400px;
                        overflow-y: auto;
                        border: 1px solid rgba(102, 179, 255, 0.1);
                    }}
                    .toggle-btn {{
                        background: rgba(102, 179, 255, 0.2);
                        color: #66b3ff;
                        border: 1px solid rgba(102, 179, 255, 0.5);
                        padding: 8px 16px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: all 0.2s;
                    }}
                    .toggle-btn:hover {{
                        background: rgba(102, 179, 255, 0.3);
                    }}
                    .stats {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin: 30px 0;
                    }}
                    .stat-box {{
                        background: rgba(42, 42, 60, 0.6);
                        padding: 20px;
                        border-radius: 10px;
                        text-align: center;
                        border: 1px solid rgba(102, 179, 255, 0.2);
                    }}
                    .stat-number {{
                        font-size: 2em;
                        font-weight: bold;
                        color: #66b3ff;
                    }}
                    .audio-indicator {{
                        display: inline-block;
                        width: 12px;
                        height: 12px;
                        background: #4CAF50;
                        border-radius: 50%;
                        margin-left: 10px;
                        animation: pulse 2s infinite;
                    }}
                    @keyframes pulse {{
                        0% {{ opacity: 1; }}
                        50% {{ opacity: 0.5; }}
                        100% {{ opacity: 1; }}
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>∞-V Scene Preview</h1>
                    <h2>{project_name}</h2>
                    <p>AI-Powered Interactive Scene Generator</p>
                </div>
                
                <div class="scene-player">
                    <h3>Interactive Scene Player</h3>
                    <div class="scene-controls">
                        <button class="btn" onclick="startScene()">▶ Start Scene</button>
                        <button class="btn" onclick="pauseScene()">⏸ Pause</button>
                        <button class="btn" onclick="resetScene()">⏮ Reset</button>
                        <button class="btn" onclick="nextBlock()">⏭ Next</button>
                    </div>
                    
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress"></div>
                    </div>
                    
                    <div class="scene-display" id="sceneDisplay">
                        <div class="dialogue-box" id="dialogueBox">
                            <div class="character-name" id="characterName"></div>
                            <div class="dialogue-text" id="dialogueText"></div>
                            <span class="audio-indicator" id="audioIndicator" style="display: none;"></span>
                        </div>
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number" id="dialogueCount">0</div>
                        <div>Dialogue Blocks</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number" id="characterCount">0</div>
                        <div>Characters</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number" id="actionCount">0</div>
                        <div>Actions</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number" id="audioCount">0</div>
                        <div>Audio Files</div>
                    </div>
                </div>
                
                <div class="script-container">
                    <h3>Generated Ren'Py Script</h3>
                    <button class="toggle-btn" onclick="toggleScript()">Show/Hide Script</button>
                    <div class="renpy-script" id="renpyScript" style="display: none;">{script_content}</div>
                </div>
                
                <script>
                    // Scene data and state
                    let sceneBlocks = {json.dumps(script_blocks)};
                    let currentBlock = 0;
                    let isPlaying = false;
                    let sceneTimer = null;
                    
                    // Initialize scene
                    document.addEventListener('DOMContentLoaded', function() {{
                        updateStats();
                        if (sceneBlocks.length > 0) {{
                            resetScene();
                        }}
                    }});
                    
                    function updateStats() {{
                        const dialogues = sceneBlocks.filter(b => b.type === 'dialogue');
                        const actions = sceneBlocks.filter(b => b.type === 'action' || b.type === 'movement' || b.type === 'environment');
                        const characters = new Set(dialogues.map(d => d.character)).size;
                        const audios = dialogues.filter(d => d.audio).length;
                        
                        document.getElementById('dialogueCount').textContent = dialogues.length;
                        document.getElementById('characterCount').textContent = characters;
                        document.getElementById('actionCount').textContent = actions.length;
                        document.getElementById('audioCount').textContent = audios;
                    }}
                    
                    function startScene() {{
                        isPlaying = true;
                        playCurrentBlock();
                    }}
                    
                    function pauseScene() {{
                        isPlaying = false;
                        if (sceneTimer) {{
                            clearTimeout(sceneTimer);
                            sceneTimer = null;
                        }}
                    }}
                    
                    function resetScene() {{
                        pauseScene();
                        currentBlock = 0;
                        updateProgress();
                        hideDialogue();
                        clearDisplay();
                    }}
                    
                    function nextBlock() {{
                        if (currentBlock < sceneBlocks.length - 1) {{
                            currentBlock++;
                            playCurrentBlock();
                        }}
                    }}
                    
                    function playCurrentBlock() {{
                        if (currentBlock >= sceneBlocks.length) {{
                            pauseScene();
                            return;
                        }}
                        
                        const block = sceneBlocks[currentBlock];
                        updateProgress();
                        
                        if (block.type === 'dialogue') {{
                            showDialogue(block);
                        }} else if (block.type === 'action' || block.type === 'movement') {{
                            showAction(block);
                        }} else if (block.type === 'environment') {{
                            showEnvironment(block);
                        }}
                        
                        // Auto-advance if playing
                        if (isPlaying) {{
                            const duration = getDuration(block);
                            sceneTimer = setTimeout(() => {{
                                currentBlock++;
                                playCurrentBlock();
                            }}, duration);
                        }}
                    }}
                    
                    function showDialogue(block) {{
                        const dialogueBox = document.getElementById('dialogueBox');
                        const characterName = document.getElementById('characterName');
                        const dialogueText = document.getElementById('dialogueText');
                        const audioIndicator = document.getElementById('audioIndicator');
                        
                        characterName.textContent = block.character || 'Narrator';
                        characterName.className = 'character-name ' + getCharacterClass(block.character);
                        dialogueText.textContent = block.text || '';
                        
                        if (block.audio) {{
                            audioIndicator.style.display = 'inline-block';
                        }} else {{
                            audioIndicator.style.display = 'none';
                        }}
                        
                        dialogueBox.style.display = 'block';
                        clearDisplay();
                    }}
                    
                    function showAction(block) {{
                        hideDialogue();
                        const display = document.getElementById('sceneDisplay');
                        const actionDiv = document.createElement('div');
                        actionDiv.className = 'action-display';
                        actionDiv.textContent = '✦ ' + (block.description || 'Action occurs');
                        display.appendChild(actionDiv);
                    }}
                    
                    function showEnvironment(block) {{
                        hideDialogue();
                        const display = document.getElementById('sceneDisplay');
                        const envDiv = document.createElement('div');
                        envDiv.className = 'environment-display';
                        envDiv.textContent = '🌆 ' + (block.description || 'Environmental change');
                        display.appendChild(envDiv);
                    }}
                    
                    function hideDialogue() {{
                        document.getElementById('dialogueBox').style.display = 'none';
                    }}
                    
                    function clearDisplay() {{
                        const display = document.getElementById('sceneDisplay');
                        const children = display.children;
                        for (let i = children.length - 1; i >= 0; i--) {{
                            const child = children[i];
                            if (child.id !== 'dialogueBox') {{
                                child.remove();
                            }}
                        }}
                    }}
                    
                    function getCharacterClass(character) {{
                        if (!character) return '';
                        const lower = character.toLowerCase();
                        if (lower.includes('character a') || lower.includes('detective')) return 'character-a';
                        if (lower.includes('character b') || lower.includes('suspect')) return 'character-b';
                        if (lower.includes('detective')) return 'detective';
                        if (lower.includes('suspect')) return 'suspect';
                        return '';
                    }}
                    
                    function getDuration(block) {{
                        if (block.type === 'dialogue') {{
                            const textLength = (block.text || '').length;
                            return Math.max(2000, textLength * 50); // 50ms per character, min 2s
                        }}
                        return 2000; // 2 seconds for actions/environment
                    }}
                    
                    function updateProgress() {{
                        const progress = sceneBlocks.length > 0 ? (currentBlock / sceneBlocks.length) * 100 : 0;
                        document.getElementById('progress').style.width = progress + '%';
                    }}
                    
                    function toggleScript() {{
                        const script = document.getElementById('renpyScript');
                        script.style.display = script.style.display === 'none' ? 'block' : 'none';
                    }}
                </script>
            </body>
            </html>
            '''
            
            # Save HTML preview
            preview_file = os.path.join(project_path, "preview.html")
            with open(preview_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            return {
                "type": "html_preview",
                "preview_file": preview_file,
                "preview_url": f"file://{os.path.abspath(preview_file)}",
                "playable": True,
                "project_path": project_path,
                "interactive": True
            }
            
        except Exception as e:
            logger.error(f"Error creating HTML preview: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _create_fallback_scene(self, script: List[Dict], audio_files: Dict[str, str]) -> Dict[str, Any]:
        """Create a fallback scene when rendering fails"""
        
        try:
            # Create a simple text-based scene summary
            fallback_dir = os.path.join(self.output_dir, "fallback")
            os.makedirs(fallback_dir, exist_ok=True)
            
            summary_file = os.path.join(fallback_dir, "scene_summary.txt")
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write("∞-V Generated Scene Summary\n")
                f.write("=" * 30 + "\n\n")
                
                for i, block in enumerate(script, 1):
                    f.write(f"Block {i} (ID: {block.get('id', 'unknown')}):\n")
                    
                    if block.get("type") == "dialogue":
                        character = block.get("character", "Unknown")
                        text = block.get("text", "")
                        emotion = block.get("emotion", "neutral")
                        f.write(f"  Character: {character} ({emotion})\n")
                        f.write(f"  Dialogue: \"{text}\"\n")
                        
                        # Note audio file if available
                        block_id = block.get("id", "")
                        if block_id in audio_files:
                            f.write(f"  Audio: {audio_files[block_id]}\n")
                    
                    elif block.get("type") == "action":
                        description = block.get("description", "")
                        f.write(f"  Action: {description}\n")
                    
                    f.write("\n")
            
            return {
                "type": "fallback",
                "summary_file": summary_file,
                "status": "fallback_created",
                "message": "Scene rendering failed, created text summary instead"
            }
            
        except Exception as e:
            logger.error(f"Error creating fallback scene: {str(e)}")
            return {
                "status": "error",
                "message": f"Complete rendering failure: {str(e)}"
            }
