"use client"

import { useState, useEffect } from "react"
import Sidebar from "./components/Sidebar"
import Dashboard from "./components/Dashboard"
import Search from "./components/Search"
import Query from "./components/Query"
import Folders from "./components/Folders"
import Files from "./components/Files"
import Settings from "./components/Settings"
import { ApiService } from "./services/api"
import "./App.css"

function App() {
  const [isBackendReady, setIsBackendReady] = useState(false)
  const [currentView, setCurrentView] = useState("dashboard")

  useEffect(() => {
    checkBackendHealth()

    // Listen for menu events from Electron
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

  const checkBackendHealth = async () => {
    try {
      await ApiService.healthCheck()
      setIsBackendReady(true)
    } catch (error) {
      console.error("Backend not ready:", error)
      // Retry after 2 seconds
      setTimeout(checkBackendHealth, 2000)
    }
  }

  if (!isBackendReady) {
    return (
        <div className="app-loading">
          <div className="loading-spinner"></div>
          <p>Starting SmartFile AI...</p>
        </div>
    )
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case "search":
        return <Search />
      case "query":
        return <Query />
      case "folders":
        return <Folders />
      case "files":
        return <Files />
      case "settings":
        return <Settings />
      default:
        return <Dashboard />
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
