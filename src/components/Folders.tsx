"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Folder, Plus, Trash2, RefreshCw, AlertCircle } from "lucide-react"
import { ApiService } from "../services/api"

interface FolderInfo {
  id: number
  path: string
  file_count: number
  last_indexed: string
}

const Folders: React.FC = () => {
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isIndexing, setIsIndexing] = useState(false)

  useEffect(() => {
    loadFolders()
  }, [])

  const loadFolders = async () => {
    try {
      const foldersData = await ApiService.getFolders()
      setFolders(foldersData)
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

    try {
      const selectedPaths = await window.electronAPI.selectFolders()

      if (selectedPaths && selectedPaths.length > 0) {
        setIsIndexing(true)

        await ApiService.indexFolders({
          folder_paths: selectedPaths,
        })

        // Refresh the folders list
        setTimeout(() => {
          loadFolders()
          setIsIndexing(false)
        }, 1000)
      }
    } catch (error) {
      console.error("Error adding folders:", error)
      setIsIndexing(false)
    }
  }

  const handleRemoveFolder = async (folderId: number, folderPath: string) => {
    if (!confirm(`Are you sure you want to remove "${folderPath}" from the index?`)) {
      return
    }

    try {
      await ApiService.removeFolder(folderId)
      setFolders(folders.filter((f) => f.id !== folderId))
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
    } catch (error) {
      console.error("Error clearing index:", error)
      alert("Error clearing index. Please try again.")
    }
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
    <div className="folders-page">
      <div className="folders-header">
        <h1>Manage Folders</h1>
        <p>Add or remove folders from your search index</p>
      </div>

      <div className="folders-actions">
        <button className="add-folders-btn" onClick={handleAddFolders} disabled={isIndexing}>
          <Plus size={20} />
          {isIndexing ? "Indexing..." : "Add Folders"}
        </button>

        {folders.length > 0 && (
          <button className="clear-all-btn" onClick={handleClearAll} disabled={isIndexing}>
            <Trash2 size={20} />
            Clear All
          </button>
        )}
      </div>

      {isIndexing && (
        <div className="indexing-notice">
          <AlertCircle size={20} />
          <p>Indexing in progress. This may take a few minutes depending on the number of files.</p>
        </div>
      )}

      {folders.length === 0 ? (
        <div className="empty-state">
          <Folder size={64} />
          <h3>No folders indexed</h3>
          <p>Add some folders to start searching through your files</p>
          <button className="add-first-folder-btn" onClick={handleAddFolders}>
            <Plus size={20} />
            Add Your First Folder
          </button>
        </div>
      ) : (
        <div className="folders-list">
          {folders.map((folder) => (
            <div key={folder.id} className="folder-item">
              <div className="folder-icon">
                <Folder size={24} />
              </div>
              <div className="folder-info">
                <h3>{folder.path}</h3>
                <div className="folder-stats">
                  <span>{folder.file_count} files</span>
                  <span>Last indexed: {new Date(folder.last_indexed).toLocaleDateString()}</span>
                </div>
              </div>
              <button
                className="remove-folder-btn"
                onClick={() => handleRemoveFolder(folder.id, folder.path)}
                disabled={isIndexing}
                title="Remove folder"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Folders
