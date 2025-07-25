# SmartFile AI

A privacy-first desktop application that semantically indexes and queries your local files entirely offline.

---

## Features

- **Semantic Search:** Find content across all your files using natural language queries
- **AI-Powered Q&A:** Ask questions about your documents and get intelligent answers
- **Privacy-First:** All processing happens locally on your device
- **Cross-Platform:** Works on Windows, macOS, and Linux
- **Multiple File Types:** Supports PDF, DOCX, TXT, Markdown, and more
- **Offline Operation:** No internet required for indexing and searching
- **Flexible LLM Support:** Use Gemini API or local models

---

## Tech Stack

- **Backend:** Python with FastAPI
- **Frontend:** React with TypeScript
- **Desktop:** Electron
- **Vector Storage:** SQLite with vector extensions
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **LLM:** Google Gemini API (with local model support)

---

## Installation & Setup

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- Git

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/smartfile-ai.git
cd smartfile-ai
```

### 2. Backend Setup (Python/FastAPI)

It's recommended to use a virtual environment for Python dependencies.

```bash
cd backend
python -m venv venv        # Create virtual environment
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 3. Frontend Setup (React/Electron)

```bash
npm install
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

## Production Build

### Build Electron App for Your Platform

```bash
npm run dist
```

### Build for All Platforms

```bash
npm run dist-all
```

- The built applications will be available in the `dist` folder.

---

## Configuration

### Gemini API Setup

1. Get your API key from [Google AI Studio](https://ai.google.dev/)
2. Open SmartFile AI and go to Settings
3. Enter your API key in the LLM Configuration section

### Local LLM Setup

For offline operation with local models:

1. Install additional dependencies for local models
2. Download a compatible model (e.g., Mistral-7B)
3. Configure the model path in SmartFile AI settings

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

## Privacy & Security

- **Local Processing:** All file indexing and searching happens on your device
- **No Data Collection:** No telemetry or analytics are collected
- **Encrypted Storage:** Optional database encryption for sensitive data
- **Selective Access:** Only index folders you explicitly choose
- **Easy Removal:** Remove folders and clear data at any time

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

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI        │    │   SQLite +      │
│   (Electron)    │◄──►│   Backend        │◄──►│   Vector Store  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   LLM Client     │
                       │   (Gemini/Local) │
                       └──────────────────┘
```

---

## Project Structure

```
smartfile-ai/
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support

- Open an issue on GitHub
- Check the documentation
- Join our community discussions

---

## Roadmap

- [ ] Support for more file types (images, audio, video)
- [ ] Advanced search filters and operators
- [ ] Document summarization features
- [ ] Integration with cloud storage providers
- [ ] Plugin system for custom processors
- [ ] Mobile companion app

---
