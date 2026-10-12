"use client"

import { useEffect, useMemo, useState } from "react"
import { tauriAPI, SystemTierInfo } from "../services/tauriApi"
import { ApiService } from "../services/api"

const STEPS = ["Welcome", "License", "System Check", "LLM Selection", "Install"]

type InstallChoice = "local" | "cloud"

interface LlmModelSpec {
  id: string
  displayName: string
  description: string
  sizeGb: number
  ramRequiredGb: number
  vramRequiredGb?: number
  contextLength: number
  parameters: string
  quantization: string
  minTier: number
  capabilities: string[]
  downloadCommand: string
}

const OLLAMA_MODELS: LlmModelSpec[] = [
  {
    id: "tinyllama:1.1b",
    displayName: "TinyLlama 1.1B",
    description: "Ultra-lightweight model for basic chat and quick responses.",
    sizeGb: 0.6,
    ramRequiredGb: 4,
    contextLength: 2048,
    parameters: "1.1B",
    quantization: "Q4_0",
    minTier: 1,
    capabilities: ["text", "lightweight"],
    downloadCommand: "ollama pull tinyllama:1.1b",
  },
  {
    id: "llama3.2:3b",
    displayName: "Llama 3.2 3B",
    description: "Small but capable general assistant with strong balance.",
    sizeGb: 2.0,
    ramRequiredGb: 6,
    contextLength: 8192,
    parameters: "3B",
    quantization: "Q4_K_M",
    minTier: 1,
    capabilities: ["text", "general"],
    downloadCommand: "ollama pull llama3.2:3b",
  },
  {
    id: "qwen2.5:7b",
    displayName: "Qwen 2.5 7B",
    description: "Multilingual model with strong code and long-context reasoning.",
    sizeGb: 4.7,
    ramRequiredGb: 8,
    contextLength: 32768,
    parameters: "7B",
    quantization: "Q4_K_M",
    minTier: 1,
    capabilities: ["text", "code", "multilingual"],
    downloadCommand: "ollama pull qwen2.5:7b",
  },
  {
    id: "llava:7b",
    displayName: "LLaVA 7B",
    description: "Vision + text model for image understanding and Q&A.",
    sizeGb: 4.7,
    ramRequiredGb: 8,
    vramRequiredGb: 6,
    contextLength: 4096,
    parameters: "7B",
    quantization: "Q4_0",
    minTier: 1,
    capabilities: ["vision", "text", "image-analysis"],
    downloadCommand: "ollama pull llava:7b",
  },
  {
    id: "llama3.2-vision:11b",
    displayName: "Llama 3.2 Vision 11B",
    description: "Advanced vision-language model with OCR and chart understanding.",
    sizeGb: 7.9,
    ramRequiredGb: 16,
    vramRequiredGb: 8,
    contextLength: 8192,
    parameters: "11B",
    quantization: "Q4_K_M",
    minTier: 2,
    capabilities: ["vision", "text", "ocr", "image-analysis"],
    downloadCommand: "ollama pull llama3.2-vision:11b",
  },
  {
    id: "llama3.1:8b",
    displayName: "Llama 3.1 8B",
    description: "Strong general-purpose model with long context window.",
    sizeGb: 4.7,
    ramRequiredGb: 12,
    contextLength: 131072,
    parameters: "8B",
    quantization: "Q4_K_M",
    minTier: 2,
    capabilities: ["text", "long-context"],
    downloadCommand: "ollama pull llama3.1:8b",
  },
  {
    id: "mistral:7b",
    displayName: "Mistral 7B",
    description: "Excellent reasoning model with good speed and quality.",
    sizeGb: 4.1,
    ramRequiredGb: 12,
    contextLength: 32768,
    parameters: "7B",
    quantization: "Q4_K_M",
    minTier: 2,
    capabilities: ["text", "reasoning"],
    downloadCommand: "ollama pull mistral:7b",
  },
  {
    id: "codellama:13b",
    displayName: "Code Llama 13B",
    description: "Code-specialized model for programming workflows.",
    sizeGb: 7.4,
    ramRequiredGb: 20,
    contextLength: 16384,
    parameters: "13B",
    quantization: "Q4_K_M",
    minTier: 3,
    capabilities: ["code", "text"],
    downloadCommand: "ollama pull codellama:13b",
  },
  {
    id: "llama3.1:70b",
    displayName: "Llama 3.1 70B",
    description: "Flagship large model for premium quality and reasoning.",
    sizeGb: 40.0,
    ramRequiredGb: 48,
    contextLength: 131072,
    parameters: "70B",
    quantization: "Q4_K_M",
    minTier: 3,
    capabilities: ["text", "advanced-reasoning"],
    downloadCommand: "ollama pull llama3.1:70b",
  },
]

const CLOUD_PROVIDERS = [
  { id: "openai", label: "OpenAI" },
  { id: "anthropic", label: "Claude (Anthropic)" },
  { id: "gemini", label: "Google Gemini" },
  { id: "openrouter", label: "OpenRouter" },
  { id: "groq", label: "Groq" },
]

export default function SetupWizard({ onComplete }: { onComplete: () => void }) {
  const isTauri = typeof window !== "undefined" && Boolean((window as any).__TAURI_INTERNALS__)
  const [step, setStep] = useState(1)
  const [systemInfo, setSystemInfo] = useState<SystemTierInfo | null>(null)
  const [systemLoading, setSystemLoading] = useState(false)
  const [systemError, setSystemError] = useState<string | null>(null)
  const [installChoice, setInstallChoice] = useState<InstallChoice>("local")
  const [selectedModels, setSelectedModels] = useState<string[]>([])
  const [downloadState, setDownloadState] = useState<Record<string, string>>({})
  const [cloudProvider, setCloudProvider] = useState("")
  const [cloudModel, setCloudModel] = useState("")
  const [cloudApiKey, setCloudApiKey] = useState("")

  const availableModels = useMemo(() => {
    if (!systemInfo) return []
    if (systemInfo.tier === 3) {
      return OLLAMA_MODELS.filter((model) => model.minTier <= systemInfo.tier)
    }
    return OLLAMA_MODELS.filter(
      (model) => model.minTier <= systemInfo.tier && systemInfo.ram_gb >= model.ramRequiredGb
    )
  }, [systemInfo])

  useEffect(() => {
    if (step === 3 && !systemInfo && !systemLoading) {
      runSystemCheck()
    }
  }, [step, systemInfo, systemLoading])

  const runSystemCheck = async () => {
    setSystemLoading(true)
    setSystemError(null)
    try {
      if (!isTauri) {
        setSystemError("System checks are available only in the desktop app.")
        return
      }
      const info = await tauriAPI.getSystemTier()
      setSystemInfo(info)
      if (info.recommended_models?.length) {
        setSelectedModels(info.recommended_models)
      }
    } catch (error) {
      setSystemError("System check failed. Please try again.")
    } finally {
      setSystemLoading(false)
    }
  }

  const toggleModel = (modelId: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelId) ? prev.filter((id) => id !== modelId) : [...prev, modelId]
    )
  }

  const downloadModel = async (modelId: string) => {
    if (!systemInfo?.ollama_installed) {
      window.alert("Ollama is not installed. Please install Ollama first.")
      return
    }
    const shouldDownload = window.confirm(`Download ${modelId} now?`)
    if (!shouldDownload) return

    setDownloadState((prev) => ({ ...prev, [modelId]: "downloading" }))
    try {
      await tauriAPI.downloadOllamaModel(modelId)
      setDownloadState((prev) => ({ ...prev, [modelId]: "completed" }))
    } catch (error) {
      setDownloadState((prev) => ({ ...prev, [modelId]: "failed" }))
    }
  }

  const handleInstall = async () => {
    if (installChoice === "cloud") {
      if (cloudProvider) {
        localStorage.setItem("llm_provider", cloudProvider)
      }
      if (cloudProvider && (cloudApiKey.trim() || cloudModel.trim())) {
        try {
          await ApiService.saveLLMConfig({
            provider: cloudProvider,
            api_key: cloudApiKey.trim() || undefined,
            model: cloudModel.trim() || undefined,
          })
        } catch (error) {
          // Ignore backend failures at install time
        }
      }
    }

    if (installChoice === "local") {
      localStorage.setItem("llm_provider", "ollama")
    }

    localStorage.setItem("setup_completed", "true")
    onComplete()
  }

  return (
    <div className="setup-wizard">
      <div className="setup-hero">
        <div className="setup-hero-content">
          <span className="setup-badge">Smart Files AI Setup</span>
          <h1>Welcome to Smart Files AI</h1>
          <p>Configure your system and choose the best AI option for your device.</p>
        </div>
        <div className="setup-steps">
          {STEPS.map((label, index) => (
            <div key={label} className={index + 1 === step ? "step active" : "step"}>
              <div className="step-index">{index + 1}</div>
              <div className="step-label">{label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="setup-body">
        {step === 1 && (
          <section className="setup-panel">
            <h2>Welcome</h2>
            <p>
              This wizard checks your hardware, recommends the right AI model tier, and prepares your
              Smart Files AI experience.
            </p>
            <ul>
              <li>Detect system specs and classify your tier</li>
              <li>Recommend the best local LLMs for your PC</li>
              <li>Optionally configure cloud providers</li>
            </ul>
          </section>
        )}

        {step === 2 && (
          <section className="setup-panel">
            <h2>License Agreement</h2>
            <div className="license-box">
              <p>
                By continuing, you agree to the Smart Files AI license agreement. The app runs locally
                and only uses cloud services if you enable them.
              </p>
              <p>
                You can switch providers or uninstall models at any time from Settings.
              </p>
            </div>
          </section>
        )}

        {step === 3 && (
          <section className="setup-panel">
            <h2>System Check</h2>
            {systemLoading && <p className="muted">Analyzing your system...</p>}
            {systemError && <p className="error-text">{systemError}</p>}
            {systemInfo && (
              <div className="system-card">
                <div className="tier-chip">Tier {systemInfo.tier}: {systemInfo.tier_name}</div>
                <p className="muted">{systemInfo.tier_description}</p>
                <div className="spec-grid">
                  <div>
                    <span>RAM</span>
                    <strong>{systemInfo.ram_gb.toFixed(1)} GB</strong>
                  </div>
                  <div>
                    <span>CPU Cores</span>
                    <strong>{systemInfo.cpu_cores}</strong>
                  </div>
                  <div>
                    <span>CPU Speed</span>
                    <strong>{systemInfo.cpu_frequency_ghz.toFixed(1)} GHz</strong>
                  </div>
                  <div>
                    <span>GPU</span>
                    <strong>{systemInfo.gpu_available ? systemInfo.gpu_name || "Detected" : "Not found"}</strong>
                  </div>
                  <div>
                    <span>VRAM</span>
                    <strong>{systemInfo.vram_gb ? `${systemInfo.vram_gb.toFixed(1)} GB` : "N/A"}</strong>
                  </div>
                  <div>
                    <span>Ollama</span>
                    <strong>{systemInfo.ollama_installed ? "Installed" : "Not installed"}</strong>
                  </div>
                </div>
              </div>
            )}
            <button className="secondary" onClick={runSystemCheck} disabled={systemLoading}>
              Re-run System Check
            </button>
          </section>
        )}

        {step === 4 && (
          <section className="setup-panel">
            <h2>LLM Selection</h2>
            <div className="choice-toggle">
              <label>
                <input
                  type="radio"
                  checked={installChoice === "local"}
                  onChange={() => setInstallChoice("local")}
                />
                Download Local LLM (Ollama)
              </label>
              <label>
                <input
                  type="radio"
                  checked={installChoice === "cloud"}
                  onChange={() => setInstallChoice("cloud")}
                />
                Use Cloud Provider
              </label>
            </div>

            {installChoice === "local" && (
              <div className="model-grid">
                {availableModels.map((model) => (
                  <div key={model.id} className="model-card">
                    <div className="model-header">
                      <h3>{model.displayName}</h3>
                      <span className="model-size">{model.sizeGb} GB</span>
                    </div>
                    <p>{model.description}</p>
                    <div className="model-specs">
                      <span>RAM: {model.ramRequiredGb} GB</span>
                      <span>VRAM: {model.vramRequiredGb ? `${model.vramRequiredGb} GB` : "Not required"}</span>
                      <span>Context: {model.contextLength.toLocaleString()}</span>
                      <span>Params: {model.parameters}</span>
                      <span>Quant: {model.quantization}</span>
                    </div>
                    <div className="model-tags">
                      {model.capabilities.map((cap) => (
                        <span key={cap}>{cap}</span>
                      ))}
                    </div>
                    <div className="model-actions">
                      <label>
                        <input
                          type="checkbox"
                          checked={selectedModels.includes(model.id)}
                          onChange={() => toggleModel(model.id)}
                        />
                        Include
                      </label>
                      <button onClick={() => downloadModel(model.id)}>
                        {downloadState[model.id] === "downloading"
                          ? "Downloading..."
                          : downloadState[model.id] === "completed"
                          ? "Downloaded"
                          : "Download"}
                      </button>
                    </div>
                    <code className="download-command">{model.downloadCommand}</code>
                  </div>
                ))}
              </div>
            )}

            {installChoice === "cloud" && (
              <div className="cloud-config">
                <label>Cloud Provider</label>
                <select value={cloudProvider} onChange={(event) => setCloudProvider(event.target.value)}>
                  <option value="">Select a provider</option>
                  {CLOUD_PROVIDERS.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.label}
                    </option>
                  ))}
                </select>
                <label>Model</label>
                <input
                  type="text"
                  value={cloudModel}
                  onChange={(event) => setCloudModel(event.target.value)}
                  placeholder="Enter the model name (e.g., gpt-4o, claude-3-5-sonnet)"
                />
                <label>API Key (optional for now)</label>
                <input
                  type="password"
                  value={cloudApiKey}
                  onChange={(event) => setCloudApiKey(event.target.value)}
                  placeholder="Paste your API key"
                />
              </div>
            )}
          </section>
        )}

        {step === 5 && (
          <section className="setup-panel">
            <h2>Install</h2>
            <p className="muted">
              Ready to apply your configuration. You can change providers later in Settings.
            </p>
            <div className="summary-card">
              <div>
                <span>Choice</span>
                <strong>{installChoice === "local" ? "Local LLM" : "Cloud Provider"}</strong>
              </div>
              <div>
                <span>Provider</span>
                <strong>{installChoice === "local" ? "Ollama" : cloudProvider || "Not selected"}</strong>
              </div>
              {installChoice === "cloud" && (
                <div>
                  <span>Model</span>
                  <strong>{cloudModel || "Not selected"}</strong>
                </div>
              )}
              {installChoice === "local" && (
                <div>
                  <span>Selected Models</span>
                  <strong>{selectedModels.length ? selectedModels.join(", ") : "None"}</strong>
                </div>
              )}
            </div>
            <button className="primary" onClick={handleInstall}>
              Install and Launch
            </button>
          </section>
        )}
      </div>

      <div className="setup-footer">
        <button
          className="secondary"
          onClick={() => setStep((prev) => Math.max(1, prev - 1))}
          disabled={step === 1}
        >
          Back
        </button>
        {step < STEPS.length && (
          <button className="primary" onClick={() => setStep((prev) => Math.min(STEPS.length, prev + 1))}>
            Continue
          </button>
        )}
      </div>
    </div>
  )
}
