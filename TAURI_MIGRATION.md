# Smart Files AI - Tauri Migration

This project has been migrated from Electron to Tauri for better performance, smaller bundle sizes, and improved security.

## What Changed

### Dependencies
- ✅ Tauri v2 (Rust-based)
- ❌ Electron (Removed)
- ✅ Tauri plugins: dialog, fs, shell

### Architecture
- Frontend: Next.js + React (unchanged)
- Backend: Python FastAPI (unchanged)
- Desktop wrapper: Tauri (was Electron)

## Development

### Prerequisites
- Node.js & pnpm
- Rust (install from https://rustup.rs/)
- Python 3.x

### Run in Development Mode

```bash
# Install dependencies
pnpm install

# Start Tauri app (includes Next.js dev server and Tauri)
pnpm tauri:dev
```

The app will automatically:
1. Start the Next.js dev server on http://localhost:3000
2. Launch the Tauri window
3. Start the Python backend (if configured)

### Build for Production

```bash
# Build for your current platform
pnpm tauri:build

# Or platform-specific builds
pnpm tauri:build:win    # Windows
pnpm tauri:build:mac    # macOS
pnpm tauri:build:linux  # Linux
```

## Migration Benefits

1. **Smaller Bundle Size**: ~3-5MB vs 150MB+ with Electron
2. **Better Performance**: Native Rust backend
3. **Improved Security**: Stronger sandboxing by default
4. **Cross-platform**: Single codebase for Windows, macOS, Linux

## API Changes

All previous Electron APIs have been migrated to Tauri:

| Electron API | Tauri Equivalent |
|-------------|------------------|
| `window.electronAPI.selectFolders()` | `tauriAPI.selectFolders()` |
| `window.electronAPI.openFile()` | `tauriAPI.openFile()` |
| `window.electronAPI.showFileInFolder()` | `tauriAPI.showFileInFolder()` |
| `window.electronAPI.getDrives()` | `tauriAPI.getDrives()` |
| `window.electronAPI.readDirectory()` | `tauriAPI.readDirectory()` |

All components have been updated automatically.

## Troubleshooting

### Rust not found
Install Rust: https://rustup.rs/

### Build errors
```bash
# Clean and rebuild
cd src-tauri
cargo clean
cd ..
pnpm tauri build
```

### Python backend not starting
Check that Python is in your PATH and backend/main.py exists.
