// "use client"
//
// import type React from "react"
// import { useState } from "react"
// import { MessageSquare, Send, FileText, ExternalLink, RefreshCw } from "lucide-react"
// import { ApiService } from "../services/api"
//
// interface QuerySource {
//   file_path: string
//   content_preview: string
//   similarity_score: number
// }
//
// interface QueryResponse {
//   success: boolean
//   answer: string
//   sources: QuerySource[]
// }
//
// const Query: React.FC = () => {
//   const [question, setQuestion] = useState("")
//   const [response, setResponse] = useState<QueryResponse | null>(null)
//   const [isQuerying, setIsQuerying] = useState(false)
//   const [history, setHistory] = useState<Array<{ question: string; response: QueryResponse }>>([])
//
//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault()
//
//     if (!question.trim() || isQuerying) return
//
//     const currentQuestion = question.trim()
//     setIsQuerying(true)
//
//     try {
//       const result = await ApiService.queryWithLLM({
//         question: currentQuestion,
//       })
//
//       setResponse(result)
//       setHistory((prev) => [...prev, { question: currentQuestion, response: result }])
//       setQuestion("") // Clear the input after successful submission
//     } catch (error) {
//       console.error("Query error:", error)
//       setResponse({
//         success: false,
//         answer:
//             "Sorry, there was an error processing your question. Please check that your folders are indexed and try again.",
//         sources: [],
//       })
//     } finally {
//       setIsQuerying(false)
//     }
//   }
//
//   const handleNewQuery = () => {
//     setResponse(null)
//     setQuestion("")
//   }
//
//   const openFile = (filePath: string) => {
//     console.log("Opening file:", filePath)
//   }
//
//   return (
//       <div className="query-page">
//         <div className="query-header">
//           <h1>Ask Questions</h1>
//           <p>Get AI-powered answers based on your indexed files</p>
//           {response && (
//               <button className="new-query-btn" onClick={handleNewQuery}>
//                 <RefreshCw size={16} />
//                 New Query
//               </button>
//           )}
//         </div>
//
//         <form onSubmit={handleSubmit} className="query-form">
//           <div className="query-input-container">
//             <MessageSquare size={20} className="query-icon" />
//             <textarea
//                 value={question}
//                 onChange={(e) => setQuestion(e.target.value)}
//                 placeholder="Ask a question about your files... (e.g., 'What files are in the certificate folder?')"
//                 className="query-input"
//                 rows={3}
//                 disabled={isQuerying}
//             />
//             <button type="submit" className="query-button" disabled={isQuerying || !question.trim()}>
//               <Send size={16} />
//               {isQuerying ? "Thinking..." : "Ask"}
//             </button>
//           </div>
//         </form>
//
//         {isQuerying && (
//             <div className="querying-status">
//               <RefreshCw className="spinning" size={20} />
//               <p>Searching through your files and generating an answer...</p>
//             </div>
//         )}
//
//         {response && (
//             <div className="query-response">
//               <div className="answer-section">
//                 <h3>Answer</h3>
//                 <div className="answer-content">
//                   <p>{response.answer}</p>
//                 </div>
//               </div>
//
//               {response.sources && response.sources.length > 0 && (
//                   <div className="sources-section">
//                     <h3>Sources ({response.sources.length} files found)</h3>
//                     <div className="sources-list">
//                       {response.sources.map((source, index) => (
//                           <div key={index} className="source-item">
//                             <div className="source-header">
//                               <FileText size={16} />
//                               <span className="source-path">{source.file_path}</span>
//                               <span className="source-score">{Math.round(source.similarity_score * 100)}% relevant</span>
//                               <button className="open-source-btn" onClick={() => openFile(source.file_path)}>
//                                 <ExternalLink size={14} />
//                               </button>
//                             </div>
//                             <div className="source-preview">
//                               <p>{source.content_preview}</p>
//                             </div>
//                           </div>
//                       ))}
//                     </div>
//                   </div>
//               )}
//             </div>
//         )}
//
//         {history.length > 0 && (
//             <div className="query-history">
//               <h3>Recent Questions</h3>
//               <div className="history-list">
//                 {history
//                     .slice(-5)
//                     .reverse()
//                     .map((item, index) => (
//                         <div key={index} className="history-item">
//                           <div className="history-question">
//                             <MessageSquare size={16} />
//                             <span>{item.question}</span>
//                           </div>
//                           <div className="history-answer">
//                             <p>{item.response.answer.substring(0, 150)}...</p>
//                           </div>
//                         </div>
//                     ))}
//               </div>
//             </div>
//         )}
//       </div>
//   )
// }
//
// export default Query

"use client"

import type React from "react"
import { useState } from "react"
import { MessageSquare, Send, FileText, ExternalLink, RefreshCw, FolderOpen } from "lucide-react"
import { ApiService } from "../services/api"

interface QuerySource {
  file_path: string
  content_preview: string
  similarity_score: number
}

interface QueryResponse {
  success: boolean
  answer: string
  sources: QuerySource[]
}

const Query: React.FC = () => {
  const [question, setQuestion] = useState("")
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [isQuerying, setIsQuerying] = useState(false)
  const [history, setHistory] = useState<Array<{ question: string; response: QueryResponse }>>([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!question.trim() || isQuerying) return

    const currentQuestion = question.trim()
    setIsQuerying(true)

    try {
      const result = await ApiService.queryWithLLM({
        question: currentQuestion,
      })

      setResponse(result)
      setHistory((prev) => [...prev, { question: currentQuestion, response: result }])
      setQuestion("") // Clear the input after successful submission
    } catch (error) {
      console.error("Query error:", error)
      setResponse({
        success: false,
        answer:
            "Sorry, there was an error processing your question. Please check that your folders are indexed and try again.",
        sources: [],
      })
    } finally {
      setIsQuerying(false)
    }
  }

  const handleNewQuery = () => {
    setResponse(null)
    setQuestion("")
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

  return (
      <div className="query-page">
        <div className="query-header">
          <div>
            <h1>Ask Questions</h1>
            <p>Get AI-powered answers based on your indexed files</p>
          </div>
          {response && (
              <button className="new-query-btn" onClick={handleNewQuery}>
                <RefreshCw size={16} />
                New Query
              </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="query-form">
          <div className="query-input-container">
            <MessageSquare size={20} className="query-icon" />
            <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your files... (e.g., 'What files are in the certificate folder?')"
                className="query-input"
                rows={3}
                disabled={isQuerying}
            />
            <button type="submit" className="query-button" disabled={isQuerying || !question.trim()}>
              <Send size={16} />
              {isQuerying ? "Thinking..." : "Ask"}
            </button>
          </div>
        </form>

        {isQuerying && (
            <div className="querying-status">
              <RefreshCw className="spinning" size={20} />
              <p>Searching through your files and generating an answer...</p>
            </div>
        )}

        {response && (
            <div className="query-response">
              <div className="answer-section">
                <h3>Answer</h3>
                <div className="answer-content">
                  <p>{response.answer}</p>
                </div>
              </div>

              {response.sources && response.sources.length > 0 && (
                  <div className="sources-section">
                    <h3>Sources ({response.sources.length} files found)</h3>
                    <div className="sources-list">
                      {response.sources.map((source, index) => (
                          <div key={index} className="source-item">
                            <div className="source-header">
                              <FileText size={16} />
                              <span className="source-path">{source.file_path}</span>
                              <span className="source-score">{Math.round(source.similarity_score * 100)}% relevant</span>
                              <div className="source-actions">
                                <button className="open-source-btn" onClick={() => openFile(source.file_path)}>
                                  <ExternalLink size={14} />
                                </button>
                                <button className="show-folder-btn" onClick={() => showInFolder(source.file_path)}>
                                  <FolderOpen size={14} />
                                </button>
                              </div>
                            </div>
                            <div className="source-preview">
                              <p>{source.content_preview}</p>
                            </div>
                          </div>
                      ))}
                    </div>
                  </div>
              )}
            </div>
        )}

        {history.length > 0 && (
            <div className="query-history">
              <h3>Recent Questions</h3>
              <div className="history-list">
                {history
                    .slice(-5)
                    .reverse()
                    .map((item, index) => (
                        <div key={index} className="history-item">
                          <div className="history-question">
                            <MessageSquare size={16} />
                            <span>{item.question}</span>
                          </div>
                          <div className="history-answer">
                            <p>{item.response.answer.substring(0, 150)}...</p>
                          </div>
                        </div>
                    ))}
              </div>
            </div>
        )}
      </div>
  )
}

export default Query
