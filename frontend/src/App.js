import React, { useState } from 'react';
import axios from 'axios';
import ApiTester from './ApiTester';
import './index.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [currentStep, setCurrentStep] = useState('');
  const [activeView, setActiveView] = useState('main'); // 'main' or 'tester'

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    setCurrentStep('Generating script...');

    try {
      // Call the full pipeline endpoint
      const response = await axios.post('/api/generate-full-scene', {
        prompt: prompt.trim(),
        references: []
      });

      if (response.data.success) {
        setResult(response.data);
        setCurrentStep('Complete!');
      } else {
        setError('Failed to generate scene');
      }
    } catch (err) {
      console.error('Error:', err);
      setError(err.response?.data?.error || 'An error occurred while generating the scene');
    } finally {
      setLoading(false);
    }
  };

  const renderScriptPreview = (script) => {
    if (!script || !Array.isArray(script)) return null;

    return (
      <div className="script-preview">
        <h3>Generated Script</h3>
        {script.map((block, index) => (
          <div key={block.id || index} className={`script-block ${block.type}`}>
            {block.type === 'dialogue' ? (
              <>
                <div className="character-name">
                  {block.character} ({block.emotion})
                </div>
                <div className="dialogue-text">"{block.text}"</div>
                {block.traits && (
                  <div style={{ fontSize: '0.8em', color: '#666', marginTop: '5px' }}>
                    Traits: {JSON.stringify(block.traits)}
                  </div>
                )}
              </>
            ) : (
              <div className="action-description">
                Action: {block.description}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderAudioFiles = (audioFiles) => {
    if (!audioFiles || Object.keys(audioFiles).length === 0) return null;

    return (
      <div className="card">
        <h3>Generated Audio</h3>
        <div>
          {Object.entries(audioFiles).map(([blockId, audioFile]) => (
            <div key={blockId} style={{ margin: '10px 0', padding: '10px', background: '#f5f5f5', borderRadius: '5px' }}>
              <strong>Block {blockId}:</strong> {audioFile}
              {audioFile.endsWith('.txt') && (
                <span style={{ color: '#666', fontSize: '0.9em' }}> (Simulated)</span>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderSceneOutput = (sceneOutput) => {
    if (!sceneOutput) return null;

    return (
      <div className="card">
        <h3>Scene Output</h3>
        <div style={{ padding: '15px', background: '#f9f9f9', borderRadius: '5px' }}>
          <p><strong>Type:</strong> {sceneOutput.type}</p>
          <p><strong>Status:</strong> {sceneOutput.status || 'Generated'}</p>
          
          {sceneOutput.preview_url && (
            <div style={{ margin: '15px 0' }}>
              <a 
                href={sceneOutput.preview_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="button"
                style={{ textDecoration: 'none' }}
              >
                View Scene Preview
              </a>
            </div>
          )}
          
          {sceneOutput.project_path && (
            <p><strong>Project Path:</strong> {sceneOutput.project_path}</p>
          )}
          
          {sceneOutput.message && (
            <p style={{ color: '#666', fontStyle: 'italic' }}>{sceneOutput.message}</p>
          )}
        </div>
      </div>
    );
  };
  return (
    <div className="container">
      <div className="header">
        <h1>∞-V</h1>
        <p>AI-Powered Animated Video Generator</p>
        <p style={{ fontSize: '1rem', color: '#888' }}>
          Turn your ideas into 2-3 minute animated scenes
        </p>
        
        {/* Navigation */}
        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeView === 'main' ? 'active' : ''}`}
            onClick={() => setActiveView('main')}
          >
            🎬 Generate Scene
          </button>
          <button
            className={`nav-tab ${activeView === 'tester' ? 'active' : ''}`}
            onClick={() => setActiveView('tester')}
          >
            🔧 API Tester
          </button>
        </div>
      </div>

      {activeView === 'main' ? (
        <>
          <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="prompt">
              Enter your scene prompt:
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., A science teacher explains gravity to two students in a treehouse"
              rows={4}
              disabled={loading}
            />
          </div>
          
          <button 
            type="submit" 
            className="button" 
            disabled={loading || !prompt.trim()}
          >
            {loading ? 'Generating...' : 'Generate Scene'}
          </button>
        </form>

        {loading && (
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>{currentStep}</p>
            <p style={{ fontSize: '0.9em', color: '#666' }}>
              This may take a few moments...
            </p>
          </div>
        )}

        {error && (
          <div className="error">
            <strong>Error:</strong> {error}
          </div>
        )}
      </div>

      {result && (
        <div>
          <div className="success">
            <strong>Success!</strong> Your scene has been generated successfully.
          </div>

          <div className="two-column">
            <div>
              {renderScriptPreview(result.script)}
            </div>
            <div>
              {renderAudioFiles(result.audio_files)}
              {renderSceneOutput(result.scene_output)}
            </div>
          </div>
        </div>
      )}

      <div className="card" style={{ marginTop: '40px', background: 'rgba(255, 255, 255, 0.8)' }}>
        <h3>About ∞-V</h3>
        <p>
          ∞-V (Infiniti-V) is an AI-powered tool that transforms simple text prompts into 
          interactive animated scenes. Our pipeline includes:
        </p>
        <ul>
          <li><strong>Script Generation:</strong> AI creates structured dialogue and actions</li>
          <li><strong>Voice Synthesis:</strong> Character-specific speech generation</li>
          <li><strong>Scene Rendering:</strong> Visual novel-style interactive scenes</li>
        </ul>
        <p>          <em>Built for Hack Berkeley 2025 by Sidharth Anand, Rohan Shah, and Yash Pradhan</em>
        </p>
      </div>
        </>
      ) : (
        <ApiTester />
      )}
    </div>
  );
}

export default App;
