// const { contextBridge, ipcRenderer } = require("electron")
//
// contextBridge.exposeInMainWorld("electronAPI", {
//   // IPC methods
//   selectFolders: () => ipcRenderer.invoke("select-folders"),
//   showSaveDialog: (options) => ipcRenderer.invoke("show-save-dialog", options),
//   onMenuAddFolders: (callback) => ipcRenderer.on("menu-add-folders", callback),
//   removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),
//
//   // Port communication
//   onBackendPort: (callback) => ipcRenderer.on('backend-port', callback)
// });


const { contextBridge, ipcRenderer } = require("electron")

contextBridge.exposeInMainWorld("electronAPI", {
  selectFolders: () => ipcRenderer.invoke("select-folders"),
  openFile: (filePath) => ipcRenderer.invoke("open-file", filePath),
  showFileInFolder: (filePath) => ipcRenderer.invoke("show-file-in-folder", filePath),
  showSaveDialog: (options) => ipcRenderer.invoke("show-save-dialog", options),
  onMenuAddFolders: (callback) => ipcRenderer.on("menu-add-folders", callback),
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),

  // Port communication
  onBackendPort: (callback) => ipcRenderer.on('backend-port', callback)
})
