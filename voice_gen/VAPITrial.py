import os
import json
import requests
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# === Load API Key ===
load_dotenv()
ELEVENLABS_API_KEY = "sk_68a0d8efe2a675a3b100a4ec944bc8abc9bccd338cb5f3e1" 
elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)
SCRIPT_PATH = "sample.json"

VOICE_CACHE = {}

# === Step 1: Delete All Custom Voices ===
def delete_all_custom_voices():
    voices = elevenlabs.voices.get_all()
    for voice in voices.voices:
        if voice.category != "premade":  # only delete custom voices
            print(f"🗑️ Deleting voice: {voice.name} ({voice.voice_id})")
            elevenlabs.voices.delete(voice_id=voice.voice_id)

# Call this first
delete_all_custom_voices()


# === Step 2: Voice Description Builder ===
def build_voice_description(traits, emotion=None):
    parts = []
    if traits.get("age_range"): parts.append(traits["age_range"])
    if traits.get("gender"): parts.append(traits["gender"])
    if traits.get("voice_style"): parts.append(traits["voice_style"])
    if traits.get("accent"): parts.append(f"{traits['accent']} accent")
    if emotion: parts.append(f"{emotion} tone")
    return "A " + ", ".join(parts) + " voice."


# === Step 3: Create Voice (One Per Character) ===
def create_voice_from_description(description, name="Unnamed"):
    if description in VOICE_CACHE:
        return VOICE_CACHE[description]

    try:
        print(f"🎙️ Generating voice for: {description}")
        previews = elevenlabs.text_to_voice.create_previews(
            voice_description=description,
            text=(
                "This is a preview of my voice. I am the character you are designing. "
                "Listen closely to how I speak — this is how I will sound in the scene. "
                "My voice should reflect my personality, tone, and emotion clearly."
            )
        )
        generated_voice_id = previews.previews[0].generated_voice_id

        voice = elevenlabs.text_to_voice.create_voice_from_preview(
            voice_name=name,
            voice_description=description,
            generated_voice_id=generated_voice_id
        )

        VOICE_CACHE[description] = voice.voice_id
        print(f"✅ Voice created: {voice.voice_id}")
        return voice.voice_id

    except Exception as e:
        print(f"❌ Error generating voice: {e}")
        return None


# === Step 4: Audio Generation ===
def generate_audio(text, voice_id, output_path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
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

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"❌ Error generating audio: {response.status_code} {response.text}")
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"🔊 Audio saved to: {output_path}")
    return output_path


# === Step 5: JSON Helpers ===
def load_script(path):
    with open(path, "r") as f:
        return json.load(f)

def save_script(script, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)
    print(f"💾 Script saved to: {path}")


# === Step 6: Main Logic ===
def process_script(script_path):
    script = load_script(script_path)
    CHARACTER_VOICE_MAP = {}  # Use only in-memory mapping, do not persist to file

    for block in script:
        if block.get("type") != "dialogue":
            continue

        char_name = block.get("character", "Unknown")
        traits = block.get("traits", {})
        emotion = block.get("emotion", "")
        text = block.get("text", "")
        block_id = block.get("id", f"{char_name}_{len(CHARACTER_VOICE_MAP)}")

        # Always check if audio exists first
        audio_path = f"audio/{char_name}_{block_id}.mp3"
        if os.path.exists(audio_path):
            block["audio"] = audio_path
            continue

        # If audio does not exist, ensure we have a voice_id
        voice_id = traits.get("elevenlabs_voice_id")
        if not voice_id:
            voice_id = CHARACTER_VOICE_MAP.get(char_name)
        if not voice_id:
            voice_desc = build_voice_description(traits, emotion)
            voice_id = create_voice_from_description(voice_desc, name=char_name)
            if voice_id:
                CHARACTER_VOICE_MAP[char_name] = voice_id
        if voice_id:
            traits["elevenlabs_voice_id"] = voice_id
            block["traits"] = traits
        else:
            print(f"⚠️ Skipping block {block_id}, no voice available.")
            continue

        # Generate audio
        generate_audio(text, voice_id, audio_path)
        block["audio"] = audio_path

    save_script(script, script_path)


# === Entry Point ===
if __name__ == "__main__":
    # Uncomment the next line to delete all custom voices before generating audio
    # delete_all_custom_voices()
    SCRIPT_PATH = "sample.json"  # Update if needed
    process_script(SCRIPT_PATH)
