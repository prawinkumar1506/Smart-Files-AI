"use client"

import { useState, useEffect } from "react"
import { SplashScreen } from "./components/SplashScreen"
import Sidebar from "./components/Sidebar"
import Dashboard from "./components/Dashboard"
import Search from "./components/Search"
import Query from "./components/Query"
import Folders from "./components/Folders"
import Files from "./components/Files"
import FileOrganiser from "./components/FileOrganiser"
import Settings from "./components/Settings"
import SmartImages from "./components/SmartImages"
import { ApiService } from "./services/api"
import "./App.css"
import "./ModernEnhancements.css"

function App() {
  const [isBackendReady, setIsBackendReady] = useState(false)
  const [currentView, setCurrentView] = useState("dashboard")

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health', { 
        method: 'GET',
        signal: AbortSignal.timeout(2000)
      })
      if (response.ok) {
        setIsBackendReady(true)
      } else {
        setTimeout(checkBackendHealth, 1000)
      }
    } catch (error) {
      console.error("Backend not ready:", error)
      setTimeout(checkBackendHealth, 500)
    }
  }

  useEffect(() => {
    checkBackendHealth()

    if (window.electronAPI) {
      window.electronAPI.onMenuAddFolders(() => {
        setCurrentView("folders")
      })
    }

    return () => {
      if (window.electronAPI) {
        window.electronAPI.removeAllListeners("menu-add-folders")
      }
    }
  }, [])

  if (!isBackendReady) {
    return <SplashScreen />
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case "search":
        return <Search />
      case "query":
        return <Query />
      case "organiser":
        return <FileOrganiser />
      case "folders":
        return <Folders />
    case "files":
        return <Files />
    case "images":
        return <SmartImages />
    case "settings":
        return <Settings />
      default:
        return <Dashboard onViewChange={setCurrentView} />
    }
  }

  return (
    <div className="app">
      <Sidebar currentView={currentView} onViewChange={setCurrentView} />
      <main className="main-content">{renderCurrentView()}</main>
    </div>
  )
}

export default App
