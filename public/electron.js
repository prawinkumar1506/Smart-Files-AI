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
    backendProcess = spawn(pythonExecutable, [backendPath]);
  } else {
    backendProcess = spawn(backendPath)
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
    properties: ["openDirectory", "multiSelections"],
    title: "Select folders to index",
  })

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
