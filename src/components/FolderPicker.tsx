"use client"

import React, { useState, useEffect } from "react"
import { Folder, File, ChevronRight, Check, X } from "lucide-react"

interface FolderPickerProps {
  onSelect: (paths: string[]) => void
  onCancel: () => void
}

interface FileItem {
  name: string
  path: string
  isDirectory: boolean
  children?: FileItem[]
}

const FolderPicker: React.FC<FolderPickerProps> = ({ onSelect, onCancel }) => {
  const ROOT_LABEL = "This PC"
  const ROOT_PATH = "__root__"
  const [currentPath, setCurrentPath] = useState<string>(ROOT_PATH)
  const [pathInput, setPathInput] = useState<string>(ROOT_LABEL)
  const [items, setItems] = useState<FileItem[]>([])
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set())
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Load initial directory (user's home or desktop)
    loadInitialDirectory()
  }, [])

  const loadInitialDirectory = async () => {
    try {
      setLoading(true)
      await loadRoot()
    } catch (error) {
      console.error("Error loading initial directory:", error)
    } finally {
      setLoading(false)
    }
  }

  const loadRoot = async () => {
    setCurrentPath(ROOT_PATH)
    setPathInput(ROOT_LABEL)
    await loadDrives()
  }

  const loadDrives = async () => {
    try {
      if (!window.electronAPI?.getDrives) {
        const homeDir = await window.electronAPI?.getHomeDirectory?.()
        if (homeDir) {
          setCurrentPath(homeDir)
          setPathInput(homeDir)
          await loadDirectory(homeDir)
          return
        }

        setItems([])
        return
      }

      const drives = await window.electronAPI.getDrives()
      const driveItems = drives.map((drive: string) => ({
        name: drive,
        path: drive,
        isDirectory: true,
      }))
      setItems(driveItems)
    } catch (error) {
      console.error("Error loading drives:", error)
      setItems([])
    }
  }

  const loadDirectory = async (path: string) => {
    try {
      setLoading(true)
      const contents = await window.electronAPI.readDirectory(path)
      setItems(contents)
    } catch (error) {
      console.error("Error loading directory:", error)
    } finally {
      setLoading(false)
    }
  }

  const handlePathChange = async (newPath: string) => {
    if (!newPath || newPath.toLowerCase() === ROOT_LABEL.toLowerCase()) {
      await loadRoot()
      return
    }

    setCurrentPath(newPath)
    setPathInput(newPath)
    await loadDirectory(newPath)
  }

  const toggleFolder = async (folderPath: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(folderPath)) {
      newExpanded.delete(folderPath)
    } else {
      newExpanded.add(folderPath)
    }
    setExpandedFolders(newExpanded)
  }

  const toggleFolderSelection = (folderPath: string) => {
    const newSelected = new Set(selectedFolders)
    if (newSelected.has(folderPath)) {
      newSelected.delete(folderPath)
    } else {
      newSelected.add(folderPath)
    }
    setSelectedFolders(newSelected)
  }

  const toggleCurrentFolderSelection = () => {
    if (currentPath === ROOT_PATH) {
      return
    }
    toggleFolderSelection(currentPath)
  }

  const handleConfirm = () => {
    onSelect(Array.from(selectedFolders))
  }

  const navigateUp = () => {
    if (currentPath === ROOT_PATH) {
      return
    }

    const isDriveRoot = /^[A-Za-z]:\\?$/.test(currentPath)
    if (isDriveRoot) {
      handlePathChange(ROOT_PATH)
      return
    }

    const parentPath = currentPath.split(/[\\/]/).slice(0, -1).join("\\")
    if (parentPath) {
      handlePathChange(parentPath)
    } else {
      handlePathChange(ROOT_PATH)
    }
  }

  const navigateTo = (item: FileItem) => {
    if (item.isDirectory) {
      handlePathChange(item.path)
    }
  }

  const getPathParts = () => {
    if (currentPath === ROOT_PATH) {
      return []
    }
    return currentPath.split(/[\\/]/).filter(Boolean)
  }

  const handlePathSubmit = async () => {
    const trimmed = pathInput.trim()
    if (!trimmed) {
      return
    }

    const normalized = trimmed.endsWith(":") ? `${trimmed}\\` : trimmed
    if (normalized.toLowerCase() === ROOT_LABEL.toLowerCase()) {
      await loadRoot()
      return
    }

    const stat = await window.electronAPI.statPath(normalized)
    if (!stat.exists) {
      return
    }

    if (stat.isDirectory) {
      await handlePathChange(stat.path)
      return
    }

    const lastSlash = normalized.lastIndexOf("\\")
    const lastForward = normalized.lastIndexOf("/")
    const lastIndex = Math.max(lastSlash, lastForward)
    if (lastIndex > 0) {
      await handlePathChange(normalized.slice(0, lastIndex))
    }
  }

  return (
    <div className="folder-picker-overlay">
      <div className="folder-picker-modal">
        <div className="folder-picker-header">
          <h2>Select Folders to Index</h2>
          <button onClick={onCancel} className="close-button">
            <X size={20} />
          </button>
        </div>

        <div className="folder-picker-pathbar">
          <button className="path-root" onClick={loadRoot}>
            {ROOT_LABEL}
          </button>
          <input
            className="path-input"
            type="text"
            value={pathInput}
            onChange={(event) => setPathInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                handlePathSubmit()
              }
            }}
          />
          <button className="path-go" onClick={handlePathSubmit}>
            Go
          </button>
          <button
            className="path-select"
            onClick={toggleCurrentFolderSelection}
            disabled={currentPath === ROOT_PATH}
          >
            Select This Folder
          </button>
        </div>

        <div className="folder-picker-breadcrumb">
          <button onClick={navigateUp} disabled={currentPath === ROOT_PATH}>
            ..
          </button>
          <button className="breadcrumb-root" onClick={loadRoot}>
            {ROOT_LABEL}
          </button>
          {getPathParts().map((part, index) => (
            <span key={index} className="breadcrumb-part">
              <ChevronRight size={16} />
              <span>{part}</span>
            </span>
          ))}
        </div>

        <div className="folder-picker-body">
          {loading ? (
            <div className="loading">Loading...</div>
          ) : (
            <div className="items-list">
              {items.map((item) => (
                <div
                  key={item.path}
                  className={`item-row ${item.isDirectory ? "folder-row" : "file-row"} ${
                    selectedFolders.has(item.path) ? "selected" : ""
                  }`}
                >
                  <div className="item-main">
                    {item.isDirectory ? (
                      <>
                        <button
                          className="folder-checkbox"
                          onClick={() => toggleFolderSelection(item.path)}
                        >
                          {selectedFolders.has(item.path) ? (
                            <Check size={16} />
                          ) : (
                            <Folder size={16} />
                          )}
                        </button>
                        <div className="folder-item-actions">
                          <button
                            className="item-name"
                            onClick={() => navigateTo(item)}
                            onDoubleClick={() => navigateTo(item)}
                          >
                            <Folder size={16} />
                            <span>{item.name}</span>
                          </button>
                          <button
                            className="item-select"
                            onClick={() => toggleFolderSelection(item.path)}
                          >
                            Select
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="file-item">
                        <File size={16} />
                        <span>{item.name}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="folder-picker-footer">
          <div className="selected-count">
            {selectedFolders.size} folder(s) selected
          </div>
          <div className="folder-picker-actions">
            <button onClick={onCancel} className="btn-cancel">
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="btn-confirm"
              disabled={selectedFolders.size === 0}
            >
              Select Folder{selectedFolders.size !== 1 ? "s" : ""}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FolderPicker
