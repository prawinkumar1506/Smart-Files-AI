// const { app, BrowserWindow, dialog, ipcMain, Menu } = require("electron")
// const path = require("path")
// const isDev = require("electron-is-dev")
// const { spawn } = require("child_process")
//
// let mainWindow
// let backendProcess
//
// function createWindow() {
//   mainWindow = new BrowserWindow({
//     width: 1200,
//     height: 800,
//     webPreferences: {
//       nodeIntegration: false,
//       contextIsolation: true,
//       enableRemoteModule: false,
//       preload: path.join(__dirname, "preload.js"),
//     },
//     titleBarStyle: "hiddenInset",
//     show: false,
//   })
//
//   const startUrl = isDev ? "http://localhost:3000" : `file://${path.join(__dirname, "../build/index.html")}`
//
//   mainWindow.loadURL(startUrl)
//
//   mainWindow.once("ready-to-show", () => {
//     mainWindow.show()
//   })
//
//   mainWindow.on("closed", () => {
//     mainWindow = null
//   })
//
//   // Start Python backend
//   startBackend()
// }
//
// function startBackend() {
//   const backendPath = isDev
//       ? path.join(__dirname, "../backend/main.py")
//       : path.join(process.resourcesPath, "backend", "main.exe")
//
//   if (isDev) {
//     backendProcess = spawn("python", [backendPath]);
//   } else {
//     backendProcess = spawn(backendPath);
//   }
//
//   // Capture backend output and detect port
//   backendProcess.stdout.on("data", (data) => {
//     const output = data.toString();
//     console.log(`Backend: ${output}`);
//
//     // Detect port from Uvicorn startup message
//     const portMatch = /Uvicorn running on .*?(\d{4,5})/.exec(output);
//     if (portMatch) {
//       const port = portMatch[1];
//       console.log(`Detected backend port: ${port}`);
//
//       // Notify renderer process
//       if (mainWindow) {
//         mainWindow.webContents.send('backend-port', port);
//       }
//     }
//   });
//
//   backendProcess.stderr.on("data", (data) => {
//     console.error(`Backend Error: ${data}`)
//   })
// }
//
// // ... rest of IPC handlers and menu setup remains unchanged ...
//
// // IPC handlers
// ipcMain.handle("select-folders", async () => {
//   const result = await dialog.showOpenDialog(mainWindow, {
//     properties: ["openDirectory", "multiSelections"],
//     title: "Select folders to index",
//   })
//
//   return result.filePaths
// })
//
// ipcMain.handle("show-save-dialog", async (event, options) => {
//   const result = await dialog.showSaveDialog(mainWindow, options)
//   return result
// })
// ipcMain.handle('update-backend-port', (_, port) => {
//   mainWindow.webContents.send('backend-port', port);
// });
//
// app.whenReady().then(createWindow)
//
// app.on("window-all-closed", () => {
//   if (backendProcess) {
//     backendProcess.kill()
//   }
//   if (process.platform !== "darwin") {
//     app.quit()
//   }
// })
//
// app.on("activate", () => {
//   if (BrowserWindow.getAllWindows().length === 0) {
//     createWindow()
//   }
// })
//
// // Create application menu
// const template = [
//   {
//     label: "File",
//     submenu: [
//       {
//         label: "Add Folders",
//         accelerator: "CmdOrCtrl+O",
//         click: () => {
//           mainWindow.webContents.send("menu-add-folders")
//         },
//       },
//       { type: "separator" },
//       {
//         label: "Quit",
//         accelerator: process.platform === "darwin" ? "Cmd+Q" : "Ctrl+Q",
//         click: () => {
//           app.quit()
//         },
//       },
//     ],
//   },
//   {
//     label: "Edit",
//     submenu: [
//       { role: "undo" },
//       { role: "redo" },
//       { type: "separator" },
//       { role: "cut" },
//       { role: "copy" },
//       { role: "paste" },
//     ],
//   },
//   {
//     label: "View",
//     submenu: [
//       { role: "reload" },
//       { role: "forceReload" },
//       { role: "toggleDevTools" },
//       { type: "separator" },
//       { role: "resetZoom" },
//       { role: "zoomIn" },
//       { role: "zoomOut" },
//       { type: "separator" },
//       { role: "togglefullscreen" },
//     ],
//   },
// ]
//
// Menu.setApplicationMenu(Menu.buildFromTemplate(template))


const { app, BrowserWindow, dialog, ipcMain, Menu, shell } = require("electron")
const path = require("path")
const isDev = require("electron-is-dev")
const { spawn } = require("child_process")

let mainWindow
let backendProcess

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, "preload.js"),
    },
    titleBarStyle: "hiddenInset",
    show: false,
  })

  const startUrl = isDev ? "http://localhost:3000" : `file://${path.join(__dirname, "../build/index.html")}`

  mainWindow.loadURL(startUrl)

  mainWindow.once("ready-to-show", () => {
    mainWindow.show()
  })

  mainWindow.on("closed", () => {
    mainWindow = null
  })

  // Start Python backend
  startBackend()
}

function startBackend() {
  const backendPath = isDev
      ? path.join(__dirname, "../backend/main.py")
      : path.join(process.resourcesPath, "backend", "main.exe")

  if (isDev) {
    const pythonExecutable = path.join(__dirname, "../backend/venv/Scripts/python.exe");
    backendProcess = spawn("python", [backendPath]);

  } else {
    backendProcess = spawn("python", [backendPath]);

  }

  backendProcess.stdout.on("data", (data) => {
    const output = data.toString();
    console.log(`Backend: ${output}`);

    // Detect port from Uvicorn startup message
    const portMatch = /Uvicorn running on .*?(\d{4,5})/.exec(output);
    if (portMatch) {
      const port = portMatch[1];
      console.log(`Detected backend port: ${port}`);

      // Notify renderer process
      if (mainWindow) {
        mainWindow.webContents.send('backend-port', port);
      }
    }
  });

  backendProcess.stderr.on("data", (data) => {
    console.error(`Backend Error: ${data}`)
  })
}

// IPC handlers  
ipcMain.handle("select-folders", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openFile", "multiSelections"],
    title: "Select files (folder will be indexed)",
  })
  
  // Extract unique parent directories from selected files
  if (result.filePaths && result.filePaths.length > 0) {
    const path = require("path")
    const uniqueFolders = [...new Set(result.filePaths.map(filePath => path.dirname(filePath)))]
    return uniqueFolders
  }

  return result.filePaths
})

ipcMain.handle("open-file", async (event, filePath) => {
  try {
    await shell.openPath(filePath)
    return { success: true }
  } catch (error) {
    console.error("Error opening file:", error)
    return { success: false, error: error.message }
  }
})

ipcMain.handle("show-file-in-folder", async (event, filePath) => {
  try {
    shell.showItemInFolder(filePath)
    return { success: true }
  } catch (error) {
    console.error("Error showing file in folder:", error)
    return { success: false, error: error.message }
  }
})

ipcMain.handle("show-save-dialog", async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options)
  return result
})

ipcMain.handle('update-backend-port', (_, port) => {
  mainWindow.webContents.send('backend-port', port);
});

// Custom folder picker handlers
ipcMain.handle("get-home-directory", async () => {
  return app.getPath("home")
})

ipcMain.handle("get-drives", async () => {
  const fs = require("fs")
  if (process.platform === "win32") {
    const drives = []
    for (let code = 65; code <= 90; code += 1) {
      const drive = `${String.fromCharCode(code)}:\\`
      if (fs.existsSync(drive)) {
        drives.push(drive)
      }
    }
    return drives
  }

  return ["/"]
})

ipcMain.handle("read-directory", async (event, dirPath) => {
  const fs = require("fs").promises
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true })
    const items = await Promise.all(
      entries.map(async (entry) => {
        const fullPath = path.join(dirPath, entry.name)
        try {
          return {
            name: entry.name,
            path: fullPath,
            isDirectory: entry.isDirectory(),
          }
        } catch (error) {
          return null
        }
      })
    )
    // Filter out null entries (permission errors) and sort: directories first
    return items
      .filter(item => item !== null)
      .sort((a, b) => {
        if (a.isDirectory && !b.isDirectory) return -1
        if (!a.isDirectory && b.isDirectory) return 1
        return a.name.localeCompare(b.name)
      })
  } catch (error) {
    console.error("Error reading directory:", error)
    return []
  }
})

ipcMain.handle("stat-path", async (event, targetPath) => {
  const fs = require("fs").promises
  try {
    const stats = await fs.stat(targetPath)
    return {
      exists: true,
      isDirectory: stats.isDirectory(),
      path: targetPath,
    }
  } catch (error) {
    return { exists: false, isDirectory: false, path: targetPath }
  }
})

app.whenReady().then(createWindow)

app.on("window-all-closed", () => {
  if (backendProcess) {
    backendProcess.kill()
  }
  if (process.platform !== "darwin") {
    app.quit()
  }
})

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// Create application menu
const template = [
  {
    label: "File",
    submenu: [
      {
        label: "Add Folders",
        accelerator: "CmdOrCtrl+O",
        click: () => {
          mainWindow.webContents.send("menu-add-folders")
        },
      },
      { type: "separator" },
      {
        label: "Quit",
        accelerator: process.platform === "darwin" ? "Cmd+Q" : "Ctrl+Q",
        click: () => {
          app.quit()
        },
      },
    ],
  },
  {
    label: "Edit",
    submenu: [
      { role: "undo" },
      { role: "redo" },
      { type: "separator" },
      { role: "cut" },
      { role: "copy" },
      { role: "paste" },
    ],
  },
  {
    label: "View",
    submenu: [
      { role: "reload" },
      { role: "forceReload" },
      { role: "toggleDevTools" },
      { type: "separator" },
      { role: "resetZoom" },
      { role: "zoomIn" },
      { role: "zoomOut" },
      { type: "separator" },
      { role: "togglefullscreen" },
    ],
  },
]

Menu.setApplicationMenu(Menu.buildFromTemplate(template))
