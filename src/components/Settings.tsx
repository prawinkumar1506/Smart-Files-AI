"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { 
  Database, Shield, Info, CheckCircle2, XCircle, AlertTriangle,
  Cloud, Cpu as CpuChip, Download, Check, Loader2, Eye, EyeOff
} from "lucide-react"
import { ApiService } from "../services/api"

interface SystemRequirement {
  name: string
  met: boolean
  value?: string
  message: string
  critical: boolean
}

// Cloud Provider Configurations
const CLOUD_PROVIDERS: Record<string, { displayName: string; models: string[]; url: string }> = {
  ollama: {
    displayName: "Ollama (Local)",
    models: ["llava:7b", "llama3.2:3b", "mistral:7b", "qwen2.5:7b"],
    url: "https://ollama.ai"
  },
  openai: {
    displayName: "OpenAI",
    models: ["gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    url: "https://platform.openai.com/api-keys"
  },
  anthropic: {
    displayName: "Anthropic Claude",
    models: ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"],
    url: "https://console.anthropic.com/keys"
  },
  groq: {
    displayName: "Groq",
    models: ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
    url: "https://console.groq.com/keys"
  },
  openrouter: {
    displayName: "OpenRouter",
    models: ["meta-llama/llama-3.1-8b-instruct", "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"],
    url: "https://openrouter.ai/keys"
  },
  gemini: {
    displayName: "Google Gemini",
    models: ["gemini-2.5-flash", "gemini-1.5-flash"],
    url: "https://ai.google.dev/tutorials/setup"
  }
}

// Local Models Data
const LOCAL_MODELS = [
  { id: "tinyllama:1.1b", name: "TinyLlama 1.1B", size: "600 MB", ram: "2 GB", tier: 1 },
  { id: "llama3.2:3b", name: "Llama 3.2 3B", size: "2.0 GB", ram: "4 GB", tier: 1 },
  { id: "qwen2.5:7b", name: "Qwen 2.5 7B", size: "4.7 GB", ram: "8 GB", tier: 1 },
  { id: "llava:7b", name: "LLaVA 7B (Vision)", size: "4.7 GB", ram: "8 GB", tier: 1 },
  { id: "mistral:7b", name: "Mistral 7B", size: "4.1 GB", ram: "8 GB", tier: 2 },
  { id: "llama3.1:8b", name: "Llama 3.1 8B", size: "4.7 GB", ram: "12 GB", tier: 2 },
  { id: "llama3.2-vision:11b", name: "Llama 3.2 Vision 11B", size: "7.9 GB", ram: "16 GB", tier: 2 },
  { id: "codellama:13b", name: "CodeLlama 13B", size: "7.4 GB", ram: "16 GB", tier: 3 },
  { id: "llama3.1:70b", name: "Llama 3.1 70B", size: "40 GB", ram: "48 GB", tier: 3 },
]

const Settings: React.FC = () => {
  const [currentProvider, setCurrentProvider] = useState<string>(localStorage.getItem("llm_provider") || "gemini")
  const [providerModels, setProviderModels] = useState<Record<string, string>>({})
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({})
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({})
  const [testing, setTesting] = useState<Record<string, boolean>>({})
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({})
  const [downloading, setDownloading] = useState<Record<string, boolean>>({})
  const [systemRequirements, setSystemRequirements] = useState<SystemRequirement[]>([])
  const [requirementsLoading, setRequirementsLoading] = useState(true)
  const [isEncryptionEnabled, setIsEncryptionEnabled] = useState(false)
  const [settings, setSettings] = useState({
    chunkSize: 1000,
    chunkOverlap: 200,
    similarityThreshold: 0.7,
    maxResults: 20,
  })

  useEffect(() => {
    loadSettings()
    checkSystemRequirements()
  }, [])

  const loadSettings = async () => {
    try {
      const savedProvider = localStorage.getItem("llm_provider") || "gemini"
      setCurrentProvider(savedProvider)

      const providers = Object.keys(CLOUD_PROVIDERS)
      const configs = await Promise.all(
        providers.map(async (provider) => {
          try {
            const config = await ApiService.getLLMConfig(provider)
            return { provider, config }
          } catch {
            return { provider, config: {} }
          }
        }),
      )

      const nextModels: Record<string, string> = {}
      const nextKeys: Record<string, string> = {}

      configs.forEach(({ provider, config }: any) => {
        nextModels[provider] = config.model || CLOUD_PROVIDERS[provider].models[0]
        if (config.api_key) {
          nextKeys[provider] = config.api_key
        }
      })

      setProviderModels(nextModels)
      setApiKeys(nextKeys)
    } catch (error) {
      console.error("Error loading settings:", error)
    }
    
    const encryption = localStorage.getItem("encryption_enabled") === "true"
    setIsEncryptionEnabled(encryption)
  }

  const checkSystemRequirements = async () => {
    try {
      const result = await ApiService.checkSystemRequirements()
      setSystemRequirements(result.requirements || [])
    } catch (error) {
      console.error("Error checking system requirements:", error)
    } finally {
      setRequirementsLoading(false)
    }
  }

  const showToast = (message: string, type: "success" | "error" = "success") => {
    alert(message)
  }

  const testApiKey = async (provider: string) => {
    const requiresApiKey = provider !== "ollama"
    if (requiresApiKey && !apiKeys[provider]?.trim()) {
      showToast("Please enter an API key", "error")
      return
    }

    setTesting(prev => ({ ...prev, [provider]: true }))
    try {
      const model = providerModels[provider] || CLOUD_PROVIDERS[provider].models[0]
      await ApiService.saveLLMConfig({ provider, api_key: requiresApiKey ? (apiKeys[provider] || "") : "", model })
      setTestResults(prev => ({ ...prev, [provider]: { success: true, message: provider === "ollama" ? "Local model connection works" : "API key valid" } }))
      showToast(provider === "ollama" ? "Local model connection works" : "API key is valid")
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || "Failed to validate"
      setTestResults(prev => ({ ...prev, [provider]: { success: false, message } }))
      showToast(message, "error")
    } finally {
      setTesting(prev => ({ ...prev, [provider]: false }))
    }
  }

  const saveProvider = async (provider: string) => {
    try {
      const model = providerModels[provider] || CLOUD_PROVIDERS[provider].models[0]
      const apiKey = provider === "ollama" ? "" : (apiKeys[provider] || "")
      await ApiService.saveLLMConfig({ provider, api_key: apiKey, model })
      localStorage.setItem("llm_provider", provider)
      setCurrentProvider(provider)
      showToast(`Using ${CLOUD_PROVIDERS[provider].displayName}`)
    } catch (error: any) {
      showToast(error.response?.data?.detail || "Failed to save", "error")
    }
  }

  const downloadModel = async (modelId: string) => {
    setDownloading(prev => ({ ...prev, [modelId]: true }))
    try {
      await ApiService.downloadOllamaModel(modelId)
      showToast(`${modelId} downloaded!`)
    } catch (error: any) {
      showToast(error.message || "Download failed", "error")
    } finally {
      setDownloading(prev => ({ ...prev, [modelId]: false }))
    }
  }

  const saveAllSettings = async () => {
    try {
      localStorage.setItem("encryption_enabled", isEncryptionEnabled.toString())
      showToast("Settings saved!")
    } catch (error) {
      showToast("Failed to save settings", "error")
    }
  }

  return (
    <div className="settings-page" style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      <div className="settings-header">
        <div className="settings-header-content">
          <div className="settings-header-logo">
            <img src="/smartfilesAI.png" alt="Smart Files AI" />
          </div>
          <div className="settings-header-text">
            <h1>Settings</h1>
            <p>Configure your LLM providers and preferences</p>
          </div>
        </div>
      </div>

      <div className="settings-scroll-container" style={{ flex: 1, overflowY: "auto", overflowX: "hidden", scrollBehavior: "smooth" }}>
        <div className="settings-content-wrapper" style={{ padding: "40px 60px", maxWidth: "1400px", margin: "0 auto" }}>
          
          {/* Cloud LLM Providers Section */}
          <div className="settings-section" style={{ marginBottom: "50px" }}>
            <div className="section-header">
              <Cloud size={24} />
              <h2>Cloud LLM Providers</h2>
            </div>
            <p className="section-description">Select and configure your preferred cloud AI provider.</p>

            <div className="providers-grid">
              {Object.entries(CLOUD_PROVIDERS).map(([key, provider]) => (
                <div key={key} className={`provider-card ${currentProvider === key ? "selected" : ""}`}>
                  <div className="provider-header">
                    <h3>{provider.displayName}</h3>
                    {currentProvider === key && <CheckCircle2 size={20} className="selected-badge" />}
                  </div>

                  <div className="provider-config">
                    <div className="form-group">
                      <label>Model</label>
                      <select 
                        value={providerModels[key] || ""}
                        onChange={(e) => setProviderModels((prev) => ({ ...prev, [key]: e.target.value }))}
                      >
                        <option value="">Select a model</option>
                        {provider.models.map(m => <option key={m} value={m}>{m}</option>)}
                      </select>
                    </div>

                    <div className="form-group">
                      <label>API Key</label>
                      {key === "ollama" ? (
                        <p className="setting-description">No API key required. Uses local Ollama service.</p>
                      ) : (
                        <>
                          <div className="api-key-input-group">
                            <input
                              type={showApiKey[key] ? "text" : "password"}
                              value={apiKeys[key] || ""}
                              onChange={(e) => setApiKeys(p => ({ ...p, [key]: e.target.value }))}
                              placeholder="Enter your API key"
                            />
                            <button 
                              onClick={() => setShowApiKey(p => ({ ...p, [key]: !p[key] }))}
                              className="toggle-visibility"
                              type="button"
                            >
                              {showApiKey[key] ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                          </div>
                          <a href={provider.url} target="_blank" rel="noopener noreferrer" className="provider-link">
                            Get API Key →
                          </a>
                        </>
                      )}
                    </div>

                    <div className="button-group">
                      <button 
                        className="btn-test"
                        onClick={() => testApiKey(key)}
                        disabled={testing[key] || (key !== "ollama" && !apiKeys[key])}
                      >
                        {testing[key] ? <Loader2 size={16} className="spinner" /> : <Check size={16} />}
                        {key === "ollama" ? "Test Local" : "Test"}
                      </button>
                      <button 
                        className="btn-save"
                        onClick={() => saveProvider(key)}
                      >
                        {currentProvider === key ? "Current Provider" : "Use This Provider"}
                      </button>
                    </div>

                    {testResults[key] && (
                      <div className={`test-result ${testResults[key].success ? "success" : "error"}`}>
                        {testResults[key].message}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Local LLMs Section */}
          <div className="settings-section" style={{ marginBottom: "50px" }}>
            <div className="section-header">
              <CpuChip size={24} />
              <h2>Local LLMs (Ollama)</h2>
            </div>
            <p className="section-description">Download and manage local AI models. No API keys required.</p>

            <div className="local-models-info">
              <Info size={20} />
              <div>
                <div className="bold">Requirements</div>
                <ul>
                  <li>• Ollama must be installed and running</li>
                  <li>• Models run locally on your machine</li>
                  <li>• No internet required after download</li>
                </ul>
              </div>
            </div>

            <div className="model-management">
              <h3>Available Models</h3>
              <div className="models-list">
                {[1, 2, 3].map(tier => (
                  <div key={tier} className="tier-section">
                    <h4>
                      {tier === 1 ? "Tier 1 - Small" : tier === 2 ? "Tier 2 - Medium" : "Tier 3 - Powerful"}
                    </h4>
                    <div className="tier-models">
                      {LOCAL_MODELS.filter(m => m.tier === tier).map(model => (
                        <div key={model.id} className="model-item">
                          <div className="model-info">
                            <h5>{model.name}</h5>
                            <p>{model.size} • {model.ram} RAM</p>
                          </div>
                          <button 
                            className="btn-download"
                            onClick={() => downloadModel(model.id)}
                            disabled={downloading[model.id]}
                          >
                            {downloading[model.id] ? (
                              <><Loader2 size={16} className="spinner" /> Downloading...</>
                            ) : (
                              <><Download size={16} /> Download</>
                            )}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Indexing Settings Section */}
          <div className="settings-section" style={{ marginBottom: "50px" }}>
            <div className="section-header">
              <Database size={24} />
              <h2>Indexing Settings</h2>
            </div>
            
            <div className="setting-group">
              <label>Chunk Size</label>
              <input
                type="number"
                value={settings.chunkSize}
                onChange={(e) => setSettings(p => ({ ...p, chunkSize: parseInt(e.target.value) }))}
                min="500" max="2000"
              />
              <p className="setting-description">Characters per chunk (500-2000)</p>
            </div>

            <div className="setting-group">
              <label>Chunk Overlap</label>
              <input
                type="number"
                value={settings.chunkOverlap}
                onChange={(e) => setSettings(p => ({ ...p, chunkOverlap: parseInt(e.target.value) }))}
                min="0" max="500"
              />
              <p className="setting-description">Overlap between chunks (0-500)</p>
            </div>

            <div className="setting-group">
              <label>Similarity Threshold: <span className="threshold-value">{settings.similarityThreshold.toFixed(2)}</span></label>
              <input
                type="range"
                value={settings.similarityThreshold}
                onChange={(e) => setSettings(p => ({ ...p, similarityThreshold: parseFloat(e.target.value) }))}
                min="0.1" max="1.0" step="0.1"
              />
              <p className="setting-description">Minimum similarity for search results</p>
            </div>

            <div className="setting-group">
              <label>Max Results</label>
              <input
                type="number"
                value={settings.maxResults}
                onChange={(e) => setSettings(p => ({ ...p, maxResults: parseInt(e.target.value) }))}
                min="5" max="100"
              />
              <p className="setting-description">Maximum search results (5-100)</p>
            </div>
          </div>

          {/* Security Section */}
          <div className="settings-section" style={{ marginBottom: "50px" }}>
            <div className="section-header">
              <Shield size={24} />
              <h2>Privacy & Security</h2>
            </div>

            <div className="security-grid">
              <div className="security-card">
                <div className="security-card-header">
                  <Shield size={18} />
                  <h4>Data Protection</h4>
                </div>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={isEncryptionEnabled}
                    onChange={(e) => setIsEncryptionEnabled(e.target.checked)}
                  />
                  <span>Enable local database encryption</span>
                </label>
                <p className="setting-description">Protects stored metadata at rest. App restart may be required.</p>
              </div>

              <div className="security-card security-highlight">
                <div className="security-card-header">
                  <Info size={18} />
                  <h4>Privacy Policy</h4>
                </div>
                <p>Your files are indexed locally by default. Data only leaves your device when you use cloud providers.</p>
              </div>
            </div>

            {requirementsLoading ? (
              <p style={{ textAlign: "center", padding: "20px", color: "#6b7280" }}>Checking system...</p>
            ) : (
              <div className="system-requirements" style={{ marginTop: "30px" }}>
                <h3 style={{ fontSize: "18px", fontWeight: "600", marginBottom: "15px" }}>System Requirements</h3>
                {systemRequirements.map((req, i) => (
                  <div key={i} className="requirement-item">
                    <div className="requirement-status">
                      {req.met ? (
                        <CheckCircle2 size={20} className="status-success" />
                      ) : req.critical ? (
                        <XCircle size={20} className="status-error" />
                      ) : (
                        <AlertTriangle size={20} className="status-warning" />
                      )}
                    </div>
                    <div className="requirement-details">
                      <div className="requirement-name">{req.name}</div>
                      <div className="requirement-message">{req.message}</div>
                    </div>
                    {req.value && <span className="requirement-value">{req.value}</span>}
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: "30px", paddingBottom: "20px" }}>
              <button className="save-settings-btn" onClick={saveAllSettings}>
                Save All Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings
