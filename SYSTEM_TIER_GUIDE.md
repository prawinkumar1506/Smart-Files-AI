# System Tier Classification & Offline LLM Setup Guide

SmartFile AI now features intelligent system tier classification and automatic LLM model recommendations based on your hardware capabilities!

## 🎯 System Tier Classification

Your PC/laptop is automatically classified into one of three tiers:

### Tier 1: Basic (Entry-Level)
**Requirements:**
- RAM: 4-15 GB
- CPU: Any
- GPU: Not required

**Optimized For:**
- Lightweight, efficient models
- Fast inference on modest hardware
- Minimal resource usage

**Recommended Models:**
1. **TinyLlama 1.1B** (0.6 GB)
   - Ultra-lightweight
   - Perfect for basic chat
   - 2048 token context

2. **Llama 3.2 3B** (2.0 GB)
   - Small but capable
   - Good for general tasks
   - 8192 token context

3. **Qwen 2.5 7B** (4.7 GB)
   - Multilingual support
   - Code generation
   - 32768 token context

4. **LLaVA 7B** (4.7 GB)
   - Vision + text model
   - Image analysis capability
   - 4096 token context

---

### Tier 2: Performance (Mid-Range)
**Requirements:**
- RAM: 16-31 GB
- CPU: 4+ cores
- GPU: Optional but beneficial

**Optimized For:**
- Medium-sized models
- Good balance of performance and resource usage
- Vision-language models

**Recommended Models:**
All from Tier 1, plus:

5. **Llama 3.2 Vision 11B** (7.9 GB)
   - Advanced vision-language model
   - State-of-the-art image understanding
   - OCR capabilities
   - 8192 token context

6. **Llama 3.1 8B** (4.7 GB)
   - Enhanced reasoning
   - Multilingual
   - Massive 131K token context

7. **Mistral 7B** (4.1 GB)
   - Excellent reasoning
   - Code generation
   - 32768 token context

---

### Tier 3: Enthusiast (High-End)
**Requirements:**
- RAM: 32+ GB
- CPU: 8+ cores
- GPU: 12+ GB VRAM (recommended)

**Optimized For:**
- Large models with 70B+ parameters
- Maximum quality responses
- Complex reasoning tasks
- Professional use

**Recommended Models:**
All from Tiers 1 & 2, plus:

8. **Code Llama 13B** (7.4 GB)
   - Specialized for code
   - Multiple programming languages
   - Debugging and refactoring
   - 16384 token context

9. **Llama 3.1 70B** (40.0 GB) 🌟
   - Flagship large model
   - Exceptional performance
   - Creative writing
   - Advanced reasoning
   - 131K token context

---

## 📥 Installation-Time Setup

### During First Launch

The Setup Wizard automatically appears on first launch and:

1. **Analyzes Your System**
   - Detects RAM, CPU cores, CPU frequency
   - Checks for NVIDIA GPU and VRAM
   - Classifies into appropriate tier

2. **Shows System Specs**
   - Visual tier badge (💻 Basic, ⚡ Performance, 🚀 Enthusiast)
   - Detailed hardware information
   - Tier-appropriate description

3. **Recommends Models**
   - Only shows models suitable for your tier
   - Sorted by size (smallest first)
   - Full specifications for each model

4. **Enables Quick Download**
   - One-click model download
   - Real-time progress tracking
   - Background downloads

5. **Validates Ollama**
   - Checks if Ollama is running
   - Provides installation link if missing
   - Clear status indicators

---

## 🤖 Featured Vision Models

### LLaVA 7B
**Specifications:**
- **Size**: 4.7 GB
- **RAM Required**: 8 GB
- **VRAM Recommended**: 6 GB
- **Capabilities**: Text, Vision, Image Analysis, Visual Q&A
- **Context Length**: 4096 tokens
- **Parameters**: 7B (Q4_0 quantization)

**What It Can Do:**
- Analyze images and answer questions about them
- Describe visual content in detail
- Extract information from images
- Visual reasoning tasks

**Download Command:**
```bash
ollama pull llava:7b
```

---

### Qwen 2.5 7B
**Specifications:**
- **Size**: 4.7 GB
- **RAM Required**: 8 GB
- **VRAM**: Not required
- **Capabilities**: Text, Code, Multilingual, Reasoning
- **Context Length**: 32,768 tokens
- **Parameters**: 7B (Q4_K_M quantization)

**What It Can Do:**
- Chinese-English bilingual tasks
- Advanced code generation
- Complex reasoning
- Long document processing

**Download Command:**
```bash
ollama pull qwen2.5:7b
```

---

### Llama 3.2 Vision 11B
**Specifications:**
- **Size**: 7.9 GB
- **RAM Required**: 16 GB
- **VRAM Recommended**: 8 GB
- **Capabilities**: Text, Vision, Image Analysis, Visual Q&A, OCR
- **Context Length**: 8192 tokens
- **Parameters**: 11B (Q4_K_M quantization)

**What It Can Do:**
- State-of-the-art image understanding
- OCR (text extraction from images)
- Advanced visual reasoning
- Multi-modal document analysis
- Diagram and chart interpretation

**Download Command:**
```bash
ollama pull llama3.2-vision:11b
```

---

## 🚀 API Endpoints

### Get System Tier
```bash
GET /api/settings/system-tier
```

**Response:**
```json
{
  "tier": 2,
  "tier_name": "Performance",
  "ram_gb": 16.0,
  "cpu_cores": 8,
  "cpu_frequency_ghz": 3.6,
  "gpu_available": true,
  "gpu_name": "NVIDIA RTX 3060",
  "vram_gb": 12.0,
  "recommended_models": [
    "llama3.2-vision:11b",
    "llama3.1:8b",
    "mistral:7b",
    "qwen2.5:7b",
    "llava:7b",
    "llama3.2:3b"
  ],
  "tier_description": "Mid-range system - Can run models up to 13B parameters"
}
```

---

### Get Available Models
```bash
GET /api/ollama/models?tier=2
```

**Response:**
```json
[
  {
    "name": "llava",
    "tag": "7b",
    "full_name": "llava:7b",
    "display_name": "LLaVA 7B (Vision)",
    "description": "Multimodal model combining Llama-2 with vision capabilities...",
    "size_gb": 4.7,
    "ram_required_gb": 8,
    "vram_required_gb": 6,
    "min_tier": 1,
    "capabilities": ["text", "vision", "image-analysis", "visual-qa"],
    "context_length": 4096,
    "parameters": "7B",
    "quantization": "Q4_0",
    "download_url": "llava:7b",
    "is_downloaded": false,
    "download_progress": 0.0
  }
]
```

---

### Download Model
```bash
POST /api/ollama/download
Content-Type: application/json

{
  "model_name": "llava:7b"
}
```

**Response:**
```json
{
  "model_name": "llava:7b",
  "status": "downloading",
  "progress": 0.0,
  "downloaded_bytes": 0,
  "total_bytes": 5046586573,
  "message": "Starting download of llava:7b..."
}
```

---

### Check Download Status
```bash
GET /api/ollama/download/status/llava:7b
```

**Response:**
```json
{
  "model_name": "llava:7b",
  "status": "completed",
  "progress": 100.0,
  "downloaded_bytes": 5046586573,
  "total_bytes": 5046586573,
  "message": "Model llava:7b is installed"
}
```

---

### Delete Model
```bash
DELETE /api/ollama/models/llava:7b
```

**Response:**
```json
{
  "success": true,
  "message": "Model llava:7b deleted successfully"
}
```

---

## 💡 Usage Guide

### For Users

1. **Launch SmartFile AI**
   - Setup Wizard appears automatically on first run
   - System is analyzed in seconds

2. **Review Your Tier**
   - Check your system classification
   - See detailed hardware specs

3. **Choose Models**
   - Browse recommended models
   - Read specifications and capabilities
   - Click "Download Model" for desired models

4. **Track Downloads**
   - Real-time progress bars
   - Download size and speed
   - Multiple models can download simultaneously

5. **Start Using**
   - Once downloaded, models are immediately available
   - Change provider to "Ollama" in Settings
   - Select your downloaded model

---

### For Developers

**Frontend Integration:**
```typescript
import SetupWizard from './components/SetupWizard'

function App() {
  const [showSetup, setShowSetup] = useState(
    !localStorage.getItem('setup_completed')
  )

  if (showSetup) {
    return (
      <SetupWizard 
        onComplete={() => {
          localStorage.setItem('setup_completed', 'true')
          setShowSetup(false)
        }}
      />
    )
  }

  return <MainApp />
}
```

**Get System Tier:**
```typescript
const tier = await ApiService.getSystemTier()
console.log(`Your system: ${tier.tier_name}`)
console.log(`Recommended: ${tier.recommended_models.join(', ')}`)
```

**Download Model:**
```typescript
try {
  const status = await ApiService.downloadOllamaModel('llava:7b')
  console.log(`Download started: ${status.message}`)
  
  // Poll for progress
  const interval = setInterval(async () => {
    const progress = await ApiService.getModelDownloadStatus('llava:7b')
    console.log(`Progress: ${progress.progress}%`)
    
    if (progress.status === 'completed') {
      clearInterval(interval)
      console.log('Download complete!')
    }
  }, 2000)
} catch (error) {
  console.error('Download failed:', error)
}
```

---

## 🔧 Prerequisites

### Required Software

1. **Ollama** (for local models)
   - Download: https://ollama.ai/
   - Windows/Mac/Linux supported
   - Runs as a background service

2. **NVIDIA GPU Drivers** (optional, for GPU acceleration)
   - Download: https://www.nvidia.com/drivers
   - Required for vision models on GPU

3. **Sufficient Disk Space**
   - Tier 1: At least 5 GB free
   - Tier 2: At least 20 GB free
   - Tier 3: At least 50 GB free

---

## 📊 Model Comparison

| Model | Size | Tier | Best For | Special Features |
|-------|------|------|----------|-----------------|
| TinyLlama | 0.6 GB | 1 | Low-end PCs | Ultra-fast |
| Llama 3.2 3B | 2.0 GB | 1 | General chat | Balanced |
| LLaVA 7B | 4.7 GB | 1 | Image analysis | Vision |
| Qwen 2.5 7B | 4.7 GB | 1 | Multilingual | Code + Chinese |
| Llama 3.2 Vision 11B | 7.9 GB | 2 | Advanced vision | OCR + Vision |
| Llama 3.1 8B | 4.7 GB | 2 | Long context | 131K tokens |
| Mistral 7B | 4.1 GB | 2 | Reasoning | 32K context |
| Code Llama 13B | 7.4 GB | 3 | Programming | Code specialist |
| Llama 3.1 70B | 40.0 GB | 3 | Professional | Flagship model |

---

## ⚙️ Configuration

### Enable/Disable Setup Wizard

**Skip Setup:**
```typescript
localStorage.setItem('setup_completed', 'true')
```

**Show Setup Again:**
```typescript
localStorage.removeItem('setup_completed')
```

### Change Default Tier Thresholds

Edit `backend/main.py`:

```python
# Current thresholds
if ram_gb >= 32 and cpu_cores >= 8:
    tier = 3  # Enthusiast
elif ram_gb >= 16 and cpu_cores >= 4:
    tier = 2  # Performance
else:
    tier = 1  # Basic
```

---

## 🎨 UI Components

### SetupWizard
- Full-screen onboarding experience
- Gradient background
- Responsive design
- Real-time download tracking

### System Tier Card
- Color-coded by tier
- Hardware specifications display
- Tier icons (💻⚡🚀)

### Model Cards
- Compact information layout
- Download/progress buttons
- Capability tags
- Size and RAM requirements

---

## 🐛 Troubleshooting

### "Ollama Not Detected"
**Solution:** Install Ollama from https://ollama.ai/ and ensure it's running

### "Model Download Failed"
**Solution:** 
1. Check internet connection
2. Verify Ollama is running: `ollama list`
3. Try manual download: `ollama pull model:tag`

### "Insufficient RAM"
**Solution:** Your system tier restricts which models you can download. Upgrade RAM or choose smaller models.

### Vision Models Not Working
**Solution:**
1. Ensure GPU drivers are up to date
2. Check VRAM availability
3. Try running with CPU: models will be slower but functional

---

## 📈 Future Enhancements

- [ ] Auto-detect best quantization based on VRAM
- [ ] Model performance benchmarking
- [ ] Custom model upload support
- [ ] Model merging capabilities
- [ ] Automatic model updates
- [ ] Hardware monitoring during inference
- [ ] Model usage statistics

---

## 🤝 Contributing

To add more models to the database, edit `OLLAMA_MODELS_DB` in `backend/main.py`:

```python
OLLAMA_MODELS_DB = {
    "your-model:tag": {
        "name": "your-model",
        "tag": "tag",
        "full_name": "your-model:tag",
        "display_name": "Your Model Display Name",
        "description": "Model description...",
        "size_gb": 5.0,
        "ram_required_gb": 8,
        "vram_required_gb": 6,  # Optional
        "min_tier": 1,
        "capabilities": ["text", "code"],
        "context_length": 4096,
        "parameters": "7B",
        "quantization": "Q4_K_M",
        "download_url": "your-model:tag"
    }
}
```

---

**Made with ❤️ for SmartFile AI users**

*Intelligent AI Model Management - Optimized for Your Hardware*
