import os
import json
import logging
import requests
from typing import List, Dict, Any
import base64
import hashlib

logger = logging.getLogger(__name__)

class VoiceGenerator:
    """Voice generation agent using Vapi API"""
    
    def __init__(self):
        self.vapi_api_key = os.getenv('VAPI_API_KEY')
        self.base_url = "https://api.vapi.ai"
        self.audio_cache = {}  # Cache for generated audio files
        
        if not self.vapi_api_key or self.vapi_api_key == 'your_vapi_api_key_here':
            logger.warning("Vapi API key not configured, voice generation will be simulated")
            self.vapi_api_key = None
    
    def generate_voices(self, script: List[Dict]) -> Dict[str, str]:
        """
        Generate voice audio for all dialogue blocks in the script
        Returns a dictionary mapping dialogue IDs to audio file paths/URLs
        """
        audio_files = {}
        
        try:
            for block in script:
                if block.get("type") == "dialogue":
                    block_id = block.get("id")
                    character = block.get("character", "Unknown")
                    text = block.get("text", "")
                    traits = block.get("traits", {})
                    emotion = block.get("emotion", "neutral")
                    
                    if text.strip():
                        logger.info(f"Generating voice for block {block_id}: {character}")
                        
                        # Generate audio for this dialogue block
                        audio_file = self._generate_single_voice(
                            text=text,
                            character=character,
                            traits=traits,
                            emotion=emotion,
                            block_id=block_id
                        )
                        
                        if audio_file:
                            audio_files[block_id] = audio_file
                        
            return audio_files
            
        except Exception as e:
            logger.error(f"Error in voice generation: {str(e)}")
            return {}
    
    def _generate_single_voice(self, text: str, character: str, traits: Dict, emotion: str, block_id: str) -> str:
        """Generate voice audio for a single dialogue block"""
        
        try:
            # Create a cache key based on content
            cache_key = hashlib.md5(f"{text}_{character}_{json.dumps(traits)}_{emotion}".encode()).hexdigest()
            
            # Check cache first
            if cache_key in self.audio_cache:
                logger.info(f"Using cached audio for block {block_id}")
                return self.audio_cache[cache_key]
            
            if not self.vapi_api_key:
                # Simulate voice generation
                return self._simulate_voice_generation(text, character, block_id)
            
            # Determine voice characteristics from traits
            voice_config = self._get_voice_config(traits, emotion)
            
            # Make API call to Vapi
            audio_file = self._call_vapi_api(text, voice_config, block_id)
            
            # Cache the result
            if audio_file:
                self.audio_cache[cache_key] = audio_file
            
            return audio_file
            
        except Exception as e:
            logger.error(f"Error generating voice for block {block_id}: {str(e)}")
            return self._simulate_voice_generation(text, character, block_id)
    
    def _get_voice_config(self, traits: Dict, emotion: str) -> Dict:
        """Convert character traits and emotion to voice configuration"""
        
        # Default voice config
        voice_config = {
            "model": "eleven_labs",
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
        
        # Adjust based on traits
        gender = traits.get("gender", "neutral").lower()
        age = traits.get("age", "adult").lower()
        style = traits.get("style", "friendly").lower()
        
        # Voice selection based on traits
        if gender == "male":
            if age in ["young", "child"]:
                voice_config["voice_id"] = "pNInz6obpgDQGcFmaJgB"  # Adam - young male
            elif age == "elderly":
                voice_config["voice_id"] = "VR6AewLTigWG4xSOukaG"  # Arnold - older male
            else:
                voice_config["voice_id"] = "pNInz6obpgDQGcFmaJgB"  # Adam - default male
        elif gender == "female":
            if age in ["young", "child"]:
                voice_config["voice_id"] = "EXAVITQu4vr4xnSDxMaL"  # Bella - young female
            elif age == "elderly":
                voice_config["voice_id"] = "MF3mGyEYCl7XYWbV9V6O"  # Elli - older female
            else:
                voice_config["voice_id"] = "21m00Tcm4TlvDq8ikWAM"  # Rachel - default female
        else:
            # Neutral/default voice
            voice_config["voice_id"] = "21m00Tcm4TlvDq8ikWAM"  # Rachel
        
        # Adjust style based on emotion
        emotion_adjustments = {
            "excited": {"stability": 0.3, "style": 0.2},
            "sad": {"stability": 0.8, "style": -0.2},
            "angry": {"stability": 0.2, "style": 0.4},
            "calm": {"stability": 0.9, "style": -0.1},
            "worried": {"stability": 0.4, "style": 0.1},
            "happy": {"stability": 0.4, "style": 0.3},
            "educational": {"stability": 0.7, "style": 0.0},
            "neutral": {"stability": 0.5, "style": 0.0}
        }
        
        if emotion in emotion_adjustments:
            voice_config.update(emotion_adjustments[emotion])
        
        return voice_config
    
    def _call_vapi_api(self, text: str, voice_config: Dict, block_id: str) -> str:
        """Make actual API call to Vapi for voice synthesis"""
        
        headers = {
            "Authorization": f"Bearer {self.vapi_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "voice_settings": voice_config,
            "output_format": "mp3_44100_128"
        }
        
        try:
            # This is a placeholder for the actual Vapi API endpoint
            # You'll need to adjust this based on Vapi's actual API structure
            response = requests.post(
                f"{self.base_url}/v1/text-to-speech",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                # Save audio file
                audio_filename = f"audio/voice_{block_id}.mp3"
                os.makedirs("audio", exist_ok=True)
                
                with open(audio_filename, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Voice generated and saved: {audio_filename}")
                return audio_filename
            else:
                logger.error(f"Vapi API error: {response.status_code} - {response.text}")
                return self._simulate_voice_generation(text, "character", block_id)
                
        except Exception as e:
            logger.error(f"Error calling Vapi API: {str(e)}")
            return self._simulate_voice_generation(text, "character", block_id)
    
    def _simulate_voice_generation(self, text: str, character: str, block_id: str) -> str:
        """Simulate voice generation when API is not available"""
        
        # Create a placeholder audio file path
        audio_filename = f"audio/simulated_voice_{block_id}.mp3"
        
        # Create audio directory if it doesn't exist
        os.makedirs("audio", exist_ok=True)
        
        # For now, just create a text file with the dialogue
        # In a real implementation, you might use a local TTS library
        text_filename = f"audio/dialogue_{block_id}.txt"
        with open(text_filename, "w", encoding="utf-8") as f:
            f.write(f"Character: {character}\n")
            f.write(f"Text: {text}\n")
            f.write(f"Block ID: {block_id}\n")
        
        logger.info(f"Simulated voice generation: {text_filename}")
        return text_filename
    
    def get_audio_duration(self, audio_file: str) -> float:
        """Get the duration of an audio file in seconds"""
        try:
            # This would typically use a library like librosa or pydub
            # For now, estimate based on text length (average speaking rate: ~150 words/min)
            if audio_file.endswith('.txt'):
                with open(audio_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract text line
                    for line in content.split('\n'):
                        if line.startswith('Text: '):
                            text = line[6:]  # Remove "Text: " prefix
                            word_count = len(text.split())
                            # Estimate duration: ~150 words per minute + some padding
                            duration = (word_count / 150) * 60 + 1.0
                            return max(duration, 2.0)  # Minimum 2 seconds
            
            # Default duration for unknown files
            return 3.0
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 3.0  # Default duration
    
    def regenerate_voice(self, block_id: str, script_block: Dict) -> str:
        """Regenerate voice for a specific dialogue block"""
        
        character = script_block.get("character", "Unknown")
        text = script_block.get("text", "")
        traits = script_block.get("traits", {})
        emotion = script_block.get("emotion", "neutral")
        
        # Clear cache for this block
        cache_key = hashlib.md5(f"{text}_{character}_{json.dumps(traits)}_{emotion}".encode()).hexdigest()
        if cache_key in self.audio_cache:
            del self.audio_cache[cache_key]
        
        # Generate new voice
        return self._generate_single_voice(text, character, traits, emotion, block_id)
