# 🚀 Smart Files AI

**Privacy-First Adaptive Multimodal Desktop Intelligence System**

Smart Files AI is a privacy-first, cross-platform desktop application that transforms your local file system into an intelligent, AI-powered knowledge base using Retrieval-Augmented Generation (RAG).

Unlike traditional AI assistants, Smart Files AI runs locally by default, supports user-selected LLMs and Vision-Language Models (VLMs), and provides optional cloud integration — ensuring complete flexibility and control.

---

# ✨ Key Features

## 🧠 Adaptive AI Engine

* Automatically detects system RAM & GPU
* Suggests optimal local model tier
* Runs on low-end laptops to high-performance GPUs

## 🔎 Privacy-First RAG System

* 100% local document indexing
* Semantic search using embeddings
* Context-grounded AI responses
* No mandatory cloud dependency

## 🖼 Smart Image Indexing (Multimodal)

* Vision-Language Model support
* Automatic caption + metadata generation
* Semantic image search
  *Example: "blue shirt photo around September"*

## 🔓 BYOM (Bring Your Own Model)

* Supports custom GGUF models
* Plug-and-play via Ollama
* Compatible with local vision + text models

## ☁ Optional Cloud AI (Hybrid Mode)

* OpenRouter integration
* Gemini / Grok support
* Switch between:

  * Strict Local Mode
  * Hybrid Mode
  * Cloud-Enhanced Mode

---

# 🏗 Architecture Overview

```
Local Files
   ↓
Parsing & Chunking
   ↓
Embedding (all-MiniLM)
   ↓
SQLite Vector Database
   ↓
Query → Vector Retrieval
   ↓
Selected LLM (Local / BYOM / Cloud)
   ↓
Grounded AI Response
```

For Images:

```
Image
  ↓
Vision-Language Model
  ↓
Caption + Metadata
  ↓
Embedding
  ↓
Vector Database
  ↓
Semantic Search
```

---

# 🛠 Technology Stack

## Frontend

* Next.js
* Electron
* Tailwind CSS

## Backend

* FastAPI (Python)
* Model Manager Engine
* Ollama (Local Model Inference)

## AI & ML

* all-MiniLM-L6-v2 (Embeddings)
* Phi-2 (Default Lightweight LLM)
* SmolVLM / LLaVA / Qwen2-VL (Multimodal Support)
* Custom GGUF Model Support

## Database

* SQLite + Vector Indexing

## Cloud Integration (Optional)

* OpenRouter
* Gemini
* Grok

---

# 🧠 Model Tiers

| Tier      | Hardware    | Suggested Model          |
| --------- | ----------- | ------------------------ |
| Low-End   | <4GB RAM    | SmolVLM / Lightweight 3B |
| Mid-Range | 8–16GB RAM  | LLaVA-7B (Quantized)     |
| High-End  | 16GB+ / GPU | Qwen2-VL-7B              |

---

# 🔒 Privacy Philosophy

Smart Files AI is built on the principle that:

> Your files should never leave your device unless you explicitly choose.

* No background telemetry
* No forced cloud upload
* Full local indexing
* API usage only with user consent

---

# 🚀 Installation

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- Git

### 1️⃣ Clone Repository

```bash
git clone https://github.com/prawinkumar1506/Smart-Files-AI.git
cd Smart-Files-AI
```

### 2️⃣ Backend Setup

```bash
cd backend
python -m venv venv        # Create virtual environment
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3️⃣ Frontend + Electron

```bash
cd ..
npm install
npm run electron
```

### 4️⃣ Install Ollama (Optional for Local Models)

Download and install Ollama from:
https://ollama.com

Pull a model:

```bash
ollama pull phi
```

---

## Running the Application

### 1. Start the Backend

```bash
cd backend
source venv/bin/activate   # On Windows: venv\Scripts\activate
uvicorn main:app --reload
```

- The backend will be available at `http://localhost:8000`
- Make sure the backend is running before starting the frontend

### 2. Start the Frontend (Electron App)

In a new terminal (from the project root):

```bash
npm run electron
```

- The Electron desktop application will launch.
- The frontend communicates with the local backend.

### 3. For Development (React Frontend Only)

```bash
npm run dev
```

- Opens the React app in your browser (for UI development).
- You still need the backend running.

---

## Configuration

### Gemini API Setup (Optional)

1. Get your API key from [Google AI Studio](https://ai.google.dev/)
2. Open Smart Files AI and go to Settings
3. Enter your API key in the LLM Configuration section

### Local LLM Setup

For offline operation with local models:

1. Install Ollama from https://ollama.com
2. Download a compatible model (e.g., `ollama pull phi`)
3. Configure the model in Smart Files AI settings

---

## Usage

### Adding Folders

- Click "Manage Folders" in the sidebar
- Click "Add Folders" and select directories to index
- Wait for the indexing process to complete

### Searching Files

- Go to "Search Files"
- Enter your search query using natural language
- Browse through semantically similar results

### Asking Questions

- Navigate to "Ask Question"
- Type your question about your documents
- Get AI-powered answers with source citations

---

## File Support

Currently supported file types:

- Plain text (.txt, .md)
- Code files (.py, .js, .html, .css, .json)
- PDF documents (.pdf)
- Microsoft Word (.docx, .doc)
- Rich Text Format (.rtf)
- OpenDocument Text (.odt)

---

## Production Build

### Build Electron App for Your Platform

```bash
npm run dist
```

### Build for Specific Platforms

```bash
npm run dist:win    # Windows
npm run dist:mac    # macOS
npm run dist:linux  # Linux
```

- The built applications will be available in the `dist` folder.

---

## Project Structure

```
Smart-Files-AI/
├── backend/                 # Python FastAPI backend
│   ├── services/           # Core services (indexing, search, LLM)
│   ├── models/             # Data models and schemas
│   └── main.py             # FastAPI application entry point
├── src/                    # React frontend
│   ├── components/         # React components
│   ├── services/           # API client and utilities
│   └── App.tsx             # Main application component
├── public/                 # Electron main process
│   ├── electron.js         # Electron main process
│   └── preload.js          # Electron preload script
└── scripts/                # Setup and build scripts
```

---

## Running Tests

### Backend (Python/FastAPI)

```bash
cd backend
source venv/bin/activate    # On Windows: venv\Scripts\activate
pytest
```

### Frontend (React)

```bash
npm test
```

---

# 📌 Roadmap

* [ ] Face recognition for image clustering
* [ ] Multi-folder intelligent organization
* [ ] Encrypted local vector database
* [ ] Plugin system for community models
* [ ] Mobile companion app
* [ ] Advanced search filters and operators
* [ ] Document summarization features
* [ ] Integration with cloud storage providers

---

# 🎯 Target Users

* Students & Researchers
* Developers & AI Enthusiasts
* Privacy-conscious professionals
* Users with low-end hardware
* Open-source model experimenters

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

# 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

# 💡 Vision

Smart Files AI aims to become:

> The AI layer for personal computing — adaptive, private, and fully under user control.

---

## Support

- Open an issue on GitHub
- Check the documentation
- Join our community discussions

---
