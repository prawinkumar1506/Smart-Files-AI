"use client"

import { useState, useEffect } from "react"
import Sidebar from "./components/Sidebar"
import Dashboard from "./components/Dashboard"
import Search from "./components/Search"
import Query from "./components/Query"
import Folders from "./components/Folders"
import Files from "./components/Files"
import FileOrganiser from "./components/FileOrganiser"
import Settings from "./components/Settings"
import { ApiService } from "./services/api"
import "./App.css"

function App() {
const [isBackendReady, setIsBackendReady] = useState(false)
  const [currentView, setCurrentView] = useState("dashboard")
  const [currentTip, setCurrentTip] = useState(0)

  const tips = [
    "Tip: Add folders to start searching through your files",
    "AI-powered file organization and search",
    "Ask questions about your documents",
  ]

  useEffect(() => {
    const tipInterval = setInterval(() => {
      setCurrentTip((prevTip) => (prevTip + 1) % tips.length)
    }, 3000) // Change tip every 3 seconds

    return () => clearInterval(tipInterval)
  }, [])

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
        <div className="loading-logo">
          <img src="/smartfilesAI.png" alt="Smart Files AI" className="logo-image" />
        </div>
        <div className="loading-content">
          <h1>Smart Files AI</h1>
          <p>Your Files. Your AI. Your Privacy.</p>
          <div className="loading-bar-container">
            <div className="loading-bar">
              <div className="loading-bar-fill"></div>
            </div>
          </div>
<div className="loading-tips">
            <p key={currentTip} className="tip-item">
              {tips[currentTip]}
            </p>
          </div>
        </div>
      </div>
    )
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
