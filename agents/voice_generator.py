import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
import base64
import hashlib

# Try to import ElevenLabs
try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceGenerator:
    """Voice generation agent using ElevenLabs API"""
    
    def __init__(self):
        # Initialize caches first
        self.audio_cache = {}  # Cache for generated audio files
        self.voice_cache = {}  # Cache for created voices (character -> voice_id)
        
        # Initialize ElevenLabs client if available
        self.elevenlabs_client = None
        self.elevenlabs_key = None
        if ELEVENLABS_AVAILABLE:
            self.elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
            if self.elevenlabs_key and self.elevenlabs_key != 'your_elevenlabs_api_key_here':
                try:
                    self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_key)
                    logger.info("ElevenLabs client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize ElevenLabs client: {str(e)}")
            else:
                logger.warning("ELEVENLABS_API_KEY not configured")
        else:
            logger.warning("ElevenLabs library not available")
        
        # Clean up any existing custom voices (only after caches are initialized)
        self.delete_all_custom_voices()

        # Vapi fallback
        self.vapi_api_key = os.getenv('VAPI_API_KEY')
        self.base_url = "https://api.vapi.ai"
        
        if not self.elevenlabs_client and not self.vapi_api_key:
            logger.warning("No voice APIs configured, voice generation will use MP3 fallback")

    def generate_voices(self, script: List[Dict], project_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Generate voice audio for all dialogue blocks in the script
        Returns a dictionary mapping dialogue IDs to audio file paths/URLs
        Does NOT modify the script data
        """
        audio_files = {}
        character_voice_map: Dict[str, str] = {}  # Local mapping for this generation session
        
        try:
            for block in script:
                if block.get("type") != "dialogue":
                    continue
                
                block_id = block.get("id", "unknown")
                character = block.get("character", "Unknown")
                text = block.get("text", "")
                traits = block.get("traits", {})
                emotion = block.get("emotion", "neutral")
                
                if not text.strip():
                    continue
                
                logger.info(f"Generating voice for block {block_id}: {character}")
                
                # Determine output directory
                if project_dir:
                    audio_dir = os.path.join(project_dir, "audio")
                else:
                    audio_dir = "audio"
                os.makedirs(audio_dir, exist_ok=True)
                
                # Create consistent audio filename
                audio_filename = f"{character}_{block_id}.mp3"
                audio_path = os.path.join(audio_dir, audio_filename)
                
                # Check if audio already exists
                if os.path.exists(audio_path):
                    audio_files[block_id] = audio_path
                    logger.info(f"Audio already exists: {audio_path}")
                    continue
                
                # Get or create voice for this character
                voice_id = self._get_or_create_voice_for_character(
                    character, traits, emotion, character_voice_map
                )
                
                if voice_id:
                    # Generate audio with ElevenLabs
                    generated_audio = self._generate_audio_with_elevenlabs(
                        text, voice_id, audio_path
                    )
                    if generated_audio:
                        audio_files[block_id] = generated_audio
                    else:
                        # Fallback to MP3 file creation
                        mp3_audio = self._create_mp3_file(
                            text, character, block_id, audio_dir, audio_filename
                        )
                        audio_files[block_id] = mp3_audio
                else:
                    # Create MP3 file with proper naming
                    mp3_audio = self._create_mp3_file(
                        text, character, block_id, audio_dir, audio_filename
                    )
                    audio_files[block_id] = mp3_audio
                        
            return audio_files
            
        except Exception as e:
            logger.error(f"Error in voice generation: {str(e)}")
            return {}

    def _get_or_create_voice_for_character(self, character: str, traits: Dict, emotion: str, character_voice_map: Dict) -> Optional[str]:
        """Get or create voice for a character using ElevenLabs"""
        
        # Check if we already have a voice for this character in this session
        if character in character_voice_map:
            return character_voice_map[character]
        
        # Check if traits already include a voice_id
        voice_id = traits.get("elevenlabs_voice_id")
        if voice_id:
            character_voice_map[character] = voice_id
            return voice_id
        
        # Check global voice cache
        if character in self.voice_cache:
            voice_id = self.voice_cache[character]
            character_voice_map[character] = voice_id
            return voice_id
        
        if not self.elevenlabs_client:
            logger.warning(f"ElevenLabs client not available for character: {character}")
            return self._get_fallback_voice_id(traits)
        
        try:
            # Build voice description from traits and emotion
            description = self._build_voice_description(traits, emotion)
            
            # Create voice from description
            voice_id = self._create_voice_from_description(description, character)
            
            if voice_id:
                self.voice_cache[character] = voice_id
                character_voice_map[character] = voice_id
                return voice_id
            else:
                return self._get_fallback_voice_id(traits)
                
        except Exception as e:
            logger.error(f"Error creating voice for {character}: {str(e)}")
            return self._get_fallback_voice_id(traits)

    def _build_voice_description(self, traits: Dict, emotion: Optional[str] = None) -> str:
        """Build voice description from character traits"""
        parts = []
        
        if traits.get("age_range"):
            parts.append(traits["age_range"])
        if traits.get("gender"):
            parts.append(traits["gender"])
        if traits.get("voice_style"):
            parts.append(traits["voice_style"])
        if traits.get("accent"):
            parts.append(f"{traits['accent']} accent")
        if emotion and emotion != "neutral":
            parts.append(f"{emotion} tone")
        
        if not parts:
            parts = ["adult", "neutral", "clear"]
        
        return "A " + ", ".join(parts) + " voice."

    def _create_voice_from_description(self, description: str, name: str = "Unnamed") -> Optional[str]:
        """Create voice from description using ElevenLabs"""
        
        # Check if we already created this voice description
        if description in self.voice_cache:
            return self.voice_cache[description]

        try:
            logger.info(f"🎙️ Generating voice for: {description}")
            
            previews = self.elevenlabs_client.text_to_voice.create_previews(
                voice_description=description,
                text=(
                    "This is a preview of my voice. I am the character you are designing. "
                    "Listen closely to how I speak — this is how I will sound in the scene. "
                    "My voice should reflect my personality, tone, and emotion clearly."
                )
            )
            
            generated_voice_id = previews.previews[0].generated_voice_id

            voice = self.elevenlabs_client.text_to_voice.create_voice_from_preview(
                voice_name=name,
                voice_description=description,
                generated_voice_id=generated_voice_id
            )

            self.voice_cache[description] = voice.voice_id
            logger.info(f"✅ Voice created: {voice.voice_id}")
            return voice.voice_id

        except Exception as e:
            logger.error(f"❌ Error generating voice: {e}")
            return None

    def _generate_audio_with_elevenlabs(self, text: str, voice_id: str, output_path: str) -> Optional[str]:
        """Generate audio using ElevenLabs API"""
        
        if not self.elevenlabs_key:
            logger.error("ElevenLabs API key not available")
            return None
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {
            "xi-api-key": self.elevenlabs_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code != 200:
                logger.error(f"❌ Error generating audio: {response.status_code} {response.text}")
                return None

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"🔊 Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating audio with ElevenLabs: {str(e)}")
            return None

    def _get_fallback_voice_id(self, traits: Dict) -> str:
        """Get a default ElevenLabs voice ID based on traits"""
        default_voices = {
            "male": "pNInz6obpgDQGcFmaJgB",  # Adam
            "female": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "neutral": "21m00Tcm4TlvDq8ikWAM"  # Rachel
        }
        gender = traits.get("gender", "neutral").lower()
        return default_voices.get(gender, default_voices["neutral"])

    def _create_mp3_file(self, text: str, character: str, block_id: str, audio_dir: str, audio_filename: str) -> str:
        """Create MP3 file with proper naming when APIs are not available"""
        
        # Create the full path for the MP3 file
        audio_path = os.path.join(audio_dir, audio_filename)
        
        # Create a minimal MP3 header (silent MP3 file)
        # This creates a valid but silent MP3 file that can be played
        mp3_header = bytes([
            0xFF, 0xFB, 0x90, 0x00,  # MP3 sync word and header
            0x00, 0x00, 0x00, 0x00,  # Additional header data
            0x00, 0x00, 0x00, 0x00,  # More header data
            0x00, 0x00, 0x00, 0x00   # Frame data
        ])
        
        # Write the MP3 file
        os.makedirs(audio_dir, exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(mp3_header)
            # Add some padding to make it a valid duration
            f.write(b'\x00' * 1024)  # 1KB of silence
        
        # Also create a metadata file for reference
        metadata_path = audio_path.replace('.mp3', '_metadata.txt')
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(f"Character: {character}\n")
            f.write(f"Text: {text}\n")
            f.write(f"Block ID: {block_id}\n")
            f.write(f"Audio File: {audio_filename}\n")
        
        logger.info(f"Created MP3 file: {audio_path}")
        return audio_path
    
    def get_audio_duration(self, audio_file: str) -> float:
        """Get the duration of an audio file in seconds"""
        try:
            # Estimate duration based on text length for metadata files
            metadata_file = audio_file.replace('.mp3', '_metadata.txt')
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract text line
                    for line in content.split('\n'):
                        if line.startswith('Text: '):
                            text = line[6:]  # Remove "Text: " prefix
                            word_count = len(text.split())
                            # Estimate duration: ~150 words per minute + some padding
                            duration = (word_count / 150) * 60 + 1.0
                            return max(duration, 2.0)  # Minimum 2 seconds
            
            # For MP3 files, return a default duration
            # In a real implementation, you would use a library like librosa or pydub
            return 3.0
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 3.0  # Default duration

    def regenerate_voice(self, block_id: str, script_block: Dict, project_dir: Optional[str] = None) -> Optional[str]:
        """Regenerate voice for a specific dialogue block"""
        
        character = script_block.get("character", "Unknown")
        text = script_block.get("text", "")
        traits = script_block.get("traits", {})
        emotion = script_block.get("emotion", "neutral")
        
        # Clear cache for this character
        if character in self.voice_cache:
            del self.voice_cache[character]
        
        # Determine output directory
        if project_dir:
            audio_dir = os.path.join(project_dir, "audio")
        else:
            audio_dir = "audio"
        os.makedirs(audio_dir, exist_ok=True)
        
        # Create consistent audio filename
        audio_filename = f"{character}_{block_id}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        
        # Create new voice and generate audio
        character_voice_map: Dict[str, str] = {}
        voice_id = self._get_or_create_voice_for_character(
            character, traits, emotion, character_voice_map
        )
        
        if voice_id:
            generated_audio = self._generate_audio_with_elevenlabs(text, voice_id, audio_path)
            if generated_audio:
                return generated_audio
            else:
                # Fallback to MP3 file creation
                return self._create_mp3_file(text, character, block_id, audio_dir, audio_filename)
        else:
            # Create MP3 file with proper naming
            return self._create_mp3_file(text, character, block_id, audio_dir, audio_filename)

    def delete_all_custom_voices(self):
        """Delete all custom voices from ElevenLabs (cleanup utility)"""
        if not self.elevenlabs_client:
            logger.warning("ElevenLabs client not available")
            return
        
        try:
            voices = self.elevenlabs_client.voices.get_all()
            for voice in voices.voices:
                if voice.category != "premade":  # only delete custom voices
                    logger.info(f"🗑️ Deleting voice: {voice.name} ({voice.voice_id})")
                    self.elevenlabs_client.voices.delete(voice_id=voice.voice_id)
            
            if not voices.voices:
                logger.info("No custom voices to delete")
            else:
                logger.info(f"Deleted {len(voices.voices)} custom voices")
                self.voice_cache.clear()
            
        except Exception as e:
            logger.error(f"Error deleting custom voices: {str(e)}")
