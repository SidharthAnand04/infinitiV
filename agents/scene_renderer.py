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

    def render_scene(self, script: Union[Dict, List[Dict]], audio_files: Dict[str, str], project_dir: str = None, extra_images: list = None) -> Dict[str, Any]:
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
            
            # Create Ren'Py project structure and process images
            image_info = self._create_renpy_project(project_path, script_blocks, audio_files)
            
            # Generate Ren'Py script with AI instead of the template-based method
            # First try AI generation, fall back to template if needed
            renpy_script = self._generate_renpy_script_with_ai(
                script_blocks, 
                audio_files, 
                extra_images=extra_images,
                image_info=image_info
            )
            
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
    # def render_scene(self, script: Union[Dict, List[Dict]], audio_files: Dict[str, str], project_dir: str = None, extra_images: list = None) -> Dict[str, Any]:
    #     """
    #     Render the scene using Ren'Py engine
    #     Returns information about the rendered scene
    #     """
    #     try:
    #         logger.info("Starting scene rendering with Ren'Py")
    #         # Normalize script format
    #         if isinstance(script, dict):
    #             script_blocks = script.get('blocks', [])
    #             script_dict = script
    #         else:
    #             script_blocks = script
    #             script_dict = {'blocks': script}
            
    #         # Create project name based on script content
    #         project_name = self._generate_project_name(script_dict)
            
    #         # Use provided project_dir or create new one
    #         if project_dir:
    #             project_path = os.path.join(project_dir, "renpy_project", project_name)
    #         else:
    #             project_path = os.path.join(self.project_dir, project_name)
            
    #         # Create Ren'Py project structure and process images
    #         image_info = self._create_renpy_project(project_path, script_blocks, audio_files)
            
    #         # Generate Ren'Py script with processed image information
    #         renpy_script = self._generate_renpy_script(
    #             script_blocks, 
    #             audio_files, 
    #             extra_images=extra_images,
    #             image_info=image_info
    #         )
            
    #         # Write script file
    #         script_file = os.path.join(project_path, "game", "script.rpy")
    #         with open(script_file, "w", encoding="utf-8") as f:
    #             f.write(renpy_script)
            
    #         # Try to build/export the scene
    #         scene_output = self._build_scene(project_path, project_name)
            
    #         return {
    #             "project_name": project_name,
    #             "project_path": project_path,
    #             "script_file": script_file,
    #             "scene_output": scene_output,
    #             "status": "success"
    #         }
    #     except Exception as e:
    #         logger.error(f"Error in scene rendering: {str(e)}")
    #         return self._create_fallback_scene(script_blocks, audio_files)
        
        
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
    
    def _process_background_images(self, images_dir: str, project_images_dir: str) -> Dict[str, str]:
        """
        Process background images from the images directory and copy them to the project
        Returns a dictionary mapping background names to image paths
        """
        background_images = {}
        
        # Ensure images directory exists
        if not os.path.exists(images_dir):
            return background_images
        
        # Create backgrounds subdirectory in project
        bg_dir = os.path.join(project_images_dir, "backgrounds")
        os.makedirs(bg_dir, exist_ok=True)
        
        # Look for background images in the images directory
        try:
            for file in os.listdir(images_dir):
                lower_file = file.lower()
                if not (lower_file.endswith('.png') or lower_file.endswith('.jpg') or lower_file.endswith('.jpeg')):
                    continue
                    
                # Check if it's a background image
                if ("background" in lower_file or "bg_" in lower_file or 
                    "scene" in lower_file or "setting" in lower_file):
                    
                    # Determine background name
                    bg_name = "background"
                    for possible_bg in ["warehouse", "office", "room", "street", "park", "cafe", "night"]:
                        if possible_bg in lower_file:
                            bg_name = possible_bg
                            break
                    
                    target_filename = f"{bg_name}.png"
                    target_path = os.path.join(bg_dir, target_filename)
                    
                    # Copy the image
                    shutil.copy2(os.path.join(images_dir, file), target_path)
                    logger.info(f"Copied background image: {file} -> {target_filename}")
                    
                    # Store the background image mapping
                    background_images[bg_name] = target_filename
        
        except Exception as e:
            logger.error(f"Error processing background images: {str(e)}")
        
        return background_images


    def _process_character_images(self, images_dir: str, project_images_dir: str) -> Dict[str, str]:
        """
        Process character images from the images directory and copy them to the project
        Returns a dictionary mapping character names to image paths
        """
        character_images = {}
        
        # Ensure images directory exists
        if not os.path.exists(images_dir):
            logger.warning(f"Images directory not found: {images_dir}")
            return character_images
        
        # Create characters subdirectory in project
        chars_dir = os.path.join(project_images_dir, "characters")
        os.makedirs(chars_dir, exist_ok=True)
        
        # Look for character images in the images directory
        try:
            for file in os.listdir(images_dir):
                lower_file = file.lower()
                if not (lower_file.endswith('.png') or lower_file.endswith('.jpg') or lower_file.endswith('.jpeg')):
                    continue
                    
                # Check if it's a character image
                character_name = None
                
                # Common character naming patterns
                if "character_a" in lower_file or "character-a" in lower_file:
                    character_name = "character_a"
                elif "character_b" in lower_file or "character-b" in lower_file:
                    character_name = "character_b"
                elif "detective" in lower_file:
                    character_name = "detective"
                elif "suspect" in lower_file:
                    character_name = "suspect"
                elif any(name in lower_file for name in ["char1", "char_1", "character1"]):
                    character_name = "character_a"
                elif any(name in lower_file for name in ["char2", "char_2", "character2"]):
                    character_name = "character_b"
                
                # If we identified a character, copy the image
                if character_name:
                    # Check for emotion indicators in filename
                    emotion = "neutral"
                    for possible_emotion in ["happy", "sad", "angry", "surprised", "neutral", "concerned", "serious"]:
                        if possible_emotion in lower_file:
                            emotion = possible_emotion
                            break
                    
                    target_filename = f"{character_name}_{emotion}.png"
                    target_path = os.path.join(chars_dir, target_filename)
                    
                    # Copy the image
                    shutil.copy2(os.path.join(images_dir, file), target_path)
                    logger.info(f"Copied character image: {file} -> {target_filename}")
                    
                    # Store the character image mapping
                    if character_name not in character_images:
                        character_images[character_name] = {}
                    character_images[character_name][emotion] = target_filename
                
        except Exception as e:
            logger.error(f"Error processing character images: {str(e)}")
        
        return character_images


    def _create_renpy_project(self, project_path: str, script: List[Dict], audio_files: Dict[str, str]):
        """Create the basic Ren'Py project structure with enhanced asset support"""
        
        # Create directory structure
        game_dir = os.path.join(project_path, "game")
        images_dir = os.path.join(game_dir, "images")
        chars_dir = os.path.join(images_dir, "characters")
        bg_dir = os.path.join(images_dir, "backgrounds")
        audio_dir = os.path.join(game_dir, "audio")
        sfx_dir = os.path.join(audio_dir, "sfx")  # Add specific directory for sound effects
        
        os.makedirs(game_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(chars_dir, exist_ok=True)
        os.makedirs(bg_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(sfx_dir, exist_ok=True)  # Create sound effects directory
        
        # Process external images directory if it exists
        external_images_dir = "images"
        character_images = {}
        background_images = {}
        
        if os.path.exists(external_images_dir):
            character_images = self._process_character_images(external_images_dir, images_dir)
            background_images = self._process_background_images(external_images_dir, images_dir)
        
        # Copy audio files to project with more organized structure
        for block_id, audio_file in audio_files.items():
            if os.path.exists(audio_file):
                # Voice lines go directly in the audio directory
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
                        logger.info(f"Copied audio file: {audio_file} -> {target_file}")
                except Exception as e:
                    logger.warning(f"Could not copy audio file {audio_file}: {str(e)}")
        
        # Create sound effects with proper organization
        self._create_sound_effects(audio_dir, sfx_dir)
        
        # Create placeholder character images only if not found in external directory
        if not character_images:
            self._create_character_images(chars_dir, script)
        
        # Create placeholder backgrounds if not found in external directory
        if not background_images:
            self._create_background_images(bg_dir)
            
        # Create basic options.rpy
        options_content = '''## This file contains options that can be changed to customize your game.

## Graphics ################################################################

## These options control the width and height of the screen.
define config.screen_width = 1280   
define config.screen_height = 720

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
        gui_content = '''## GUI Configuration ######################################################

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

## Make character names show above dialogue
define gui.name_xpos = 240
define gui.name_ypos = 0
define gui.name_xalign = 0.0
define gui.namebox_width = 168
define gui.namebox_height = 39
    '''

        with open(os.path.join(game_dir, "gui.rpy"), "w", encoding="utf-8") as f:
            f.write(gui_content)
        
        # Create audio init file to ensure proper audio loading
        audio_init_content = '''## Audio initialization file
## This ensures all audio paths are correctly handled

init python:
    # Ensure audio directory exists when the game runs
    import os
    
    # Create audio directories if they don't exist
    if not os.path.exists(config.gamedir + "/audio"):
        os.makedirs(config.gamedir + "/audio")
    if not os.path.exists(config.gamedir + "/audio/sfx"):
        os.makedirs(config.gamedir + "/audio/sfx")
    '''
        
        with open(os.path.join(game_dir, "audio_init.rpy"), "w", encoding="utf-8") as f:
            f.write(audio_init_content)
        
        # Return the processed image information for use in script generation
        return {
            "character_images": character_images,
            "background_images": background_images
        }
        
    def _create_sound_effects(self, audio_dir: str, sfx_dir: str):
        """Create placeholder sound effect files and copy existing ones if available"""
        sound_effects = {
            "sfx_rain.mp3": "Rain sound effect placeholder",
            "sfx_footsteps.mp3": "Footsteps sound effect placeholder", 
            "sfx_door.mp3": "Door sound effect placeholder",
            "sfx_ambient.mp3": "Ambient sound effect placeholder",
            "sfx_wind.mp3": "Wind sound effect placeholder",
            "sfx_thunder.mp3": "Thunder sound effect placeholder",
            "sfx_typing.mp3": "Keyboard typing sound effect placeholder",
            "sfx_phone_ring.mp3": "Phone ringing sound effect placeholder",
            "sfx_heartbeat.mp3": "Heartbeat sound effect placeholder",
            "sfx_clock.mp3": "Clock ticking sound effect placeholder",
            "sfx_impact.mp3": "Impact sound effect placeholder"
        }
        
        # Check multiple locations for sound effects
        possible_sfx_locations = [
            os.path.join("resources", "audio", "sfx"),  # Original location
            os.path.join("audio"),                      # Project root audio folder
            os.path.join("audio", "sfx")                # Project root audio/sfx folder
        ]
        
        logger.info("Searching for sound effects in multiple locations")
        
        for filename, description in sound_effects.items():
            # Set target paths for both direct audio dir and sfx subdir
            main_target = os.path.join(audio_dir, filename)
            sfx_target = os.path.join(sfx_dir, filename)
            
            # Try to find the sound effect file in all possible locations
            sound_file_found = False
            
            for location in possible_sfx_locations:
                system_sfx_path = os.path.join(location, filename)
                if os.path.exists(system_sfx_path):
                    # Copy the real sound effect to both locations
                    shutil.copy2(system_sfx_path, main_target)
                    shutil.copy2(system_sfx_path, sfx_target)
                    logger.info(f"Copied sound effect from {location}: {filename}")
                    sound_file_found = True
                    break
            
            if not sound_file_found:
                # Create placeholder files
                placeholder_main = os.path.join(audio_dir, filename.replace('.mp3', '.txt'))
                placeholder_sfx = os.path.join(sfx_dir, filename.replace('.mp3', '.txt'))
                
                with open(placeholder_main, 'w') as f:
                    f.write(f"{description}\n")
                    f.write("This is a placeholder. Replace with actual audio file for full functionality.\n")
                    
                with open(placeholder_sfx, 'w') as f:
                    f.write(f"{description}\n")
                    f.write("This is a placeholder. Replace with actual audio file for full functionality.\n")
    def _create_character_images(self, images_dir: str, script: List[Dict]):
        """Create simple character image files"""
        # Only create character_a.png and character_b.png
        for char in ["character_a", "character_b"]:
            filename = f"{char}.jpg"
            placeholder_file = os.path.join(images_dir, filename.replace('.jpg', '.txt'))
            with open(placeholder_file, 'w') as f:
                f.write(f"Character image placeholder: {char}\n")
                f.write("Replace with actual character image for full functionality.\n")

    def _create_background_images(self, images_dir: str):
        """Create simple background image file"""
        filename = "background.jpg"
        placeholder_file = os.path.join(images_dir, filename.replace('.jpg', '.txt'))
        with open(placeholder_file, 'w') as f:
            f.write("Background placeholder: background\n")
            f.write("Replace with actual background image for full functionality.\n")
    def _generate_renpy_script(
        self,
        script: List[Dict],
        audio_files: Dict[str, str],
        extra_images: list = None,
        image_info: Dict = None
    ) -> str:

        image_info = image_info or {"character_images": {}, "background_images": {}}
        char_images   = image_info.get("character_images", {})
        bg_images     = image_info.get("background_images", {})

        # ---------- gather characters & give them safe identifiers ----------
        characters          = [blk["character"] for blk in script if blk.get("type") == "dialogue"]
        unique_chars        = list(dict.fromkeys(characters))          # preserve order
        char_var_for_name   = {name: f'char_{self._sanitize_name(name)}'
                               for name in unique_chars}

        # ---------- start building the .rpy text ----------
        out = [
            "# ∞-V Generated Scene Script",
            "# This script was automatically generated by Infiniti-V",
            "",
            "# Background images",
        ]

        # background block – default plus any detected backgrounds
        out.append('image bg background = "images/backgrounds/background.png"')
        for bg_key, bg_file in bg_images.items():
            out.append(f'image bg {bg_key} = "images/backgrounds/{bg_file}"')
        out.append("")

        # character image declarations (neutral only – easy to extend later)
        out.append("# Character images - neutral pose")
        for orig_name, var in char_var_for_name.items():
            out.append(f'image {var} = "images/characters/{var}_neutral.png"')
        out.append("")

        # movement / focus transforms
        out.append("# Define transforms for character movement and positioning")
        out.extend([
            "transform left:\n    xalign 0.3\n    yalign 1.0",
            "transform right:\n   xalign 0.7\n    yalign 1.0",
            "transform center:\n    xalign 0.5\n    yalign 1.0",
            "",
            "transform appear:\n  alpha 0.0\n    ease 1.0\n    alpha 1.0",
            "transform focus:\n   zoom 1.1\n    ease 0.5\n    alpha 1.0",
            "transform unfocus:\n   ease 0.5\n    zoom 1.0",
            ""
        ])

        # SFX map
        out.extend([
            "# Sound effects",
            'define audio.rain      = "audio/sfx_rain.mp3"',
            'define audio.footsteps = "audio/sfx_footsteps.mp3"',
            'define audio.door      = "audio/sfx_door.mp3"',
            'define audio.ambient   = "audio/sfx_ambient.mp3"',
            ""
        ])

        # colour palette (fallback to steel-blue if unknown)
        colour_palette = {
            "Character A": "#66b3ff",
            "Character B": "#ff6b6b",
            "Detective":   "#4ecdc4",
            "Suspect":     "#ffe66d",
        }

        out.append("# Define characters")
        for orig_name, var in char_var_for_name.items():
            colour = colour_palette.get(orig_name, "#66b3ff")
            out.append(f'define {var} = Character("{orig_name}", color="{colour}")')
        out.append("")

        # ---------- scene body ----------
        out.extend([
            "# Main scene",
            "label start:",
            "    # Scene: Unknown location",
            "    # Scene begins in Unknown location with a neutral atmosphere.",
            "    scene bg background",
            "    with fade",
            ""
        ])

        # keep track of which characters have been shown (to call 'show' only once)
        shown = set()

        for blk in script:
            btype = blk.get("type", "")
            bid   = blk.get("id", "")
            char  = blk.get("character", "")
            text  = blk.get("text", "")
            var   = char_var_for_name.get(char, "")           # may be None for non-dialogue

            if btype == "environment":
                desc = blk.get("description", "")
                out.append(f'    # Environment: {desc}')
                out.append(f'    "The camera slowly pans across the {desc.lower()}.\"\n')
                continue

            if btype == "movement":
                desc = blk.get("description", "")
                out.append(f'    # Movement: {desc}')
                continue

            if btype != "dialogue":
                continue

            # first appearance: place on left/right
            if var and var not in shown:
                pos = "left" if "a" in var else "right"
                out.append(f'    # Show {char} on the {pos}')
                out.append(f'    show {var} at {pos}, appear')
                shown.add(var)
                out.append("")

            # voice line if provided
            if bid in audio_files:
                out.append(f'    voice "audio/{os.path.basename(audio_files[bid])}"')

            # actual dialogue
            out.append(f'    {var} "{text}"\n')

        # wrap-up
        out.extend([
            "    # Scene complete",
            '    "Scene complete! Thank you for watching this ∞-V generated scene."',
            "    return",
            ""
        ])

        return "\n".join(out)
    
    def _generate_renpy_script_with_ai(
        self,
        script: List[Dict],
        audio_files: Dict[str, str],
        extra_images: list = None,
        image_info: Dict = None
    ) -> str:
        """Generate the Ren'Py script using Gemini"""
        try:
            # Initialize AI if not already available (similar to ScriptGenerator)
            if not hasattr(self, 'gemini_model'):
                try:
                    import google.generativeai as genai
                    gemini_key = os.getenv('GEMINI_API_KEY')
                    if gemini_key:
                        genai.configure(api_key=gemini_key)
                        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")
                        logger.info("Gemini model initialized for script generation")
                    else:
                        logger.warning("GEMINI_API_KEY not found, falling back to template-based script")
                        return self._generate_renpy_script(script, audio_files, extra_images, image_info)
                except ImportError:
                    logger.warning("Google GenerativeAI not available, falling back to template-based script")
                    return self._generate_renpy_script(script, audio_files, extra_images, image_info)
            
            # Process audio files to create proper paths relative to the game directory
            processed_audio_files = {}
            for block_id, audio_path in audio_files.items():
                if audio_path:
                    filename = os.path.basename(audio_path)
                    processed_audio_files[block_id] = filename
            
            # Prepare the image info
            image_info = image_info or {"character_images": {}, "background_images": {}}
            char_images = image_info.get("character_images", {})
            bg_images = image_info.get("background_images", {})
            
            # Gather characters & give them safe identifiers
            characters = [blk["character"] for blk in script if blk.get("type") == "dialogue"]
            unique_chars = list(dict.fromkeys(characters))  # preserve order
            char_var_for_name = {name: f'char_{self._sanitize_name(name)}' for name in unique_chars}
            


            # Build the prompt for the AI
            prompt = f"""
            Generate a complete Ren'Py script file based on the provided scene information:
            
            IMAGE INFORMATION:
            {image_info}

            CHARACTERS:
            {json.dumps(unique_chars, indent=2)}
            
            CHARACTER VARIABLES:
            {json.dumps(char_var_for_name, indent=2)}
            
            SCRIPT BLOCKS:
            {json.dumps(script, indent=2)}
            
            AUDIO FILES:
            {json.dumps(processed_audio_files, indent=2)}
            
            BACKGROUND IMAGES:
            {json.dumps(list(bg_images.keys()), indent=2)}
            
            FORMAT YOUR RESPONSE EXACTLY LIKE THIS TEMPLATE - including all sections, transforms, etc:
            
            ```
            # ∞-V Generated Scene Script
            # This script was automatically generated by Infiniti-V

            # Background images
            image bg background = "images/backgrounds/background.png"
            
            # Character images - neutral pose
            # Include character images for all characters in the script
            # example 
            # image char_character_a_neutral = "images/characters/character_a_neutral.png"
            #  look at the character files available 
            # it will be character_a_neutral.png or character_b_neutral.png like that 

            # Define transforms for character movement and positioning
            transform left:
                xalign 0.3
                yalign 1.0
                
            transform right:
                xalign 0.7
                yalign 1.0
                
            transform center:
                xalign 0.5
                yalign 1.0
                
            transform appear:
                alpha 0.0
                ease 1.0 alpha 1.0
                
            transform focus:
                zoom 1.1
                ease 0.5 alpha 1.0
                
            transform unfocus:
                ease 0.5 zoom 1.0
                
            # Sound effects - accessible as audio.effect_name
            define audio.rain = "audio/sfx_rain.mp3"
            define audio.footsteps = "audio/sfx_footsteps.mp3"
            define audio.door = "audio/sfx_door.mp3"
            define audio.ambient = "audio/sfx_ambient.mp3"
            define audio.wind = "audio/sfx_wind.mp3"
            define audio.thunder = "audio/sfx_thunder.mp3"
            define audio.typing = "audio/sfx_typing.mp3"
            define audio.phone_ring = "audio/sfx_phone_ring.mp3"
            define audio.heartbeat = "audio/sfx_heartbeat.mp3"
            define audio.clock = "audio/sfx_clock.mp3"
            
            # Define characters with appropriate colors
            # Character A should use #66b3ff
            # Character B should use #ff6b6b
            # Others can use appropriate colors
            
            # Main scene - include all dialogues, actions, environments
            label start:
                # Scene setup
                scene bg background
                with fade
                
                # Include all dialogue, actions, etc. in the correct format
                # For dialogue, use:
                #   char_variable "Dialogue text"
                
                # For voice lines when audio exists, use:
                #   voice "audio/filename.mp3"
                #   char_variable "Dialogue text"
                
                # For environment descriptions, use:
                #   "Description text"
                
                # For character entrances, use:
                #   show char_variable at position, appear
                
                # To play sound effects, use:
                #   play sound audio.effect_name
                
                # End with scene completion message
                "Scene complete! Thank you for watching this ∞-V generated scene."
                return
            ```
            
            IMPORTANT RULES:
            1. Output ONLY the Ren'Py script, no other text or comments
            2. Include ALL dialogue from the script blocks
            3. Properly format all character definitions, dialogues, and audio
            4. ALWAYS use "audio/" prefix for ALL audio files
            5. Maintain proper Ren'Py indentation (4 spaces)
            6. Add appropriate show/hide commands for characters
            7. Add sound effects at appropriate moments based on the environment
            8. The script must be properly formatted and syntactically valid
            
            After generating the script, verify it is correctly formatted with proper indentation, quotes, and syntax.
            Renpy version is 8.3.7. pay attention to the synteax that has been dated or phased out. for example do not use "with appear" use ", appear" instead
            """
            
            # Generate the script using AI
            response = self.gemini_model.generate_content(prompt)
            renpy_script = response.text
            
            # Clean up the response to extract just the script content
            if "```" in renpy_script:
                script_start = renpy_script.find("```")
                script_end = renpy_script.rfind("```")
                if script_start != -1 and script_end != -1 and script_end > script_start:
                    renpy_script = renpy_script[script_start + 3:script_end].strip()
                    # Remove language identifier if present
                    if renpy_script.startswith("python") or renpy_script.startswith("renpy"):
                        renpy_script = renpy_script.split("\n", 1)[1]
            
            # Verify that the script handles audio paths correctly
            if audio_files and "voice \"audio/" not in renpy_script:
                logger.warning("AI script doesn't properly reference audio files, adding a fix")
                # Add an audio path note at the top of the script
                audio_note = "\n# Note: Audio files are located in the audio/ directory\n"
                renpy_script = audio_note + renpy_script
            
            # Ensure sound effect definitions are present
            if "define audio.rain" not in renpy_script:
                logger.warning("AI script doesn't include sound effect definitions, adding them")
                sfx_definitions = """
    # Sound effects - accessible as audio.effect_name
    define audio.rain = "audio/sfx_rain.mp3"
    define audio.footsteps = "audio/sfx_footsteps.mp3"
    define audio.door = "audio/sfx_door.mp3"
    define audio.ambient = "audio/sfx_ambient.mp3"
    define audio.wind = "audio/sfx_wind.mp3"
    define audio.thunder = "audio/sfx_thunder.mp3"
    define audio.typing = "audio/sfx_typing.mp3"
    define audio.phone_ring = "audio/sfx_phone_ring.mp3"
    define audio.heartbeat = "audio/sfx_heartbeat.mp3"
    define audio.clock = "audio/sfx_clock.mp3"
    """
                # Find a good spot to insert SFX definitions
                if "# Define characters" in renpy_script:
                    renpy_script = renpy_script.replace("# Define characters", sfx_definitions + "\n# Define characters")
                else:
                    # Just add it near the top
                    lines = renpy_script.split('\n')
                    insertion_point = min(10, len(lines))
                    lines.insert(insertion_point, sfx_definitions)
                    renpy_script = '\n'.join(lines)
            
            if not renpy_script or len(renpy_script) < 100:
                logger.warning("AI generated script too short or empty, falling back to template")
                return self._generate_renpy_script(script, audio_files, extra_images, image_info)
            
            return renpy_script
            
        except Exception as e:
            logger.error(f"Error generating script with AI: {str(e)}")
            # Fall back to template-based method
            return self._generate_renpy_script(script, audio_files, extra_images, image_info)
        
    def _sanitize_name(self, raw: str) -> str:
        """
        Turn an arbitrary character label into a valid Ren'Py variable.
        • Lower-case, keep alphanumerics.
        • Convert all other chars to underscore, collapse repeats.
        • Prepend '_' if the result would start with a digit.
        """
        clean = ''.join(ch.lower() if ch.isalnum() else '_' for ch in raw)
        clean = '_'.join(filter(None, clean.split('_')))      # remove doubles
        if clean and clean[0].isdigit():
            clean = '_' + clean
        return clean or 'unknown'
    
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

