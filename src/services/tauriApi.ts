import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

export interface FileOperationResult {
  success: boolean;
  error?: string;
}

export interface DirectoryItem {
  name: string;
  path: string;
  isDirectory: boolean;
}

interface DirectoryItemRaw {
  name: string;
  path: string;
  is_directory: boolean;
}

export interface PathStat {
  exists: boolean;
  isDirectory: boolean;
  path: string;
}

interface PathStatRaw {
  exists: boolean;
  is_directory: boolean;
  path: string;
}

export interface SystemTierInfo {
  tier: number;
  tier_name: string;
  ram_gb: number;
  cpu_cores: number;
  cpu_frequency_ghz: number;
  gpu_available: boolean;
  gpu_name?: string;
  vram_gb?: number;
  ollama_installed: boolean;
  recommended_models: string[];
  tier_description: string;
}

export const tauriAPI = {
  selectFolders: async (): Promise<string[]> => {
    return await invoke('select_folders');
  },

  openFile: async (filePath: string): Promise<FileOperationResult> => {
    return await invoke('open_file', { filePath });
  },

  showFileInFolder: async (filePath: string): Promise<FileOperationResult> => {
    return await invoke('show_file_in_folder', { filePath });
  },

  getHomeDirectory: async (): Promise<string> => {
    return await invoke('get_home_directory');
  },

  getDrives: async (): Promise<string[]> => {
    return await invoke('get_drives');
  },

  readDirectory: async (dirPath: string): Promise<DirectoryItem[]> => {
    const items = await invoke<DirectoryItemRaw[]>('read_directory', { dirPath });
    // Transform snake_case from Rust to match expected format
    return items.map(item => ({
      name: item.name,
      path: item.path,
      isDirectory: item.is_directory
    }));
  },

  statPath: async (targetPath: string): Promise<PathStat> => {
    const stat = await invoke<PathStatRaw>('stat_path', { targetPath });
    // Transform snake_case from Rust to match expected format
    return {
      exists: stat.exists,
      isDirectory: stat.is_directory,
      path: stat.path
    };
  },

  getSystemTier: async (): Promise<SystemTierInfo> => {
    return await invoke<SystemTierInfo>('get_system_tier');
  },

  downloadOllamaModel: async (model: string): Promise<string> => {
    return await invoke<string>('download_ollama_model', { model });
  },

  isOllamaModelInstalled: async (model: string): Promise<boolean> => {
    return await invoke<boolean>('is_ollama_model_installed', { model });
  },

  onBackendPort: (callback: (port: number) => void) => {
    listen<{ port: number }>('backend-port', (event) => {
      callback(event.payload.port);
    });
  },

  // Placeholder for compatibility
  onMenuAddFolders: (callback: () => void) => {
    // To be implemented with Tauri custom menu events if needed
    console.warn('onMenuAddFolders not yet implemented in Tauri');
  },

  removeAllListeners: (channel: string) => {
    // Tauri doesn't need this
    console.warn('removeAllListeners not needed in Tauri');
  },
};
