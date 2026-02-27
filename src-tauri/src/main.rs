// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Serialize;
use std::path::Path;
use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{Emitter, Manager};

#[derive(Clone, Serialize)]
struct BackendPortPayload {
    port: u16,
}

#[derive(Serialize)]
struct FileOperationResult {
    success: bool,
    error: Option<String>,
}

#[derive(Serialize)]
struct DirectoryItem {
    name: String,
    path: String,
    is_directory: bool,
}

#[derive(Serialize)]
struct PathStat {
    exists: bool,
    is_directory: bool,
    path: String,
}

struct BackendProcess(Mutex<Option<Child>>);

#[tauri::command]
async fn select_folders(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    use tauri_plugin_dialog::{DialogExt, FilePath};
    
    let file_path = app
        .dialog()
        .file()
        .set_title("Select files (folder will be indexed)")
        .blocking_pick_files();
    
    if let Some(files) = file_path {
        // Extract unique parent directories from selected files
        let mut unique_folders: std::collections::HashSet<String> = std::collections::HashSet::new();
        for file in files {
            let path = match file {
                FilePath::Path(path) => path,
                FilePath::Url(url) => {
                    if let Ok(path) = url.to_file_path() {
                        path
                    } else {
                        continue;
                    }
                }
            };

            if let Some(parent) = path.parent() {
                unique_folders.insert(parent.to_string_lossy().to_string());
            }
        }
        Ok(unique_folders.into_iter().collect())
    } else {
        Ok(Vec::new())
    }
}

#[tauri::command]
async fn open_file(file_path: String) -> FileOperationResult {
    let result = opener::open(&file_path);
    
    match result {
        Ok(_) => FileOperationResult {
            success: true,
            error: None,
        },
        Err(e) => FileOperationResult {
            success: false,
            error: Some(e.to_string()),
        },
    }
}

#[tauri::command]
async fn show_file_in_folder(file_path: String) -> FileOperationResult {
    #[cfg(target_os = "windows")]
    {
        let result = Command::new("explorer")
            .args(["/select,", &file_path])
            .spawn();
        
        match result {
            Ok(_) => FileOperationResult {
                success: true,
                error: None,
            },
            Err(e) => FileOperationResult {
                success: false,
                error: Some(e.to_string()),
            },
        }
    }
    
    #[cfg(target_os = "macos")]
    {
        let result = Command::new("open")
            .args(["-R", &file_path])
            .spawn();
        
        match result {
            Ok(_) => FileOperationResult {
                success: true,
                error: None,
            },
            Err(e) => FileOperationResult {
                success: false,
                error: Some(e.to_string()),
            },
        }
    }
    
    #[cfg(target_os = "linux")]
    {
        // Try different file managers
        let file_managers = ["nautilus", "dolphin", "thunar", "nemo"];
        let parent = Path::new(&file_path).parent();
        
        if let Some(parent_path) = parent {
            for fm in &file_managers {
                let result = Command::new(fm)
                    .arg(parent_path)
                    .spawn();
                
                if result.is_ok() {
                    return FileOperationResult {
                        success: true,
                        error: None,
                    };
                }
            }
        }
        
        FileOperationResult {
            success: false,
            error: Some("No supported file manager found".to_string()),
        }
    }
}

#[tauri::command]
async fn get_home_directory() -> Result<String, String> {
    dirs::home_dir()
        .ok_or_else(|| "Could not determine home directory".to_string())
        .map(|p| p.to_string_lossy().to_string())
}

#[tauri::command]
async fn get_drives() -> Vec<String> {
    #[cfg(target_os = "windows")]
    {
        let mut drives = Vec::new();
        for letter in b'A'..=b'Z' {
            let drive = format!("{}:\\", letter as char);
            if Path::new(&drive).exists() {
                drives.push(drive);
            }
        }
        drives
    }
    
    #[cfg(not(target_os = "windows"))]
    {
        vec!["/".to_string()]
    }
}

#[tauri::command]
async fn read_directory(dir_path: String) -> Vec<DirectoryItem> {
    let path = Path::new(&dir_path);
    let mut items = Vec::new();
    
    if let Ok(entries) = std::fs::read_dir(path) {
        for entry in entries.flatten() {
            if let Ok(metadata) = entry.metadata() {
                if let Some(name) = entry.file_name().to_str() {
                    items.push(DirectoryItem {
                        name: name.to_string(),
                        path: entry.path().to_string_lossy().to_string(),
                        is_directory: metadata.is_dir(),
                    });
                }
            }
        }
    }
    
    // Sort: directories first, then alphabetically
    items.sort_by(|a, b| {
        if a.is_directory && !b.is_directory {
            std::cmp::Ordering::Less
        } else if !a.is_directory && b.is_directory {
            std::cmp::Ordering::Greater
        } else {
            a.name.cmp(&b.name)
        }
    });
    
    items
}

#[tauri::command]
async fn stat_path(target_path: String) -> PathStat {
    let path = Path::new(&target_path);
    
    if let Ok(metadata) = std::fs::metadata(path) {
        PathStat {
            exists: true,
            is_directory: metadata.is_dir(),
            path: target_path,
        }
    } else {
        PathStat {
            exists: false,
            is_directory: false,
            path: target_path,
        }
    }
}

fn start_backend(app: &tauri::AppHandle) -> Result<Child, std::io::Error> {
    let backend_path = if cfg!(debug_assertions) {
        // Development mode
        app.path()
            .resolve("backend/main.py", tauri::path::BaseDirectory::Resource)
            .unwrap()
    } else {
        // Production mode
        app.path()
            .resolve("backend/main.exe", tauri::path::BaseDirectory::Resource)
            .unwrap()
    };

    let mut cmd = if cfg!(debug_assertions) {
        let mut c = Command::new("python");
        c.arg(backend_path);
        c
    } else {
        Command::new(backend_path)
    };

    cmd.stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let app_handle = app.handle().clone();
            
            // Start Python backend
            match start_backend(&app_handle) {
                Ok(mut child) => {
                    // Spawn a thread to monitor backend output
                    if let Some(stdout) = child.stdout.take() {
                        let handle = app_handle.clone();
                        std::thread::spawn(move || {
                            use std::io::{BufRead, BufReader};
                            let reader = BufReader::new(stdout);
                            
                            for line in reader.lines().flatten() {
                                println!("Backend: {}", line);
                                
                                // Detect port from Uvicorn startup message
                                if let Some(captures) = regex::Regex::new(r"Uvicorn running on .*?(\d{4,5})")
                                    .ok()
                                    .and_then(|re| re.captures(&line))
                                {
                                    if let Some(port_str) = captures.get(1) {
                                        if let Ok(port) = port_str.as_str().parse::<u16>() {
                                            println!("Detected backend port: {}", port);
                                            let _ = handle.emit("backend-port", BackendPortPayload { port });
                                        }
                                    }
                                }
                            }
                        });
                    }
                    
                    // Store the backend process
                    app.manage(BackendProcess(Mutex::new(Some(child))));
                }
                Err(e) => {
                    eprintln!("Failed to start backend: {}", e);
                }
            }
            
            Ok(())
        })
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            select_folders,
            open_file,
            show_file_in_folder,
            get_home_directory,
            get_drives,
            read_directory,
            stat_path
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
