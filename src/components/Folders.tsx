"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Folder, Plus, Trash2, RefreshCw, AlertCircle, FolderOpen, Files, Clock, BarChart3, Upload } from "lucide-react"
import { ApiService } from "../services/api"
import FolderPicker from "./FolderPicker"

interface FolderInfo {
  id: number
  path: string
  name: string
  file_count: number
  last_indexed: string
}

const Folders: React.FC = () => {
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isIndexing, setIsIndexing] = useState(false)
  const [selectedFolder, setSelectedFolder] = useState<FolderInfo | null>(null)
  const [showAnalytics, setShowAnalytics] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [showFolderPicker, setShowFolderPicker] = useState(false)

  useEffect(() => {
    loadFolders()
  }, [])

  const loadFolders = async () => {
    try {
      const foldersData = await ApiService.getFolders()
      // Add name property for easier display
      const foldersWithNames = foldersData.map((f: FolderInfo) => ({
        ...f,
        name: f.path.split(/[\\/]/).pop() || f.path
      }))
      setFolders(foldersWithNames)
    } catch (error) {
      console.error("Error loading folders:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddFolders = async () => {
    if (!window.electronAPI) {
      alert("Folder selection is only available in the desktop app")
      return
    }

    setShowFolderPicker(true)
  }

  const handleFoldersSelected = async (selectedPaths: string[]) => {
    setShowFolderPicker(false)

    if (selectedPaths && selectedPaths.length > 0) {
      setIsIndexing(true)

      try {
        await ApiService.indexFolders({
          folder_paths: selectedPaths,
        })

        // Refresh the folders list
        setTimeout(() => {
          loadFolders()
          setIsIndexing(false)
        }, 1000)
      } catch (error) {
        console.error("Error indexing folders:", error)
        setIsIndexing(false)
      }
    }
  }

  const handleFolderPickerCancel = () => {
    setShowFolderPicker(false)
  }

  const handleRemoveFolder = async (folderId: number, folderPath: string) => {
    if (!confirm(`Are you sure you want to remove "${folderPath}" from the index?`)) {
      return
    }

    try {
      await ApiService.removeFolder(folderId)
      setFolders(folders.filter((f) => f.id !== folderId))
      if (selectedFolder?.id === folderId) {
        setSelectedFolder(null)
        setShowAnalytics(false)
      }
    } catch (error) {
      console.error("Error removing folder:", error)
      alert("Error removing folder. Please try again.")
    }
  }

  const handleClearAll = async () => {
    if (!confirm("Are you sure you want to clear the entire index? This cannot be undone.")) {
      return
    }

    try {
      await ApiService.clearIndex()
      setFolders([])
      setSelectedFolder(null)
      setShowAnalytics(false)
    } catch (error) {
      console.error("Error clearing index:", error)
      alert("Error clearing index. Please try again.")
    }
  }

  const getStatus = (folder: FolderInfo) => {
    const hoursSinceIndexed = (Date.now() - new Date(folder.last_indexed).getTime()) / (1000 * 60 * 60)
    if (hoursSinceIndexed < 1) return 'processing'
    if (hoursSinceIndexed < 24) return 'active'
    return 'indexed'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    // In Electron, you'd handle folder drops here
    console.log('Drop event:', e.dataTransfer.files)
  }

  if (isLoading) {
    return (
      <div className="folders-page">
        <div className="loading-state">
          <RefreshCw className="spinning" size={24} />
          <p>Loading folders...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="folders-page-modern">
      <div className="folders-header">
<div className="folders-header-content">
          <div className="folders-header-logo">
            <img src="/smartfilesAI.png" alt="Smart Files AI" className="logo-image logo-glow" />
          </div>
          <div className="folders-header-text">
            <h1 className="gradient-text">Manage Folders</h1>
            <p className="subtitle-text">Organize and monitor your indexed folders</p>
          </div>
        </div>
      </div>

      <div className="folders-actions-modern">
        <button className="add-folders-btn-modern gradient-bg-blue" onClick={handleAddFolders} disabled={isIndexing}>
          <Plus size={20} />
          {isIndexing ? "Indexing..." : "Add Folders"}
        </button>

        {folders.length > 0 && (
          <button className="clear-all-btn-modern" onClick={handleClearAll} disabled={isIndexing}>
            <Trash2 size={20} />
            Clear All
          </button>
        )}
      </div>

      {isIndexing && (
        <div className="indexing-notice glassmorphic">
          <AlertCircle size={20} />
          <div>
            <strong>Indexing in progress</strong>
            <p>Processing your files with AI. This may take a few minutes.</p>
          </div>
        </div>
      )}

      {folders.length === 0 ? (
        <div 
          className={`drop-zone-modern glassmorphic ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="drop-zone-content">
            <div className="illustration-circle pulse">
              <Upload size={64} />
            </div>
            <h3>Drag & Drop Folders Here</h3>
            <p>Or click the button below to browse</p>
            <button className="add-first-folder-btn gradient-bg-blue" onClick={handleAddFolders}>
              <Plus size={20} />
              Add Your First Folder
            </button>
          </div>
        </div>
      ) : (
        <div className="folders-table-container glassmorphic">
          <table className="folders-table-modern">
            <thead>
              <tr>
                <th>Folder</th>
                <th>Files</th>
                <th>Last Indexed</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {folders.map((folder) => (
                <tr key={folder.id} className="folder-row-modern hover-lift">
                  <td className="folder-cell">
                    <div className="folder-cell-content">
                      <div className="folder-icon-wrapper gradient-bg-blue">
                        <FolderOpen size={20} />
                      </div>
                      <div className="folder-text">
                        <div className="folder-name-text">{folder.name}</div>
                        <div className="folder-path-text">{folder.path}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div className="file-count-badge">
                      <Files size={14} />
                      {folder.file_count.toLocaleString()}
                    </div>
                  </td>
                  <td>
                    <div className="date-cell">
                      <Clock size={14} />
                      {new Date(folder.last_indexed).toLocaleString()}
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge status-${getStatus(folder)}`}>
                      {getStatus(folder) === 'processing' ? '🟡 Processing' : 
                       getStatus(folder) === 'active' ? '🟢 Active' : '🟢 Indexed'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button 
                        className="analytics-btn-small"
                        onClick={() => {
                          setSelectedFolder(folder)
                          setShowAnalytics(true)
                        }}
                      >
                        <BarChart3 size={16} />
                      </button>
                      <button 
                        className="delete-btn-small"
                        onClick={() => handleRemoveFolder(folder.id, folder.path)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Analytics Modal */}
      {showAnalytics && selectedFolder && (
        <div className="modal-overlay" onClick={() => setShowAnalytics(false)}>
          <div className="analytics-modal glassmorphic" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-modern">
              <h3>Folder Analytics</h3>
              <button className="close-btn-modern" onClick={() => setShowAnalytics(false)}>
                ×
              </button>
            </div>
            <div className="modal-content-modern">
              <div className="analytics-header">
                <div className="folder-icon-large gradient-bg-purple">
                  <FolderOpen size={48} />
                </div>
                <div>
                  <h4>{selectedFolder.name}</h4>
                  <p className="folder-path-small">{selectedFolder.path}</p>
                </div>
              </div>

              <div className="analytics-grid">
                <div className="analytic-card">
                  <div className="analytic-icon gradient-bg-blue">
                    <Files size={24} />
                  </div>
                  <div className="analytic-info">
                    <h5>Total Files</h5>
                    <div className="analytic-value">{selectedFolder.file_count.toLocaleString()}</div>
                  </div>
                </div>

                <div className="analytic-card">
                  <div className="analytic-icon gradient-bg-green">
                    <Clock size={24} />
                  </div>
                  <div className="analytic-info">
                    <h5>Last Indexed</h5>
                    <div className="analytic-value-small">
                      {new Date(selectedFolder.last_indexed).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                <div className="analytic-card">
                  <div className="analytic-icon gradient-bg-orange">
                    <BarChart3 size={24} />
                  </div>
                  <div className="analytic-info">
                    <h5>Status</h5>
                    <span className={`status-badge status-${getStatus(selectedFolder)}`}>
                      {getStatus(selectedFolder) === 'processing' ? 'Processing' : 
                       getStatus(selectedFolder) === 'active' ? 'Active' : 'Indexed'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="file-type-breakdown">
                <h4>File Type Breakdown</h4>
                <div className="breakdown-chart">
                  <div className="chart-bar">
                    <div className="chart-segment" style={{ width: '40%', background: '#3b82f6' }}></div>
                    <div className="chart-segment" style={{ width: '30%', background: '#8b5cf6' }}></div>
                    <div className="chart-segment" style={{ width: '20%', background: '#10b981' }}></div>
                    <div className="chart-segment" style={{ width: '10%', background: '#f59e0b' }}></div>
                  </div>
                  <div className="chart-legend">
                    <div className="legend-item">
                      <span className="legend-color" style={{ background: '#3b82f6' }}></span>
                      <span>Documents (40%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-color" style={{ background: '#8b5cf6' }}></span>
                      <span>Images (30%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-color" style={{ background: '#10b981' }}></span>
                      <span>Code (20%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-color" style={{ background: '#f59e0b' }}></span>
                      <span>Other (10%)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {showFolderPicker && (
        <FolderPicker 
          onSelect={handleFoldersSelected}
          onCancel={handleFolderPickerCancel}
        />
      )}
    </div>
  )
}

export default Folders
