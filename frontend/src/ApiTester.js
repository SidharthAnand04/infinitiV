
import React, { useState } from 'react';
import axios from 'axios';

// Configure axios base URL to point to your Python backend
const api = axios.create({
  baseURL: 'http://localhost:8080'
});

function ApiTester() {
  const [activeTab, setActiveTab] = useState('health');
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState({});
  const [formData, setFormData] = useState({
    prompt: 'A detective interviews a suspect in a dark room',
    script: [],
    audio_files: {},
    project_folder: ''
  });

  const handleApiCall = async (endpoint, method = 'GET', data = null) => {
    const requestKey = `${method}-${endpoint}`;
    setLoading(prev => ({ ...prev, [requestKey]: true }));
    
    try {
      const config = {
        method: method.toLowerCase(),
        url: endpoint,
      };
      
      if (data) {
        config.data = data;
      }
      
      const response = await api(config);
      setResults(prev => ({ 
        ...prev, 
        [requestKey]: {
          status: response.status,
          data: response.data,
          success: true
        }
      }));
    } catch (error) {
      setResults(prev => ({ 
        ...prev, 
        [requestKey]: {
          status: error.response?.status || 500,
          data: error.response?.data || { error: error.message },
          success: false
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [requestKey]: false }));
    }
  };

  const renderResult = (result) => {
    if (!result) return null;
    
    return (
      <div className={`api-result ${result.success ? 'success' : 'error'}`}>
        <div className="result-header">
          <span className={`status-code ${result.success ? 'success' : 'error'}`}>
            Status: {result.status}
          </span>
          <span className={`result-type ${result.success ? 'success' : 'error'}`}>
            {result.success ? 'SUCCESS' : 'ERROR'}
          </span>
        </div>
        <pre className="result-body">
          {JSON.stringify(result.data, null, 2)}
        </pre>
      </div>
    );
  };

  const testEndpoints = [
    {
      id: 'health',
      name: 'Health Check',
      endpoint: '/',
      method: 'GET',
      description: 'Test if the API is running'
    },
    {
      id: 'list-projects',
      name: 'List Projects',
      endpoint: '/api/list-projects',
      method: 'GET',
      description: 'Get all generated projects'
    },
    {
      id: 'generate-script',
      name: 'Generate Script',
      endpoint: '/api/generate-script',
      method: 'POST',
      description: 'Generate a script from a prompt',
      requiresData: ['prompt']
    },
    {
      id: 'generate-voice',
      name: 'Generate Voice',
      endpoint: '/api/generate-voice',
      method: 'POST',
      description: 'Generate voice audio from script',
      requiresData: ['script', 'project_folder']
    },
    {
      id: 'render-scene',
      name: 'Render Scene',
      endpoint: '/api/render-scene',
      method: 'POST',
      description: 'Render scene with Ren\'Py',
      requiresData: ['script', 'audio_files', 'project_folder']
    },
    {
      id: 'generate-full-scene',
      name: 'Full Pipeline',
      endpoint: '/api/generate-full-scene',
      method: 'POST',
      description: 'Complete pipeline: prompt → script → voice → scene',
      requiresData: ['prompt']
    }
  ];

  return (
    <div className="api-tester">
      <h2>🔧 API Endpoint Tester</h2>
      <p>Test individual API endpoints to debug your backend</p>

      <div className="tabs">
        {testEndpoints.map(endpoint => (
          <button
            key={endpoint.id}
            className={`tab ${activeTab === endpoint.id ? 'active' : ''}`}
            onClick={() => setActiveTab(endpoint.id)}
          >
            {endpoint.name}
          </button>
        ))}
      </div>

      {testEndpoints.map(endpoint => (
        <div
          key={endpoint.id}
          className={`tab-content ${activeTab === endpoint.id ? 'active' : ''}`}
        >
          <div className="endpoint-info">
            <h3>{endpoint.name}</h3>
            <p>{endpoint.description}</p>
            <div className="endpoint-details">
              <span className={`method ${endpoint.method.toLowerCase()}`}>
                {endpoint.method}
              </span>
              <code>{endpoint.endpoint}</code>
            </div>
          </div>

          {endpoint.requiresData && (
            <div className="form-section">
              <h4>Request Data:</h4>
              
              {endpoint.requiresData.includes('prompt') && (
                <div className="input-group">
                  <label htmlFor="prompt">Prompt:</label>
                  <textarea
                    id="prompt"
                    value={formData.prompt}
                    onChange={(e) => setFormData(prev => ({ ...prev, prompt: e.target.value }))}
                    rows={3}
                    placeholder="Enter your scene prompt..."
                  />
                </div>
              )}

              {endpoint.requiresData.includes('script') && (
                <div className="input-group">
                  <label htmlFor="script">Script (JSON):</label>
                  <textarea
                    id="script"
                    value={JSON.stringify(formData.script, null, 2)}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value);
                        setFormData(prev => ({ ...prev, script: parsed }));
                      } catch (err) {
                        // Invalid JSON, but allow editing
                      }
                    }}
                    rows={8}
                    placeholder="Enter script JSON..."
                  />
                  <small>Sample script structure: {`[{"type": "dialogue", "character": "Detective", "text": "Hello", "emotion": "neutral"}]`}</small>
                </div>
              )}

              {endpoint.requiresData.includes('audio_files') && (
                <div className="input-group">
                  <label htmlFor="audio_files">Audio Files (JSON):</label>
                  <textarea
                    id="audio_files"
                    value={JSON.stringify(formData.audio_files, null, 2)}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value);
                        setFormData(prev => ({ ...prev, audio_files: parsed }));
                      } catch (err) {
                        // Invalid JSON
                      }
                    }}
                    rows={4}
                    placeholder="Enter audio files JSON..."
                  />
                  <small>Sample: {`{"block_1": "path/to/audio1.wav", "block_2": "path/to/audio2.wav"}`}</small>
                </div>
              )}

              {endpoint.requiresData.includes('project_folder') && (
                <div className="input-group">
                  <label htmlFor="project_folder">Project Folder:</label>
                  <input
                    id="project_folder"
                    type="text"
                    value={formData.project_folder}
                    onChange={(e) => setFormData(prev => ({ ...prev, project_folder: e.target.value }))}
                    placeholder="Leave empty to auto-generate"
                  />
                </div>
              )}
            </div>
          )}

          <div className="test-section">
            <button
              className="test-button"
              onClick={() => {
                const data = endpoint.requiresData ? 
                  Object.fromEntries(
                    endpoint.requiresData.map(key => [key, formData[key]])
                  ) : null;
                handleApiCall(endpoint.endpoint, endpoint.method, data);
              }}
              disabled={loading[`${endpoint.method}-${endpoint.endpoint}`]}
            >
              {loading[`${endpoint.method}-${endpoint.endpoint}`] ? 'Testing...' : `Test ${endpoint.name}`}
            </button>
          </div>

          {renderResult(results[`${endpoint.method}-${endpoint.endpoint}`])}
        </div>
      ))}
    </div>
  );
}

export default ApiTester;
