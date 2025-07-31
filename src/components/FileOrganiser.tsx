"use client"

import React, { useState, useEffect } from "react"
import {
  Folder,
  FolderOpen,
  File,
  ChevronRight,
  ChevronDown,
  Sparkles,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  Play,
} from "lucide-react"
import { ApiService } from "../services/api"

interface FolderHierarchy {
  id: number
  path: string
  name: string
  parent_id?: number
  level: number
  file_count: number
  subfolder_count: number
  last_modified: string
  children: FolderHierarchy[]
}

interface FileClassification {
  file_id: number
  file_path: string
  file_name: string
  file_type: string
  classification: string
  confidence: number
  suggested_folder: string
  reasoning: string
}

interface OrganiseAnalysis {
  success: boolean
  message: string
  classifications: FileClassification[]
  suggested_structure: Record<string, string[]>
  total_files: number
}

const FileOrganiser: React.FC = () => {
  const [hierarchy, setHierarchy] = useState<FolderHierarchy[]>([])
  const [expandedFolders, setExpandedFolders] = useState<Set<number>>(new Set())
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [analysis, setAnalysis] = useState<OrganiseAnalysis | null>(null)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)

  useEffect(() => {
    loadFolderHierarchy()
  }, [])

  const loadFolderHierarchy = async () => {
    try {
      setIsLoading(true)
      const response = await ApiService.getFolderHierarchy()
      
      // The API now returns a nested structure directly
      if (response.success && response.hierarchy) {
        setHierarchy(response.hierarchy)
      } else {
        setHierarchy([])
        console.error("Failed to load folder hierarchy:", response)
      }
    } catch (error) {
      console.error("Error loading folder hierarchy:", error)
      setHierarchy([])
    } finally {
      setIsLoading(false)
    }
  }

  const toggleFolder = (folderId: number) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId)
    } else {
      newExpanded.add(folderId)
    }
    setExpandedFolders(newExpanded)
  }

  const selectFolder = (folderId: number) => {
    setSelectedFolder(folderId)
    setAnalysis(null) // Clear previous analysis
  }

  const analyzeFolder = async () => {
    if (!selectedFolder) return

    try {
      setIsAnalyzing(true)
      const response = await ApiService.analyzeFolderForOrganisation({
        folder_id: selectedFolder,
        dry_run: true,
      })
      setAnalysis(response)
    } catch (error) {
      console.error("Error analyzing folder:", error)
      alert("Failed to analyze folder. Please try again.")
    } finally {
      setIsAnalyzing(false)
    }
  }

  const executeOrganisation = async () => {
    if (!selectedFolder || !analysis) return

    try {
      setIsExecuting(true)
      const response = await ApiService.executeOrganisation({
        folder_id: selectedFolder,
        actions: analysis.classifications,
        confirm: true,
      })

      if (response.success) {
        alert(`Successfully organized ${response.moved_files} files into ${response.created_folders} folders!`)
        setAnalysis(null)
        setShowConfirmDialog(false)
        // Refresh hierarchy to show new structure
        await loadFolderHierarchy()
      } else {
        alert(`Organization failed: ${response.message}`)
      }
    } catch (error) {
      console.error("Error executing organization:", error)
      alert("Failed to execute organization. Please try again.")
    } finally {
      setIsExecuting(false)
    }
  }

  const renderFolder = (folder: FolderHierarchy, level = 0) => {
    const isExpanded = expandedFolders.has(folder.id)
    const isSelected = selectedFolder === folder.id
    const hasChildren = folder.children && folder.children.length > 0

    return (
      <div key={folder.id} className="folder-tree-item">
        <div
          className={`folder-item ${isSelected ? "selected" : ""}`}
          style={{ paddingLeft: `${level * 20 + 10}px` }}
          onClick={() => selectFolder(folder.id)}
        >
          <div className="folder-content">
            <button
              className="expand-button"
              onClick={(e) => {
                e.stopPropagation()
                toggleFolder(folder.id)
              }}
              disabled={!hasChildren}
            >
              {hasChildren ? (
                isExpanded ? (
                  <ChevronDown size={16} />
                ) : (
                  <ChevronRight size={16} />
                )
              ) : (
                <div style={{ width: 16 }} />
              )}
            </button>

            <div className="folder-icon">{isExpanded ? <FolderOpen size={20} /> : <Folder size={20} />}</div>

            <div className="folder-info">
              <span className="folder-name">{folder.name}</span>
              <span className="folder-stats">
                {folder.file_count} files
                {folder.subfolder_count > 0 && `, ${folder.subfolder_count} subfolders`}
              </span>
            </div>
          </div>
        </div>

        {isExpanded && hasChildren && (
          <div className="folder-children">{folder.children.map((child) => renderFolder(child, level + 1))}</div>
        )}
      </div>
    )
  }

  const getSelectedFolderInfo = () => {
    const findFolder = (folders: FolderHierarchy[], id: number): FolderHierarchy | null => {
      for (const folder of folders) {
        if (folder.id === id) return folder
        if (folder.children) {
          const found = findFolder(folder.children, id)
          if (found) return found
        }
      }
      return null
    }

    return selectedFolder ? findFolder(hierarchy, selectedFolder) : null
  }

  const selectedFolderInfo = getSelectedFolderInfo()

  if (isLoading) {
    return (
      <div className="file-organiser-page">
        <div className="loading-state">
          <RefreshCw className="spinning" size={24} />
          <p>Loading folder structure...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="file-organiser-page">
      <div className="organiser-header">
        <h1>File Organiser</h1>
        <p>Intelligently organize your files using AI-powered classification</p>
      </div>

      <div className="organiser-content">
        <div className="folder-tree-panel">
          <div className="panel-header">
            <h3>Folder Structure</h3>
            <button className="refresh-btn" onClick={loadFolderHierarchy}>
              <RefreshCw size={16} />
            </button>
          </div>

          <div className="folder-tree">
            {hierarchy.length === 0 ? (
              <div className="empty-state">
                <Folder size={48} />
                <p>No folders indexed yet</p>
                <p>Add some folders to get started</p>
              </div>
            ) : (
              hierarchy.map((folder) => renderFolder(folder))
            )}
          </div>
        </div>

        <div className="analysis-panel">
          {!selectedFolder ? (
            <div className="no-selection">
              <Sparkles size={48} />
              <h3>Select a Folder to Organize</h3>
              <p>Choose a folder from the tree to analyze and organize its files</p>
            </div>
          ) : (
            <div className="folder-analysis">
              <div className="selected-folder-info">
                <h3>Selected Folder</h3>
                <div className="folder-details">
                  <Folder size={20} />
                  <div>
                    <div className="folder-name">{selectedFolderInfo?.name}</div>
                    <div className="folder-path">{selectedFolderInfo?.path}</div>
                    <div className="folder-stats">
                      {selectedFolderInfo?.file_count} files, {selectedFolderInfo?.subfolder_count} subfolders
                    </div>
                  </div>
                </div>
              </div>

              <div className="analysis-actions">
                <button className="analyze-btn" onClick={analyzeFolder} disabled={isAnalyzing}>
                  <Sparkles size={16} />
                  {isAnalyzing ? "Analyzing..." : "Analyze for Organization"}
                </button>
              </div>

              {analysis && (
                <div className="analysis-results">
                  <div className="results-header">
                    <h4>Analysis Results</h4>
                    <div className="results-summary">
                      {analysis.total_files} files analyzed, {Object.keys(analysis.suggested_structure).length}{" "}
                      categories suggested
                    </div>
                  </div>

                  <div className="suggested-structure">
                    <h5>Suggested Organization</h5>
                    {Object.entries(analysis.suggested_structure).map(([folderName, files]) => (
                      <div key={folderName} className="category-group">
                        <div className="category-header">
                          <Folder size={16} />
                          <span className="category-name">{folderName}</span>
                          <span className="file-count">({files.length} files)</span>
                        </div>
                        <div className="category-files">
                          {files.slice(0, 5).map((fileName) => (
                            <div key={fileName} className="file-item">
                              <File size={14} />
                              <span>{fileName}</span>
                            </div>
                          ))}
                          {files.length > 5 && <div className="more-files">+{files.length - 5} more files</div>}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="classification-details">
                    <h5>Classification Details</h5>
                    <div className="classifications-list">
                      {analysis.classifications.slice(0, 10).map((classification) => (
                        <div key={classification.file_id} className="classification-item">
                          <div className="file-info">
                            <File size={14} />
                            <span className="file-name">{classification.file_name}</span>
                          </div>
                          <div className="classification-info">
                            <span className="category">{classification.classification}</span>
                            <span className="confidence">
                              {Math.round(classification.confidence * 100)}% confidence
                            </span>
                          </div>
                          <div className="reasoning">{classification.reasoning}</div>
                        </div>
                      ))}
                      {analysis.classifications.length > 10 && (
                        <div className="more-classifications">
                          +{analysis.classifications.length - 10} more classifications
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="execution-actions">
                    <button className="preview-btn" onClick={() => setShowConfirmDialog(true)}>
                      <Eye size={16} />
                      Preview Changes
                    </button>
                    <button className="execute-btn" onClick={() => setShowConfirmDialog(true)}>
                      <Play size={16} />
                      Execute Organization
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {showConfirmDialog && analysis && (
        <div className="modal-overlay">
          <div className="confirmation-modal">
            <div className="modal-header">
              <h3>Confirm File Organization</h3>
              <button className="close-btn" onClick={() => setShowConfirmDialog(false)}>
                <XCircle size={20} />
              </button>
            </div>

            <div className="modal-content">
              <div className="warning-notice">
                <AlertTriangle size={20} />
                <div>
                  <h4>Important Notice</h4>
                  <p>
                    This action will physically move files on your system and create new folders. Make sure you have
                    backups of important files.
                  </p>
                </div>
              </div>

              <div className="changes-summary">
                <h4>Changes to be made:</h4>
                <ul>
                  <li>Create {Object.keys(analysis.suggested_structure).length} new folders</li>
                  <li>Move {analysis.total_files} files to organized locations</li>
                  <li>Update file index to reflect new structure</li>
                </ul>
              </div>

              <div className="folder-preview">
                <h4>New folder structure:</h4>
                {Object.entries(analysis.suggested_structure).map(([folderName, files]) => (
                  <div key={folderName} className="preview-folder">
                    <Folder size={16} />
                    <span>
                      {folderName} ({files.length} files)
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="modal-actions">
              <button className="cancel-btn" onClick={() => setShowConfirmDialog(false)}>
                Cancel
              </button>
              <button className="confirm-btn" onClick={executeOrganisation} disabled={isExecuting}>
                {isExecuting ? (
                  <>
                    <RefreshCw className="spinning" size={16} />
                    Organizing...
                  </>
                ) : (
                  <>
                    <CheckCircle size={16} />
                    Confirm & Execute
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FileOrganiser
