import os
import json
import requests
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# === Load API Key ===
load_dotenv()
ELEVENLABS_API_KEY = "sk_68a0d8efe2a675a3b100a4ec944bc8abc9bccd338cb5f3e1"
elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

VOICE_CACHE = {}

def build_voice_description(traits, emotion=None):
    parts = []
    if traits.get("age"): parts.append(traits["age"])
    if traits.get("gender"): parts.append(traits["gender"])
    if traits.get("style"): parts.append(traits["style"])
    if traits.get("accent"): parts.append(f"{traits['accent']} accent")
    if emotion: parts.append(f"{emotion} tone")
    return "A " + ", ".join(parts) + " voice."

def create_voice_from_description(description, name="Unnamed"):
    if description in VOICE_CACHE:
        return VOICE_CACHE[description]

    try:
        print(f" Generating voice for: {description}")
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

def load_script(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_script(script, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2)
    print(f"💾 Script saved to: {path}")

def process_script(script_path):
    script = load_script(script_path)

    for block in script:
        if block.get("type") != "dialogue":
            continue

        char_name = block.get("character", "Unknown")
        traits = block.get("traits", {})
        emotion = block.get("emotion", "")
        text = block.get("text", "")
        block_id = block.get("id", f"{char_name}_{len(VOICE_CACHE)}")

        voice_desc = build_voice_description(traits, emotion)
        voice_id = create_voice_from_description(voice_desc, name=char_name)

        if not voice_id:
            continue

        audio_path = f"audio/{block_id}.mp3"
        generate_audio(text, voice_id, audio_path)

        block["traits"]["elevenlabs_voice_id"] = voice_id
        block["audio"] = audio_path

    save_script(script, script_path)

if __name__ == "__main__":
    SCRIPT_PATH = "sample.json"  # Change if needed
    process_script(SCRIPT_PATH)
