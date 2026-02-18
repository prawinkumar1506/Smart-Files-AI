export {};

declare global {
  interface Window {
    electronAPI: {
      selectFolders: () => Promise<string[]>;
      openFile: (filePath: string) => Promise<{ success: boolean; error?: string }>;
      showFileInFolder: (filePath: string) => Promise<{ success: boolean; error?: string }>;
      showSaveDialog: (options: any) => Promise<any>;
      onMenuAddFolders: (callback: () => void) => void;
      removeAllListeners: (channel: string) => void;
      getHomeDirectory: () => Promise<string>;
      getDrives: () => Promise<string[]>;
      readDirectory: (dirPath: string) => Promise<Array<{ name: string; path: string; isDirectory: boolean }>>;
      statPath: (targetPath: string) => Promise<{ exists: boolean; isDirectory: boolean; path: string }>;
      onBackendPort: (callback: (event: any, port: number) => void) => void;
    };
  }
}
