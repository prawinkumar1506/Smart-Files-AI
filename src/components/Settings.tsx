"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Key, Database, Shield, Info } from "lucide-react"

const Settings: React.FC = () => {
  const [geminiApiKey, setGeminiApiKey] = useState("")
  const [llmProvider, setLlmProvider] = useState("gemini")
  const [isEncryptionEnabled, setIsEncryptionEnabled] = useState(false)
  const [settings, setSettings] = useState({
    chunkSize: 1000,
    chunkOverlap: 200,
    similarityThreshold: 0.7,
    maxResults: 20,
  })

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = () => {
    // Load settings from localStorage or electron store
    const savedApiKey = localStorage.getItem("gemini_api_key") || ""
    const savedProvider = localStorage.getItem("llm_provider") || "gemini"
    const savedEncryption = localStorage.getItem("encryption_enabled") === "true"

    setGeminiApiKey(savedApiKey)
    setLlmProvider(savedProvider)
    setIsEncryptionEnabled(savedEncryption)
  }

  const saveSettings = () => {
    localStorage.setItem("gemini_api_key", geminiApiKey)
    localStorage.setItem("llm_provider", llmProvider)
    localStorage.setItem("encryption_enabled", isEncryptionEnabled.toString())

    alert("Settings saved successfully!")
  }

  const handleSettingChange = (key: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Configure SmartFile AI to your preferences</p>
      </div>

      <div className="settings-sections">
        <div className="settings-section">
          <div className="section-header">
            <Key size={20} />
            <h2>LLM Configuration</h2>
          </div>

          <div className="setting-group">
            <label htmlFor="llm-provider">LLM Provider</label>
            <select id="llm-provider" value={llmProvider} onChange={(e) => setLlmProvider(e.target.value)}>
              <option value="gemini">Google Gemini (Cloud)</option>
              <option value="local">Local LLM (Offline)</option>
            </select>
            <p className="setting-description">Choose between cloud-based Gemini API or local LLM for privacy</p>
          </div>

          {llmProvider === "gemini" && (
            <div className="setting-group">
              <label htmlFor="gemini-key">Gemini API Key</label>
              <input
                type="password"
                id="gemini-key"
                value={geminiApiKey}
                onChange={(e) => setGeminiApiKey(e.target.value)}
                placeholder="Enter your Gemini API key"
              />
              <p className="setting-description">
                Get your API key from{" "}
                <a href="https://ai.google.dev/" target="_blank" rel="noopener noreferrer">
                  Google AI Studio
                </a>
              </p>
            </div>
          )}
        </div>

        <div className="settings-section">
          <div className="section-header">
            <Database size={20} />
            <h2>Indexing Settings</h2>
          </div>

          <div className="setting-group">
            <label htmlFor="chunk-size">Chunk Size</label>
            <input
              type="number"
              id="chunk-size"
              value={settings.chunkSize}
              onChange={(e) => handleSettingChange("chunkSize", Number.parseInt(e.target.value))}
              min="500"
              max="2000"
            />
            <p className="setting-description">Size of text chunks for embedding (500-2000 characters)</p>
          </div>

          <div className="setting-group">
            <label htmlFor="chunk-overlap">Chunk Overlap</label>
            <input
              type="number"
              id="chunk-overlap"
              value={settings.chunkOverlap}
              onChange={(e) => handleSettingChange("chunkOverlap", Number.parseInt(e.target.value))}
              min="0"
              max="500"
            />
            <p className="setting-description">Overlap between chunks to maintain context (0-500 characters)</p>
          </div>

          <div className="setting-group">
            <label htmlFor="similarity-threshold">Similarity Threshold</label>
            <input
              type="range"
              id="similarity-threshold"
              value={settings.similarityThreshold}
              onChange={(e) => handleSettingChange("similarityThreshold", Number.parseFloat(e.target.value))}
              min="0.1"
              max="1.0"
              step="0.1"
            />
            <span>{settings.similarityThreshold}</span>
            <p className="setting-description">Minimum similarity score for search results (0.1-1.0)</p>
          </div>
        </div>

        <div className="settings-section">
          <div className="section-header">
            <Shield size={20} />
            <h2>Privacy & Security</h2>
          </div>

          <div className="setting-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isEncryptionEnabled}
                onChange={(e) => setIsEncryptionEnabled(e.target.checked)}
              />
              <span>Enable database encryption</span>
            </label>
            <p className="setting-description">
              Encrypt your local database for additional security (requires restart)
            </p>
          </div>

          <div className="privacy-info">
            <Info size={16} />
            <div>
              <h4>Privacy Notice</h4>
              <p>
                SmartFile AI processes your files locally. No data is sent to external servers except when using cloud
                LLM providers (Gemini API) for generating answers.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="settings-actions">
        <button className="save-settings-btn" onClick={saveSettings}>
          Save Settings
        </button>
      </div>
    </div>
  )
}

export default Settings
