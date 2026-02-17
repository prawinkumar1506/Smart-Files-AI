"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { ApiService } from "../services/api"
import { Files, Folder, Clock, Activity, Plus, RefreshCw, Sparkles, TrendingUp, Database, Zap, Check, FolderOpen } from "lucide-react"

interface IndexStatus {
  is_indexing: boolean
  progress: number
  current_file: string
}

interface FolderInfo {
  id: number
  path: string
  file_count: number
  last_indexed: string
}

interface ActivityItem {
  id: number
  type: 'indexed' | 'classified' | 'processed'
  message: string
  timestamp: Date
}

const Dashboard: React.FC = () => {
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([])
  const [stats, setStats] = useState({
    totalFolders: 0,
    totalFiles: 0,
    lastIndexed: null as string | null,
  })

  useEffect(() => {
    loadDashboardData()
    loadRecentActivity()

    // Poll for index status if indexing is in progress
    const interval = setInterval(() => {
      if (indexStatus?.is_indexing) {
        loadIndexStatus()
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [indexStatus?.is_indexing])

  const loadDashboardData = async () => {
    try {
      const [statusData, foldersData] = await Promise.all([ApiService.getIndexStatus(), ApiService.getFolders()])

      setIndexStatus(statusData)
      setFolders(foldersData)

      // Calculate stats
      const totalFiles = foldersData.reduce((sum: number, folder: FolderInfo) => sum + folder.file_count, 0)
      const lastIndexed =
        foldersData.length > 0
          ? foldersData.reduce((latest: string, folder: FolderInfo) => {
              const latestDate = new Date(latest);
              const folderDate = new Date(folder.last_indexed);
              return folderDate > latestDate ? folder.last_indexed : latest;
            }, foldersData[0].last_indexed)
          : null

      setStats({
        totalFolders: foldersData.length,
        totalFiles,
        lastIndexed,
      })
    } catch (error) {
      console.error("Error loading dashboard data:", error)
    }
  }

  const loadIndexStatus = async () => {
    try {
      const status = await ApiService.getIndexStatus()
      setIndexStatus(status)
    } catch (error) {
      console.error("Error loading index status:", error)
    }
  }

  const loadRecentActivity = () => {
    // Generate mock recent activity based on folders
    const activities: ActivityItem[] = folders.slice(0, 5).map((folder, index) => ({
      id: index,
      type: index % 3 === 0 ? 'indexed' : index % 3 === 1 ? 'classified' : 'processed',
      message: `${folder.file_count} files ${index % 3 === 0 ? 'indexed' : index % 3 === 1 ? 'classified' : 'processed'} in ${folder.path.split(/[\\/]/).pop()}`,
      timestamp: new Date(folder.last_indexed)
    }))
    setRecentActivity(activities)
  }

  const handleAddFolders = async () => {
    if (!window.electronAPI) {
      alert("Folder selection is only available in the desktop app")
      return
    }

    try {
      const selectedPaths = await window.electronAPI.selectFolders()
      if (selectedPaths && selectedPaths.length > 0) {
        await ApiService.indexFolders({ folder_paths: selectedPaths })
        setTimeout(() => loadDashboardData(), 1000)
      }
    } catch (error) {
      console.error("Error adding folders:", error)
    }
  }

  const handleReindex = async () => {
    try {
      // Trigger reindexing for all folders
      const folderPaths = folders.map(f => f.path)
      if (folderPaths.length > 0) {
        await ApiService.indexFolders({ folder_paths: folderPaths })
        setTimeout(() => loadDashboardData(), 1000)
      }
    } catch (error) {
      console.error("Error reindexing:", error)
    }
  }

  const calculateIndexingProgress = () => {
    if (folders.length === 0) return 0
    return Math.min(100, (stats.totalFiles / (folders.length * 100)) * 100)
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="dashboard-header-content">
          <div className="dashboard-header-logo">
            <img src="/smartfilesAI.png" alt="Smart Files AI" className="logo-image logo-glow" />
          </div>
          <div className="dashboard-header-text">
            <h1 className="gradient-text">Dashboard</h1>
            <p className="subtitle-text">AI-powered insights for your files</p>
          </div>
        </div>
      </div>

      {indexStatus?.is_indexing && (
        <div className="indexing-status glassmorphic">
          <div className="status-header">
            <Activity className="spinning" size={20} />
            <h3>AI Processing Files</h3>
          </div>
          <div className="progress-bar-modern">
            <div className="progress-fill-animated" style={{ width: `${indexStatus.progress}%` }}></div>
          </div>
          <p className="progress-text">
            {indexStatus.progress}% - {indexStatus.current_file}
          </p>
        </div>
      )}

      {/* Enhanced Stats Grid with Progress Bars and Mini Charts */}
      <div className="stats-grid-modern">
        <div className="stat-card-modern hover-lift">
          <div className="stat-header">
            <div className="stat-icon-modern gradient-bg-blue">
              <Folder size={24} />
            </div>
            <div className="stat-badge">+{folders.length > 0 ? '100%' : '0%'}</div>
          </div>
          <div className="stat-content-modern">
            <h3 className="stat-number">{stats.totalFolders}</h3>
            <p className="stat-label">Indexed Folders</p>
            <div className="stat-progress">
              <div className="stat-progress-bar">
                <div className="stat-progress-fill gradient-bg-blue" style={{ width: `${Math.min(100, stats.totalFolders * 20)}%` }}></div>
              </div>
              <span className="stat-progress-text">{Math.min(100, stats.totalFolders * 20)}%</span>
            </div>
          </div>
        </div>

        <div className="stat-card-modern hover-lift">
          <div className="stat-header">
            <div className="stat-icon-modern gradient-bg-purple">
              <Files size={24} />
            </div>
            <div className="stat-badge">
              <TrendingUp size={12} />
            </div>
          </div>
          <div className="stat-content-modern">
            <h3 className="stat-number">{stats.totalFiles.toLocaleString()}</h3>
            <p className="stat-label">Total Files Indexed</p>
            <div className="stat-progress">
              <div className="stat-progress-bar">
                <div className="stat-progress-fill gradient-bg-purple" style={{ width: `${calculateIndexingProgress()}%` }}></div>
              </div>
              <span className="stat-progress-text">{Math.round(calculateIndexingProgress())}%</span>
            </div>
          </div>
        </div>

        <div className="stat-card-modern hover-lift">
          <div className="stat-header">
            <div className="stat-icon-modern gradient-bg-green">
              <Database size={24} />
            </div>
            <div className="stat-badge status-active">
              <Check size={12} /> Active
            </div>
          </div>
          <div className="stat-content-modern">
            <h3 className="stat-number">{stats.lastIndexed ? new Date(stats.lastIndexed).toLocaleDateString() : "Never"}</h3>
            <p className="stat-label">Last Indexed</p>
            <div className="stat-mini-chart">
              <div className="mini-bar" style={{ height: '40%' }}></div>
              <div className="mini-bar" style={{ height: '65%' }}></div>
              <div className="mini-bar" style={{ height: '45%' }}></div>
              <div className="mini-bar" style={{ height: '80%' }}></div>
              <div className="mini-bar" style={{ height: '95%' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="dashboard-two-column">
        {/* Left Column: Quick Actions */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Quick Actions</h2>
            <Sparkles size={20} className="sparkle-icon" />
          </div>
          <div className="quick-actions-grid">
            <button className="action-card hover-lift gradient-bg-blue" onClick={handleAddFolders}>
              <div className="action-icon">
                <Plus size={24} />
              </div>
              <div className="action-content">
                <h3>Add Folder</h3>
                <p>Index new folders</p>
              </div>
            </button>

            <button className="action-card hover-lift gradient-bg-purple" onClick={handleReindex}>
              <div className="action-icon">
                <RefreshCw size={24} />
              </div>
              <div className="action-content">
                <h3>Reindex All</h3>
                <p>Refresh index</p>
              </div>
            </button>

            <button className="action-card hover-lift gradient-bg-green" onClick={() => {}}>
              <div className="action-icon">
                <Sparkles size={24} />
              </div>
              <div className="action-content">
                <h3>AI Organize</h3>
                <p>Auto-organize files</p>
              </div>
            </button>

            <button className="action-card hover-lift gradient-bg-orange">
              <div className="action-icon">
                <Zap size={24} />
              </div>
              <div className="action-content">
                <h3>Smart Search</h3>
                <p>AI-powered search</p>
              </div>
            </button>
          </div>
        </div>

        {/* Right Column: Recent Activity */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recent Activity</h2>
            <Activity size={20} />
          </div>
          <div className="activity-timeline">
            {recentActivity.length === 0 && folders.length === 0 ? (
              <div className="activity-empty">
                <Activity size={32} className="empty-icon" />
                <p>No recent activity</p>
                <span>Add folders to see activity</span>
              </div>
            ) : (
              folders.slice(0, 5).map((folder, index) => (
                <div key={folder.id} className="activity-item">
                  <div className={`activity-icon ${index % 3 === 0 ? 'bg-blue' : index % 3 === 1 ? 'bg-purple' : 'bg-green'}`}>
                    {index % 3 === 0 ? <Database size={16} /> : index % 3 === 1 ? <Sparkles size={16} /> : <Check size={16} />}
                  </div>
                  <div className="activity-content">
                    <h4>{index % 3 === 0 ? 'Folder Indexed' : index % 3 === 1 ? 'Files Classified' : 'AI Processed'}</h4>
                    <p>{folder.file_count} files in {folder.path.split(/[\\/]/).pop()}</p>
                    <span className="activity-time">{new Date(folder.last_indexed).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Folders Section */}
      {folders.length === 0 ? (
        <div className="empty-state-modern glassmorphic">
          <div className="empty-illustration">
            <div className="illustration-circle pulse">
              <Folder size={64} />
            </div>
          </div>
          <h3>Let's Get Started!</h3>
          <p>Add folders to unlock the power of AI-driven file management</p>
          <button className="cta-button gradient-bg-blue" onClick={handleAddFolders}>
            <Plus size={20} />
            Add Your First Folder
          </button>
        </div>
      ) : (
        <div className="recent-folders-modern">
          <h2>Recent Folders</h2>
          <div className="folders-grid">
            {folders.slice(0, 6).map((folder) => (
              <div key={folder.id} className="folder-card-modern hover-lift">
                <div className="folder-icon-wrapper">
                  <FolderOpen size={32} className="folder-icon" />
                </div>
                <div className="folder-info">
                  <h4>{folder.path.split(/[\\/]/).pop()}</h4>
                  <p className="folder-path">{folder.path}</p>
                  <div className="folder-stats">
                    <span className="folder-stat">
                      <Files size={14} />
                      {folder.file_count} files
                    </span>
                    <span className="folder-stat">
                      <Clock size={14} />
                      {new Date(folder.last_indexed).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
