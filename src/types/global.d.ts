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
      onBackendPort: (callback: (event: any, port: number) => void) => void;
    };
  }
}
