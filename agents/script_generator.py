import os
import json
from pprint import pprint
import logging
from typing import List, Dict, Optional
from datetime import datetime
from .prompts.script_generator_prompts import (
    INTERPRET_PROMPT_SYSTEM,
    DIALOGUE_GENERATION_SYSTEM,
    ACTION_GENERATION_SYSTEM
)


# Try to import AI libraries
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

STORY_MODEL = "llama-3.1-8b-instant"
GOOGLE_MODEL = "gemma-3-4b-it"


class ScriptGenerator:
    """Agent pipeline for generating structured scripts from prompts"""
    
    def __init__(self):
        
        # Initialize Groq client if available
        if GROQ_AVAILABLE:
            groq_key = os.getenv('GROQ_API_KEY')
            if groq_key:
                try:
                    # Initialize Groq with minimal parameters to avoid version issues
                    self.groq_client = Groq(api_key=groq_key)
                    logger.info("Groq client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Groq client: {str(e)}")
                    self.groq_client = None
            else:
                logger.warning("GROQ_API_KEY not found in environment variables")
        
        if GEMINI_AVAILABLE:
            gemini_key = os.getenv('GEMINI_API_KEY')
           
            if gemini_key and gemini_key != 'your_gemini_api_key_here':
                try:
                    genai.configure(api_key=gemini_key)
                    self.gemini_model = genai.GenerativeModel(GOOGLE_MODEL)
                    logger.info("Gemini model initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini: {str(e)}")
                    self.gemini_model = None
            else:
                logger.warning("GEMINI_API_KEY not configured")
        self.groq_client = None
        
        if not (GROQ_AVAILABLE or GEMINI_AVAILABLE):
            logger.warning("No AI APIs configured, will use fallback script generation")

    def generate_script(self, prompt: str, reference_materials: List[Dict] = None, project_dir: str = None) -> List[Dict]:
        """
        Generate a structured script using the agent pipeline
        """
        try:
            logger.info(f"Starting script generation for: {prompt}")
            
            # Step 1: Interpret the prompt
            scene_plan = self._interpret_prompt(prompt, reference_materials)

            
            # Step 2: Generate dialogue
            dialogue = self._generate_dialogue(scene_plan)
             
            # Step 3: Generate actions
            actions = self._generate_actions(scene_plan, dialogue)
        
            
            # Step 4: Structure as JSON
            structured_script = self._structure_as_json(dialogue, actions, scene_plan)
            
            # Save to project directory if provided
            if project_dir:
                self._save_script_files(structured_script, scene_plan, project_dir)
            
            logger.info(f"Script generation completed. Generated {len(structured_script)} blocks.")
            return structured_script
            
        except Exception as e:
            logger.error(f"Error in script generation: {str(e)}")
            return self._create_fallback_script(prompt)
    
    def _save_script_files(self, script: List[Dict], scene_plan: Dict, project_dir: str):
        """Save script and scene plan to project directory"""
        try:
            scripts_dir = os.path.join(project_dir, "scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            
            # Save scene plan
            scene_plan_path = os.path.join(scripts_dir, "scene_plan.json")
            with open(scene_plan_path, 'w', encoding='utf-8') as f:
                json.dump(scene_plan, f, indent=2, ensure_ascii=False)
            
            # Save detailed script analysis
            script_analysis = {
                "total_blocks": len(script),
                "dialogue_blocks": len([b for b in script if b.get('type') == 'dialogue']),
                "action_blocks": len([b for b in script if b.get('type') == 'action']),
                "characters": list(set([b.get('character') for b in script if b.get('character')]))
            }
            
            analysis_path = os.path.join(scripts_dir, "script_analysis.json")
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(script_analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Script files saved to {scripts_dir}")
            
        except Exception as e:
            logger.error(f"Error saving script files: {str(e)}")
    
    def _interpret_prompt(self, prompt: str, reference_materials: List[Dict] = None) -> Dict:
        """Interpret the user prompt and create a scene plan"""
        
        if self.groq_client or self.gemini_model:
            system_prompt = INTERPRET_PROMPT_SYSTEM
            
            user_prompt = f"Prompt: {prompt}"
            if reference_materials:
                user_prompt += f"\nReference materials: {json.dumps(reference_materials, indent=2)}"
            
            try:
                if self.groq_client:
                    response = self.groq_client.chat.completions.create(
                        model=STORY_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )

                    result = response.choices[0].message.content
                elif self.gemini_model:
                    response = self.gemini_model.generate_content(f"{system_prompt}\n\n{user_prompt}")
                    result = response.text
                
                try:
                    # pprint(json.loads(result))  # Pretty print the JSON for debugging
                    pprint(json.loads(result))  # Pretty print the JSON for debugging
                    return json.loads(result)
                except:
                    # If JSON parsing fails, create a structured response
                    return {
                        "setting": "Unknown location",
                        "characters": ["Character A", "Character B"],
                        "conflict": result[:200] + "..." if len(result) > 200 else result,
                        "tone": "neutral",
                        "events": ["Scene begins", "Characters interact", "Scene concludes"]
                    }
                    
            except Exception as e:
                logger.error(f"Error in prompt interpretation: {str(e)}")
        
        # Fallback interpretation
        return {
            "setting": "A generic location",
            "characters": ["Speaker", "Listener"],
            "conflict": prompt,
            "tone": "conversational",
            "events": ["Introduction", "Main discussion", "Conclusion"]
        }
    
    def _generate_dialogue(self, scene_plan: Dict) -> List[Dict]:
        """Generate dialogue based on the scene plan"""
        if self.groq_client or self.gemini_model:
            system_prompt = DIALOGUE_GENERATION_SYSTEM
        
        user_prompt = f"Scene plan: {json.dumps(scene_plan, indent=2)}"
        try:
            if self.groq_client:
                response = self.groq_client.chat.completions.create(
                    model=STORY_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8,
                    max_tokens=1500
                )
                result = response.choices[0].message.content
            elif self.gemini_model:
                response = self.gemini_model.generate_content(f"{system_prompt}\n\n{user_prompt}")
                result = response.text
            
            # Debug: Print the raw result
            print("=== RAW DIALOGUE GENERATION RESULT ===")
            print(f"Result type: {type(result)}")
            print(f"Result length: {len(result) if result else 0}")
            print(f"First 200 chars: {result[:200] if result else 'None'}")
            print("=====================================")
            
            # Check if result is empty or None
            if not result or result.strip() == "":
                logger.error("Empty response from AI service for dialogue generation")
                return self._create_fallback_dialogue(scene_plan)
        
            try:
                # Try to parse JSON directly first
                parsed_result = json.loads(result)
                pprint(parsed_result)
                return parsed_result
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed for dialogue: {str(e)}")
                logger.error(f"Raw result that failed to parse: {repr(result[:500])}")
                
                # Try to extract JSON from markdown code blocks
                if "```json" in result:
                    try:
                        json_start = result.find("```json") + 7
                        json_end = result.find("```", json_start)
                        if json_end > json_start:
                            json_content = result[json_start:json_end].strip()
                            print(f"Extracted JSON: {json_content[:200]}...")
                            parsed_result = json.loads(json_content)
                            pprint(parsed_result)
                            return parsed_result
                    except Exception as extract_error:
                        logger.error(f"Failed to extract JSON from markdown: {str(extract_error)}")
                
                # If all parsing fails, create fallback
                return self._create_fallback_dialogue(scene_plan)
                
        except Exception as e:
            logger.error(f"Error in dialogue generation: {str(e)}")
        
        # Fallback dialogue
        characters = scene_plan.get("characters", ["Character A", "Character B"])
        return [
            {
                "id": "1",
                "type": "dialogue",
                "character": characters[0],
                "text": f"Hello! Let me tell you about {scene_plan.get('conflict', 'our situation')}.",
                "emotion": "friendly",
                "traits": {"gender": "neutral", "age": "adult", "style": "conversational"}
            },
            {
                "id": "2",
                "type": "dialogue",
                "character": characters[1] if len(characters) > 1 else "Listener",
                "text": "That's interesting! Tell me more.",
                "emotion": "curious",
                "traits": {"gender": "neutral", "age": "adult", "style": "conversational"}
            }
        ]
    
    def _generate_actions(self, scene_plan: Dict, dialogue: List[Dict]) -> List[Dict]:
        """Generate actions and visual descriptions"""
        
        if self.groq_client or self.gemini_model:
            system_prompt = ACTION_GENERATION_SYSTEM
            
            user_prompt = f"""
            Scene plan: {json.dumps(scene_plan, indent=2)}
            
            Dialogue: {json.dumps(dialogue, indent=2)}
            
            Generate appropriate actions and visual elements for this scene.
            """
            
            try:
                if self.groq_client:
                    response = self.groq_client.chat.completions.create(
                        model=STORY_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1500
                    )
                    result = response.choices[0].message.content
                elif self.gemini_model:
                    response = self.gemini_model.generate_content(f"{system_prompt}\n\n{user_prompt}")
                    result = response.text
                  # Debug: Print the raw result
                print("=== RAW ACTION GENERATION RESULT ===")
                print(f"Result type: {type(result)}")
                print(f"Result length: {len(result) if result else 0}")
                print(f"First 200 chars: {result[:200] if result else 'None'}")
                print("=====================================")
                
                # Check if result is empty or None
                if not result or result.strip() == "":
                    logger.error("Empty response from AI service for action generation")
                    return self._create_fallback_actions(scene_plan)
                
                try:
                    # Try to parse JSON directly first
                    parsed_result = json.loads(result)
                    pprint(parsed_result)
                    return parsed_result
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed for actions: {str(e)}")
                    logger.error(f"Raw result that failed to parse: {repr(result[:500])}")
                    
                    # Try to extract JSON from markdown code blocks
                    if "```json" in result:
                        try:
                            json_start = result.find("```json") + 7
                            json_end = result.find("```", json_start)
                            if json_end > json_start:
                                json_content = result[json_start:json_end].strip()
                                print(f"Extracted JSON from actions: {json_content[:200]}...")
                                parsed_result = json.loads(json_content)
                                pprint(parsed_result)
                                return parsed_result
                        except Exception as extract_error:
                            logger.error(f"Failed to extract JSON from markdown in actions: {str(extract_error)}")
                    
                    # If all parsing fails, create fallback
                    return self._create_fallback_actions(scene_plan)
                    
            except Exception as e:
                logger.error(f"Error in action generation: {str(e)}")
        
        # Fallback actions
        return [
            {"id": "action_1", "type": "action", "description": f"Scene opens in {scene_plan.get('setting', 'a location')}"},
            {"id": "action_2", "type": "action", "description": "Characters begin their interaction"},
            {"id": "action_3", "type": "action", "description": f"The atmosphere is {scene_plan.get('tone', 'neutral')}"}
        ]
    
    def _structure_as_json(self, dialogue: List[Dict], actions: List[Dict], scene_plan: Dict) -> List[Dict]:
        """Structure everything into the final JSON format for the pipeline"""
        
        structured_script = []
        dialogue_index = 0
        action_index = 0
        
        # Start with scene setting
        structured_script.append({
            "id": "scene_start",
            "type": "scene",
            "setting": scene_plan.get("setting", "Unknown location"),
            "description": f"Scene begins in {scene_plan.get('setting', 'a location')} with a {scene_plan.get('tone', 'neutral')} atmosphere."
        })
        
        # Interleave dialogue and actions
        max_items = max(len(dialogue), len(actions))
        
        for i in range(max_items * 2):
            # Add action first (if available)
            if action_index < len(actions) and i % 2 == 0:
                structured_script.append(actions[action_index])
                action_index += 1
            
            # Add dialogue (if available)
            if dialogue_index < len(dialogue):
                structured_script.append(dialogue[dialogue_index])
                dialogue_index += 1
        
        # Add any remaining items
        while action_index < len(actions):
            structured_script.append(actions[action_index])
            action_index += 1
        
        while dialogue_index < len(dialogue):
            structured_script.append(dialogue[dialogue_index])
            dialogue_index += 1
        
        # Ensure all items have unique IDs
        for i, block in enumerate(structured_script):
            if not block.get('id'):
                block['id'] = f"block_{i}"
        
        return structured_script
    
    def _create_fallback_script(self, prompt: str) -> List[Dict]:
        """Create a basic fallback script when AI services are unavailable"""
        return [
            {
                "id": "1",
                "type": "scene",
                "setting": "Generic location",
                "description": "A scene begins to unfold."
            },
            {
                "id": "2",
                "type": "dialogue",
                "character": "Narrator",
                "text": f"Welcome to this scene about: {prompt}",
                "emotion": "neutral",
                "traits": {"gender": "neutral", "age": "adult", "style": "conversational"}
            },
            {
                "id": "3",
                "type": "action",
                "description": "The scene continues as planned."
            },
            {
                "id": "4",
                "type": "dialogue",
                "character": "Narrator",
                "text": "This concludes our generated scene.",
                "emotion": "conclusive",
                "traits": {"gender": "neutral", "age": "adult", "style": "conversational"}
            }
        ]
    
    def _create_fallback_dialogue(self, scene_plan: Dict) -> List[Dict]:
        """Create fallback dialogue structure when AI parsing fails"""
        characters = scene_plan.get("characters", ["Character A", "Character B"])
        return [
            {
                "id": "1",
                "type": "dialogue",
                "character": characters[0],
                "text": f"Hello! Let me tell you about {scene_plan.get('conflict', 'our situation')}.",
                "emotion": "friendly",
                "traits": {"gender": "neutral", "age": "adult", "style": "conversational"}
            },
            {
                "id": "2",
                "type": "dialogue",
                "character": characters[1] if len(characters) > 1 else "Listener",
                "text": "That's interesting! Tell me more.",
                "emotion": "curious",
                "traits": {"gender": "neutral", "age": "adult", "style": "conversational"}
            }
        ]
    
    def _create_fallback_actions(self, scene_plan: Dict) -> List[Dict]:
        """Create fallback actions when AI parsing fails"""
        return [
            {"id": "action_1", "type": "action", "description": f"Scene opens in {scene_plan.get('setting', 'a location')}"},
            {"id": "action_2", "type": "action", "description": "Characters begin their interaction"},
            {"id": "action_3", "type": "action", "description": f"The atmosphere is {scene_plan.get('tone', 'neutral')}"}
        ]
