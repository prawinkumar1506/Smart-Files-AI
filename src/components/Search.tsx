// "use client"
//
// import type React from "react"
// import { useState } from "react"
// import { SearchIcon, File, Clock } from "lucide-react"
// import { ApiService } from "../services/api"
//
// interface SearchResult {
//   file_path: string
//   file_name: string
//   content: string
//   similarity_score: number
//   file_type: string
//   last_modified: string
// }
//
// const Search: React.FC = () => {
//   const [query, setQuery] = useState("")
//   const [results, setResults] = useState<SearchResult[]>([])
//   const [isSearching, setIsSearching] = useState(false)
//   const [hasSearched, setHasSearched] = useState(false)
//
//   const handleSearch = async (e: React.FormEvent) => {
//     e.preventDefault()
//
//     if (!query.trim()) return
//
//     setIsSearching(true)
//     setHasSearched(true)
//
//     try {
//       const response = await ApiService.searchFiles({
//         query: query.trim(),
//         limit: 20,
//         threshold: 0.6,
//       })
//
//       setResults(response.results)
//     } catch (error) {
//       console.error("Search error:", error)
//       setResults([])
//     } finally {
//       setIsSearching(false)
//     }
//   }
//
//   const openFile = (filePath: string) => {
//     // In a real Electron app, you would use shell.openPath or similar
//     console.log("Opening file:", filePath)
//   }
//
//   const highlightText = (text: string, query: string) => {
//     if (!query) return text
//
//     const regex = new RegExp(`(${query})`, "gi")
//     const parts = text.split(regex)
//
//     return parts.map((part, index) => (regex.test(part) ? <mark key={index}>{part}</mark> : part))
//   }
//
//   return (
//     <div className="search-page">
//       <div className="search-header">
//         <h1>Search Files</h1>
//         <p>Find content across all your indexed files using semantic search</p>
//       </div>
//
//       <form onSubmit={handleSearch} className="search-form">
//         <div className="search-input-container">
//           <SearchIcon size={20} className="search-icon" />
//           <input
//             type="text"
//             value={query}
//             onChange={(e) => setQuery(e.target.value)}
//             placeholder="Search for content, concepts, or keywords..."
//             className="search-input"
//             disabled={isSearching}
//           />
//           <button type="submit" className="search-button" disabled={isSearching || !query.trim()}>
//             {isSearching ? "Searching..." : "Search"}
//           </button>
//         </div>
//       </form>
//
//       {hasSearched && (
//         <div className="search-results">
//           <div className="results-header">
//             <h2>Search Results</h2>
//             <span className="results-count">
//               {results.length} result{results.length !== 1 ? "s" : ""} found
//             </span>
//           </div>
//
//           {results.length === 0 ? (
//             <div className="no-results">
//               <SearchIcon size={48} />
//               <h3>No results found</h3>
//               <p>Try different keywords or check if your files are indexed</p>
//             </div>
//           ) : (
//             <div className="results-list">
//               {results.map((result, index) => (
//                 <div key={index} className="result-item">
//                   <div className="result-header">
//                     <div className="file-info">
//                       <File size={16} />
//                       <span className="file-name">{result.file_name}</span>
//                       <span className="similarity-score">{Math.round(result.similarity_score * 100)}% match</span>
//                     </div>
//                     <button className="open-file-btn" onClick={() => openFile(result.file_path)}>
//                       Open
//                     </button>
//                   </div>
//
//                   <div className="result-content">
//                     <p>{highlightText(result.content.substring(0, 300), query)}...</p>
//                   </div>
//
//                   <div className="result-meta">
//                     <span className="file-path">{result.file_path}</span>
//                     <span className="last-modified">
//                       <Clock size={14} />
//                       {new Date(result.last_modified).toLocaleDateString()}
//                     </span>
//                   </div>
//                 </div>
//               ))}
//             </div>
//           )}
//         </div>
//       )}
//     </div>
//   )
// }
//
// export default Search

"use client"

import type React from "react"
import { useState } from "react"
import { SearchIcon, File, Clock, ExternalLink, FolderOpen } from "lucide-react"
import { ApiService } from "../services/api"

interface SearchResult {
  file_path: string
  file_name: string
  content: string
  similarity_score: number
  file_type: string
  last_modified: string
}

const Search: React.FC = () => {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!query.trim()) return

    setIsSearching(true)
    setHasSearched(true)

    try {
      const response = await ApiService.searchFiles({
        query: query.trim(),
        limit: 20,
        threshold: 0.3,
      })

      setResults(response.results)
    } catch (error) {
      console.error("Search error:", error)
      setResults([])
    } finally {
      setIsSearching(false)
    }
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

  const highlightText = (text: string, query: string) => {
    if (!query) return text

    const regex = new RegExp(`(${query})`, "gi")
    const parts = text.split(regex)

    return parts.map((part, index) => (regex.test(part) ? <mark key={index}>{part}</mark> : part))
  }

  return (
      <div className="search-page">
        <div className="search-header">
          <h1>Search Files</h1>
          <p>Find content across all your indexed files using semantic search</p>
        </div>

        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-container">
            <SearchIcon size={20} className="search-icon" />
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search for content, concepts, or keywords..."
                className="search-input"
                disabled={isSearching}
            />
            <button type="submit" className="search-button" disabled={isSearching || !query.trim()}>
              {isSearching ? "Searching..." : "Search"}
            </button>
          </div>
        </form>

        {hasSearched && (
            <div className="search-results">
              <div className="results-header">
                <h2>Search Results</h2>
                <span className="results-count">
              {results.length} result{results.length !== 1 ? "s" : ""} found
            </span>
              </div>

              {results.length === 0 ? (
                  <div className="no-results">
                    <SearchIcon size={48} />
                    <h3>No results found</h3>
                    <p>Try different keywords or check if your files are indexed</p>
                  </div>
              ) : (
                  <div className="results-list">
                    {results.map((result, index) => (
                        <div key={index} className="result-item">
                          <div className="result-header">
                            <div className="file-info">
                              <File size={16} />
                              <span className="file-name">{result.file_name}</span>
                              <span className="similarity-score">{Math.round(result.similarity_score * 100)}% match</span>
                            </div>
                            <div className="result-actions">
                              <button className="open-file-btn" onClick={() => openFile(result.file_path)}>
                                <ExternalLink size={14} />
                                Open
                              </button>
                              <button className="show-folder-btn" onClick={() => showInFolder(result.file_path)}>
                                <FolderOpen size={14} />
                                Show
                              </button>
                            </div>
                          </div>

                          <div className="result-content">
                            <p>{highlightText(result.content.substring(0, 300), query)}...</p>
                          </div>

                          <div className="result-meta">
                            <span className="file-path">{result.file_path}</span>
                            <span className="last-modified">
                      <Clock size={14} />
                              {new Date(result.last_modified).toLocaleDateString()}
                    </span>
                          </div>
                        </div>
                    ))}
                  </div>
              )}
            </div>
        )}
      </div>
  )
}

export default Search
