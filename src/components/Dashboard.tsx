"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { ApiService } from "../services/api"
import { Files, Folder, Clock, Activity } from "lucide-react"

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

const Dashboard: React.FC = () => {
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [stats, setStats] = useState({
    totalFolders: 0,
    totalFiles: 0,
    lastIndexed: null as string | null,
  })

  useEffect(() => {
    loadDashboardData()

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
      const totalFiles = foldersData.reduce((sum, folder) => sum + folder.file_count, 0)
      const lastIndexed =
        foldersData.length > 0
          ? foldersData.reduce((latest, folder) =>
              new Date(folder.last_indexed) > new Date(latest) ? folder.last_indexed : latest,
            )
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

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Overview of your indexed files and system status</p>
      </div>

      {indexStatus?.is_indexing && (
        <div className="indexing-status">
          <div className="status-header">
            <Activity className="spinning" size={20} />
            <h3>Indexing in Progress</h3>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${indexStatus.progress}%` }}></div>
          </div>
          <p className="progress-text">
            {indexStatus.progress}% - {indexStatus.current_file}
          </p>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <Folder size={24} />
          </div>
          <div className="stat-content">
            <h3>{stats.totalFolders}</h3>
            <p>Indexed Folders</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Files size={24} />
          </div>
          <div className="stat-content">
            <h3>{stats.totalFiles}</h3>
            <p>Total Files</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Clock size={24} />
          </div>
          <div className="stat-content">
            <h3>{stats.lastIndexed ? new Date(stats.lastIndexed).toLocaleDateString() : "Never"}</h3>
            <p>Last Indexed</p>
          </div>
        </div>
      </div>

      <div className="recent-folders">
        <h2>Recent Folders</h2>
        {folders.length === 0 ? (
          <div className="empty-state">
            <Folder size={48} />
            <h3>No folders indexed yet</h3>
            <p>Add some folders to get started with SmartFile AI</p>
          </div>
        ) : (
          <div className="folders-list">
            {folders.slice(0, 5).map((folder) => (
              <div key={folder.id} className="folder-item">
                <Folder size={20} />
                <div className="folder-info">
                  <h4>{folder.path}</h4>
                  <p>
                    {folder.file_count} files • Last indexed {new Date(folder.last_indexed).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
