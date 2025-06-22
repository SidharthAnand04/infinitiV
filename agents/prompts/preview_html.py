import json

def get_preview_html(**kwargs):
    """
    Generate a preview HTML for the script.
    This function is used to create a simple HTML representation of the script.
    """
    return f"""
<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>∞-V Scene Preview: {kwargs['project_name']}</title>
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
                    <h2>{ kwargs['project_name']}</h2>
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
                    <div class="renpy-script" id="renpyScript" style="display: none;">{kwargs['script_content']}</div>
                </div>
                
                <script>
                    // Scene data and state
                    let sceneBlocks = {json.dumps(kwargs['script_blocks'])};
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
        """