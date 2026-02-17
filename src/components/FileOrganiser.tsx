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
  TrendingUp,
  BarChart3,
  Zap,
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
  const [currentStep, setCurrentStep] = useState(1) // 1: Select, 2: Analyze, 3: Review

  useEffect(() => {
    loadFolderHierarchy()
  }, [])

  useEffect(() => {
    // Update step based on state
    if (!selectedFolder) {
      setCurrentStep(1)
    } else if (selectedFolder && !analysis) {
      setCurrentStep(2)
    } else if (analysis) {
      setCurrentStep(3)
    }
  }, [selectedFolder, analysis])

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

  const calculateAverageConfidence = () => {
    if (!analysis || analysis.classifications.length === 0) return 0
    const sum = analysis.classifications.reduce((acc, c) => acc + c.confidence, 0)
    return Math.round((sum / analysis.classifications.length) * 100)
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

            <div className="folder-icon">{isExpanded ? <FolderOpen size={24} /> : <Folder size={24} />}</div>

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
        <div className="organiser-header-content">
          <div className="organiser-header-logo">
            <img src="/smartfilesAI.png" alt="Smart Files AI" className="logo-image logo-glow" />
          </div>
          <div className="organiser-header-text">
            <h1 className="gradient-text">AI File Organiser</h1>
            <p className="subtitle-text">Intelligently organize your files with AI-powered classification</p>
          </div>
        </div>
      </div>

      {/* 3-Step Workflow Indicator */}
      <div className="workflow-steps">
        <div className={`workflow-step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
          <div className="step-circle">
            {currentStep > 1 ? <CheckCircle size={20} /> : '1'}
          </div>
          <div className="step-label">
            <h4>Select Folder</h4>
            <p>Choose folder to organize</p>
          </div>
        </div>
        
        <div className="step-connector"></div>
        
        <div className={`workflow-step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
          <div className="step-circle">
            {currentStep > 2 ? <CheckCircle size={20} /> : '2'}
          </div>
          <div className="step-label">
            <h4>Analyze Files</h4>
            <p>AI categorizes your files</p>
          </div>
        </div>
        
        <div className="step-connector"></div>
        
        <div className={`workflow-step ${currentStep >= 3 ? 'active' : ''}`}>
          <div className="step-circle">3</div>
          <div className="step-label">
            <h4>Review & Execute</h4>
            <p>Confirm and apply changes</p>
          </div>
        </div>
      </div>

      <div className="organiser-content-modern">
        {/* Left Panel: Folder Tree */}
        <div className="folder-tree-panel-modern glassmorphic">
          <div className="panel-header">
            <h3>Folder Structure</h3>
            <button className="refresh-btn-modern" onClick={loadFolderHierarchy}>
              <RefreshCw size={16} />
            </button>
          </div>

          <div className="folder-tree">
            {hierarchy.length === 0 ? (
              <div className="empty-state-small">
                <Folder size={32} />
                <p>No folders indexed</p>
              </div>
            ) : (
              hierarchy.map((folder) => renderFolder(folder))
            )}
          </div>
        </div>

        {/* Right Panel: AI Analysis */}
        <div className="analysis-panel-modern">
          {!selectedFolder ? (
            <div className="no-selection-modern glassmorphic">
              <div className="illustration-circle pulse">
                <Sparkles size={48} />
              </div>
              <h3>Select a Folder to Begin</h3>
              <p>Choose a folder from the tree to start AI-powered organization</p>
              <div className="feature-highlights">
                <div className="feature-item">
                  <Zap size={16} />
                  <span>AI Classification</span>
                </div>
                <div className="feature-item">
                  <BarChart3 size={16} />
                  <span>Smart Categorization</span>
                </div>
                <div className="feature-item">
                  <TrendingUp size={16} />
                  <span>Confidence Scoring</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="folder-analysis-modern">
              {/* Selected Folder Info */}
              <div className="selected-folder-card glassmorphic">
                <div className="card-header-modern">
                  <h3>Selected Folder</h3>
                  {selectedFolderInfo && (
                    <span className="file-badge">{selectedFolderInfo.file_count} files</span>
                  )}
                </div>
                <div className="folder-details-modern">
                  <div className="folder-icon-large gradient-bg-blue">
                    <Folder size={32} />
                  </div>
                  <div className="folder-text">
                    <div className="folder-name-large">{selectedFolderInfo?.name}</div>
                    <div className="folder-path-small">{selectedFolderInfo?.path}</div>
                  </div>
                </div>
                <button 
                  className="analyze-btn-modern gradient-bg-purple" 
                  onClick={analyzeFolder} 
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <RefreshCw size={16} className="spinning" />
                      AI Analyzing...
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      Start AI Analysis
                    </>
                  )}
                </button>
              </div>

              {/* AI Analysis Results */}
              {analysis && (
                <>
                  {/* Confidence Score Card */}
                  <div className="confidence-card glassmorphic">
                    <div className="confidence-header">
                      <h4>AI Confidence Score</h4>
                      <div className={`confidence-badge ${calculateAverageConfidence() > 80 ? 'high' : calculateAverageConfidence() > 60 ? 'medium' : 'low'}`}>
                        {calculateAverageConfidence() > 80 ? 'High' : calculateAverageConfidence() > 60 ? 'Medium' : 'Low'} Confidence
                      </div>
                    </div>
                    <div className="confidence-visual">
                      <div className="confidence-circle">
                        <svg viewBox="0 0 100 100">
                          <circle cx="50" cy="50" r="45" className="confidence-bg" />
                          <circle 
                            cx="50" 
                            cy="50" 
                            r="45" 
                            className="confidence-progress"
                            style={{ 
                              strokeDasharray: `${calculateAverageConfidence() * 2.83} 283`,
                              stroke: calculateAverageConfidence() > 80 ? '#10b981' : calculateAverageConfidence() > 60 ? '#f59e0b' : '#ef4444'
                            }}
                          />
                        </svg>
                        <div className="confidence-percentage">{calculateAverageConfidence()}%</div>
                      </div>
                      <div className="confidence-stats">
                        <div className="stat-item">
                          <span className="stat-label">Total Files</span>
                          <span className="stat-value">{analysis.total_files}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Categories</span>
                          <span className="stat-value">{Object.keys(analysis.suggested_structure).length}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* AI Suggested Structure */}
                  <div className="structure-card glassmorphic">
                    <div className="card-header-modern">
                      <h4>AI Suggested Structure</h4>
                      <span className="info-badge">
                        {Object.keys(analysis.suggested_structure).length} categories
                      </span>
                    </div>
                    <div className="category-tree">
                      {Object.entries(analysis.suggested_structure).map(([folderName, files]) => (
                        <div key={folderName} className="category-item-modern">
                          <div className="category-header-modern">
                            <FolderOpen size={18} className="category-icon" />
                            <span className="category-name">{folderName}</span>
                            <span className="category-count">{files.length} files</span>
                          </div>
                          <div className="category-progress-bar">
                            <div 
                              className="category-progress-fill"
                              style={{ width: `${(files.length / analysis.total_files) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="action-buttons-modern">
                    <button className="preview-btn-modern" onClick={() => setShowConfirmDialog(true)}>
                      <Eye size={18} />
                      Preview Changes
                    </button>
                    <button className="execute-btn-modern gradient-bg-green" onClick={() => setShowConfirmDialog(true)}>
                      <Play size={18} />
                      Execute Organization
                    </button>
                  </div>
                </>
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
