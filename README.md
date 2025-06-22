# ∞-V (Infiniti-V) - AI-Powered Animated Video Generator

A generative AI tool that transforms single-sentence prompts into 2-3 minute animated video scenes.

## Team
- Sidharth Anand
- Rohan Shah  
- Yash Pradhan

**Event:** Hack Berkeley 2025  
**Tracks:** Creative, AI, Voice, Multimodal

## Overview

∞-V follows a structured pipeline:
1. **Input Processing** - User prompt + optional reference materials
2. **Script Generation** - Gemini API creates structured scripts with characters, dialogue, and actions
3. **Voice Synthesis** - Vapi generates character-specific speech
4. **Scene Rendering** - Ren'Py engine creates playable 2D visual novel scenes

## Architecture

```
Prompt + Uploads → Gemini + Unify → Structured Script → Vapi Voice Generation → Scene Renderer → Output
```

## Key Features

- Prompt-to-script generation using Gemini
- Character-specific voice synthesis using Vapi
- Scene rendering via Ren'Py engine
- React frontend with Flask backend
- Multimodal reference support

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`

3. Run the Flask backend:
```bash
python app.py
```

4. Start the React frontend:
```bash
cd frontend && npm start
```

## Example Use Case

**Prompt:** "A science teacher explains gravity to two students in a treehouse."
- Gemini generates scene with dialogue and actions
- Vapi creates character voices
- Ren'Py renders interactive educational animation

## MVP Goals

- [x] Project structure setup
- [ ] User prompt input
- [ ] Script generation preview
- [ ] Voice synthesis playback
- [ ] Rendered scene output
- [ ] Working React UI
