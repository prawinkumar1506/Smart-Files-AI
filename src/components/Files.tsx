// "use client"
//
// import type React from "react"
// import { useState, useEffect } from "react"
// import { File, Search, RefreshCw, FileText, ImageIcon, Code, Archive } from "lucide-react"
// import { ApiService } from "../services/api"
//
// interface FileInfo {
//     id: number
//     file_path: string
//     file_name: string
//     file_type: string
//     file_size: number
//     last_modified: string
//     folder_path: string
//     chunk_count: number
// }
//
// const Files: React.FC = () => {
//     const [files, setFiles] = useState<FileInfo[]>([])
//     const [filteredFiles, setFilteredFiles] = useState<FileInfo[]>([])
//     const [isLoading, setIsLoading] = useState(true)
//     const [searchQuery, setSearchQuery] = useState("")
//     const [selectedFileType, setSelectedFileType] = useState("all")
//     const [sortBy, setSortBy] = useState("name")
//     const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc")
//
//     useEffect(() => {
//         loadFiles()
//     }, [])
//
//     useEffect(() => {
//         filterAndSortFiles()
//     }, [files, searchQuery, selectedFileType, sortBy, sortOrder])
//
//     const loadFiles = async () => {
//         try {
//             const response = await ApiService.getIndexedFiles()
//             setFiles(response.files || [])
//         } catch (error) {
//             console.error("Error loading files:", error)
//         } finally {
//             setIsLoading(false)
//         }
//     }
//
//     const filterAndSortFiles = () => {
//         let filtered = [...files]
//
//         // Filter by search query
//         if (searchQuery) {
//             filtered = filtered.filter(
//                 (file) =>
//                     file.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
//                     file.file_path.toLowerCase().includes(searchQuery.toLowerCase()),
//             )
//         }
//
//         // Filter by file type
//         if (selectedFileType !== "all") {
//             filtered = filtered.filter((file) => {
//                 const ext = file.file_type.toLowerCase()
//                 switch (selectedFileType) {
//                     case "text":
//                         return [".txt", ".md", ".rtf"].includes(ext)
//                     case "code":
//                         return [".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"].includes(ext)
//                     case "document":
//                         return [".pdf", ".doc", ".docx", ".odt"].includes(ext)
//                     case "image":
//                         return [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"].includes(ext)
//                     default:
//                         return true
//                 }
//             })
//         }
//
//         // Sort files
//         filtered.sort((a, b) => {
//             let aValue: any, bValue: any
//
//             switch (sortBy) {
//                 case "name":
//                     aValue = a.file_name.toLowerCase()
//                     bValue = b.file_name.toLowerCase()
//                     break
//                 case "size":
//                     aValue = a.file_size
//                     bValue = b.file_size
//                     break
//                 case "modified":
//                     aValue = new Date(a.last_modified)
//                     bValue = new Date(b.last_modified)
//                     break
//                 case "type":
//                     aValue = a.file_type.toLowerCase()
//                     bValue = b.file_type.toLowerCase()
//                     break
//                 default:
//                     aValue = a.file_name.toLowerCase()
//                     bValue = b.file_name.toLowerCase()
//             }
//
//             if (aValue < bValue) return sortOrder === "asc" ? -1 : 1
//             if (aValue > bValue) return sortOrder === "asc" ? 1 : -1
//             return 0
//         })
//
//         setFilteredFiles(filtered)
//     }
//
//     const getFileIcon = (fileType: string) => {
//         const ext = fileType.toLowerCase()
//         if ([".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"].includes(ext)) {
//             return <ImageIcon size={20} />
//         }
//         if ([".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"].includes(ext)) {
//             return <Code size={20} />
//         }
//         if ([".zip", ".rar", ".7z", ".tar", ".gz"].includes(ext)) {
//             return <Archive size={20} />
//         }
//         return <FileText size={20} />
//     }
//
//     const formatFileSize = (bytes: number) => {
//         if (bytes === 0) return "0 B"
//         const k = 1024
//         const sizes = ["B", "KB", "MB", "GB"]
//         const i = Math.floor(Math.log(bytes) / Math.log(k))
//         return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
//     }
//
//     const openFile = (filePath: string) => {
//         console.log("Opening file:", filePath)
//         // In a real Electron app, you would use shell.openPath
//     }
//
//     const getFileTypeStats = () => {
//         const stats = files.reduce(
//             (acc, file) => {
//                 const ext = file.file_type.toLowerCase()
//                 let category = "other"
//
//                 if ([".txt", ".md", ".rtf"].includes(ext)) category = "text"
//                 else if ([".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"].includes(ext)) category = "code"
//                 else if ([".pdf", ".doc", ".docx", ".odt"].includes(ext)) category = "document"
//                 else if ([".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"].includes(ext)) category = "image"
//
//                 acc[category] = (acc[category] || 0) + 1
//                 return acc
//             },
//             {} as Record<string, number>,
//         )
//
//         return stats
//     }
//
//     if (isLoading) {
//         return (
//             <div className="files-page">
//                 <div className="loading-state">
//                     <RefreshCw className="spinning" size={24} />
//                     <p>Loading files...</p>
//                 </div>
//             </div>
//         )
//     }
//
//     const fileTypeStats = getFileTypeStats()
//
//     return (
//         <div className="files-page">
//             <div className="files-header">
//                 <h1>Indexed Files</h1>
//                 <p>Browse and manage all your indexed files</p>
//             </div>
//
//             <div className="files-stats">
//                 <div className="stats-grid">
//                     <div className="stat-card">
//                         <File size={24} />
//                         <div>
//                             <h3>{files.length}</h3>
//                             <p>Total Files</p>
//                         </div>
//                     </div>
//                     <div className="stat-card">
//                         <FileText size={24} />
//                         <div>
//                             <h3>{fileTypeStats.text || 0}</h3>
//                             <p>Text Files</p>
//                         </div>
//                     </div>
//                     <div className="stat-card">
//                         <Code size={24} />
//                         <div>
//                             <h3>{fileTypeStats.code || 0}</h3>
//                             <p>Code Files</p>
//                         </div>
//                     </div>
//                     <div className="stat-card">
//                         <Archive size={24} />
//                         <div>
//                             <h3>{fileTypeStats.document || 0}</h3>
//                             <p>Documents</p>
//                         </div>
//                     </div>
//                 </div>
//             </div>
//
//             <div className="files-controls">
//                 <div className="search-control">
//                     <Search size={20} />
//                     <input
//                         type="text"
//                         placeholder="Search files..."
//                         value={searchQuery}
//                         onChange={(e) => setSearchQuery(e.target.value)}
//                     />
//                 </div>
//
//                 <div className="filter-controls">
//                     <select value={selectedFileType} onChange={(e) => setSelectedFileType(e.target.value)}>
//                         <option value="all">All Types</option>
//                         <option value="text">Text Files</option>
//                         <option value="code">Code Files</option>
//                         <option value="document">Documents</option>
//                         <option value="image">Images</option>
//                     </select>
//
//                     <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
//                         <option value="name">Sort by Name</option>
//                         <option value="size">Sort by Size</option>
//                         <option value="modified">Sort by Modified</option>
//                         <option value="type">Sort by Type</option>
//                     </select>
//
//                     <button className="sort-order-btn" onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}>
//                         {sortOrder === "asc" ? "↑" : "↓"}
//                     </button>
//
//                     <button className="refresh-btn" onClick={loadFiles}>
//                         <RefreshCw size={16} />
//                         Refresh
//                     </button>
//                 </div>
//             </div>
//
//             {filteredFiles.length === 0 ? (
//                 <div className="empty-state">
//                     <File size={64} />
//                     <h3>No files found</h3>
//                     <p>
//                         {files.length === 0
//                             ? "No files have been indexed yet. Add some folders to get started."
//                             : "No files match your current filters. Try adjusting your search or filters."}
//                     </p>
//                 </div>
//             ) : (
//                 <div className="files-list">
//                     <div className="files-table">
//                         <div className="table-header">
//                             <div className="col-icon"></div>
//                             <div className="col-name">Name</div>
//                             <div className="col-type">Type</div>
//                             <div className="col-size">Size</div>
//                             <div className="col-chunks">Chunks</div>
//                             <div className="col-modified">Modified</div>
//                             <div className="col-actions">Actions</div>
//                         </div>
//
//                         {filteredFiles.map((file) => (
//                             <div key={file.id} className="table-row">
//                                 <div className="col-icon">{getFileIcon(file.file_type)}</div>
//                                 <div className="col-name">
//                                     <div className="file-name">{file.file_name}</div>
//                                     <div className="file-path">{file.folder_path}</div>
//                                 </div>
//                                 <div className="col-type">{file.file_type}</div>
//                                 <div className="col-size">{formatFileSize(file.file_size)}</div>
//                                 <div className="col-chunks">{file.chunk_count}</div>
//                                 <div className="col-modified">{new Date(file.last_modified).toLocaleDateString()}</div>
//                                 <div className="col-actions">
//                                     <button className="open-file-btn" onClick={() => openFile(file.file_path)} title="Open file">
//                                         Open
//                                     </button>
//                                 </div>
//                             </div>
//                         ))}
//                     </div>
//                 </div>
//             )}
//         </div>
//     )
// }
//
// export default Files

"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { File, Search, RefreshCw, FileText, ImageIcon, Code, Archive, ExternalLink, FolderOpen } from "lucide-react"
import { ApiService } from "../services/api"

interface FileInfo {
    id: number
    file_path: string
    file_name: string
    file_type: string
    file_size: number
    last_modified: string
    folder_path: string
    chunk_count: number
}

const Files: React.FC = () => {
    const [files, setFiles] = useState<FileInfo[]>([])
    const [filteredFiles, setFilteredFiles] = useState<FileInfo[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [selectedFileType, setSelectedFileType] = useState("all")
    const [sortBy, setSortBy] = useState("name")
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc")

    useEffect(() => {
        loadFiles()
    }, [])

    useEffect(() => {
        filterAndSortFiles()
    }, [files, searchQuery, selectedFileType, sortBy, sortOrder])

    const loadFiles = async () => {
        try {
            const response = await ApiService.getIndexedFiles()
            console.log("API response for files:", response) // Log the raw response
            
            if (response.files) {
                // Remove duplicates before setting state
                const uniqueFiles = Array.from(new Map(response.files.map((file: FileInfo) => [file.id, file])).values()) as FileInfo[];
                setFiles(uniqueFiles)
            } else {
                setFiles([])
            }
        } catch (error) {
            console.error("Error loading files:", error)
        } finally {
            setIsLoading(false)
        }
    }

    const filterAndSortFiles = () => {
        let filtered = [...files]

        // Filter by search query
        if (searchQuery) {
            filtered = filtered.filter(
                (file) =>
                    file.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    file.file_path.toLowerCase().includes(searchQuery.toLowerCase()),
            )
        }

        // Filter by file type
        if (selectedFileType !== "all") {
            filtered = filtered.filter((file) => {
                const ext = file.file_type.toLowerCase()
                switch (selectedFileType) {
                    case "text":
                        return [".txt", ".md", ".rtf"].includes(ext)
                    case "code":
                        return [".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"].includes(ext)
                    case "document":
                        return [".pdf", ".doc", ".docx", ".odt"].includes(ext)
                    case "image":
                        return [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"].includes(ext)
                    default:
                        return true
                }
            })
        }

        // Sort files
        filtered.sort((a, b) => {
            let aValue: any, bValue: any

            switch (sortBy) {
                case "name":
                    aValue = a.file_name.toLowerCase()
                    bValue = b.file_name.toLowerCase()
                    break
                case "size":
                    aValue = a.file_size
                    bValue = b.file_size
                    break
                case "modified":
                    aValue = new Date(a.last_modified)
                    bValue = new Date(b.last_modified)
                    break
                case "type":
                    aValue = a.file_type.toLowerCase()
                    bValue = b.file_type.toLowerCase()
                    break
                default:
                    aValue = a.file_name.toLowerCase()
                    bValue = b.file_name.toLowerCase()
            }

            if (aValue < bValue) return sortOrder === "asc" ? -1 : 1
            if (aValue > bValue) return sortOrder === "asc" ? 1 : -1
            return 0
        })

        setFilteredFiles(filtered)
    }

    const getFileIcon = (fileType: string) => {
        const ext = fileType.toLowerCase()
        if ([".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"].includes(ext)) {
            return <ImageIcon size={20} />
        }
        if ([".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"].includes(ext)) {
            return <Code size={20} />
        }
        if ([".zip", ".rar", ".7z", ".tar", ".gz"].includes(ext)) {
            return <Archive size={20} />
        }
        return <FileText size={20} />
    }

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return "0 B"
        const k = 1024
        const sizes = ["B", "KB", "MB", "GB"]
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
    }

    const openFile = async (filePath: string) => {
        if (window.electronAPI) {
            try {
                const result = await window.electronAPI.openFile(filePath)
                if (!result.success) {
                    alert(`Failed to open file: ${result.error}`)
                }
            } catch (error) {
                console.error("Error opening file:", error)
                alert("Failed to open file")
            }
        } else {
            // Fallback for web version
            console.log("Opening file:", filePath)
            alert("File opening is only available in the desktop app")
        }
    }

    const showInFolder = async (filePath: string) => {
        if (window.electronAPI) {
            try {
                const result = await window.electronAPI.showFileInFolder(filePath)
                if (!result.success) {
                    alert(`Failed to show file in folder: ${result.error}`)
                }
            } catch (error) {
                console.error("Error showing file in folder:", error)
                alert("Failed to show file in folder")
            }
        } else {
            console.log("Showing file in folder:", filePath)
            alert("This feature is only available in the desktop app")
        }
    }

    const getFileTypeStats = () => {
        const stats = files.reduce(
            (acc, file) => {
                const ext = file.file_type.toLowerCase()
                let category = "other"

                if ([".txt", ".md", ".rtf"].includes(ext)) category = "text"
                else if ([".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"].includes(ext)) category = "code"
                else if ([".pdf", ".doc", ".docx", ".odt"].includes(ext)) category = "document"
                else if ([".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"].includes(ext)) category = "image"

                acc[category] = (acc[category] || 0) + 1
                return acc
            },
            {} as Record<string, number>,
        )

        return stats
    }

    if (isLoading) {
        return (
            <div className="files-page">
                <div className="loading-state">
                    <RefreshCw className="spinning" size={24} />
                    <p>Loading files...</p>
                </div>
            </div>
        )
    }

    const fileTypeStats = getFileTypeStats()

    return (
        <div className="files-page">
            <div className="files-header">
                <h1>Indexed Files</h1>
                <p>Browse and manage all your indexed files</p>
            </div>

            <div className="files-stats">
                <div className="stats-grid">
                    <div className="stat-card">
                        <File size={24} />
                        <div>
                            <h3>{files.length}</h3>
                            <p>Total Files</p>
                        </div>
                    </div>
                    <div className="stat-card">
                        <FileText size={24} />
                        <div>
                            <h3>{fileTypeStats.text || 0}</h3>
                            <p>Text Files</p>
                        </div>
                    </div>
                    <div className="stat-card">
                        <Code size={24} />
                        <div>
                            <h3>{fileTypeStats.code || 0}</h3>
                            <p>Code Files</p>
                        </div>
                    </div>
                    <div className="stat-card">
                        <Archive size={24} />
                        <div>
                            <h3>{fileTypeStats.document || 0}</h3>
                            <p>Documents</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="files-controls">
                <div className="search-control">
                    <Search size={20} />
                    <input
                        type="text"
                        placeholder="Search files..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="filter-controls">
                    <select value={selectedFileType} onChange={(e) => setSelectedFileType(e.target.value)}>
                        <option value="all">All Types</option>
                        <option value="text">Text Files</option>
                        <option value="code">Code Files</option>
                        <option value="document">Documents</option>
                        <option value="image">Images</option>
                    </select>

                    <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                        <option value="name">Sort by Name</option>
                        <option value="size">Sort by Size</option>
                        <option value="modified">Sort by Modified</option>
                        <option value="type">Sort by Type</option>
                    </select>

                    <button className="sort-order-btn" onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}>
                        {sortOrder === "asc" ? "↑" : "↓"}
                    </button>

                    <button className="refresh-btn" onClick={loadFiles}>
                        <RefreshCw size={16} />
                        Refresh
                    </button>
                </div>
            </div>

            {filteredFiles.length === 0 ? (
                <div className="empty-state">
                    <File size={64} />
                    <h3>No files found</h3>
                    <p>
                        {files.length === 0
                            ? "No files have been indexed yet. Add some folders to get started."
                            : "No files match your current filters. Try adjusting your search or filters."}
                    </p>
                </div>
            ) : (
                <div className="files-list">
                    <div className="files-table">
                        <div className="table-header">
                            <div className="col-icon"></div>
                            <div className="col-name">Name</div>
                            <div className="col-type">Type</div>
                            <div className="col-size">Size</div>
                            <div className="col-chunks">Chunks</div>
                            <div className="col-modified">Modified</div>
                            <div className="col-actions">Actions</div>
                        </div>

                        {filteredFiles.map((file) => (
                            <div key={file.id} className="table-row">
                                <div className="col-icon">{getFileIcon(file.file_type)}</div>
                                <div className="col-name">
                                    <div className="file-name">{file.file_name}</div>
                                    <div className="file-path">{file.folder_path}</div>
                                </div>
                                <div className="col-type">{file.file_type}</div>
                                <div className="col-size">{formatFileSize(file.file_size)}</div>
                                <div className="col-chunks">{file.chunk_count}</div>
                                <div className="col-modified">{new Date(file.last_modified).toLocaleDateString()}</div>
                                <div className="col-actions">
                                    <button className="open-file-btn" onClick={() => openFile(file.file_path)} title="Open file">
                                        <ExternalLink size={14} />
                                        Open
                                    </button>
                                    <button
                                        className="show-folder-btn"
                                        onClick={() => showInFolder(file.file_path)}
                                        title="Show in folder"
                                    >
                                        <FolderOpen size={14} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default Files
