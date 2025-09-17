"use client"

import type React from "react"
import { Search, MessageSquare, Folder, Settings, Home, File, Sparkles } from "lucide-react"

interface SidebarProps {
  currentView: string
  onViewChange: (view: string) => void
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: Home },
    { id: "search", label: "Search Files", icon: Search },
    { id: "query", label: "Ask Question", icon: MessageSquare },
    { id: "organiser", label: "File Organiser", icon: Sparkles },
    { id: "folders", label: "Manage Folders", icon: Folder },
    { id: "files", label: "Browse Files", icon: File },
    { id: "settings", label: "Settings", icon: Settings },
  ]

  return (
    <div className="sidebar">
      <div className="sidebar-header">
<div className="sidebar-logo">
          <img src="/smartfilesAI.png" alt="Smart Files AI" className="logo-image" />
        </div>
        <div className="sidebar-title">
          <h1>Smart Files AI</h1>
          <p>Your Files. Your AI. Your Privacy.</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              className={`nav-item ${currentView === item.id ? "active" : ""}`}
              onClick={() => onViewChange(item.id)}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>
    </div>
  )
}

export default Sidebar
