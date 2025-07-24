"use client"

import React, { useState, useEffect, useRef } from "react"
import { MessageSquare, Send, FileText, RefreshCw, ThumbsUp, ThumbsDown, Bot, User, ExternalLink, FolderOpen } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { ApiService } from "../services/api"

interface QuerySource {
  file_path: string
  content_preview: string
  similarity_score: number
}

interface Message {
  type: "user" | "ai"
  text: string
  sources?: QuerySource[]
}

const Query: React.FC = () => {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [isQuerying, setIsQuerying] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const storedMessages = localStorage.getItem("chatHistory")
    if (storedMessages) {
      setMessages(JSON.parse(storedMessages))
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    localStorage.setItem("chatHistory", JSON.stringify(messages))
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isQuerying) return

    const userMessage: Message = { type: "user", text: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsQuerying(true)

    try {
      const result = await ApiService.queryWithLLM({ question: userMessage.text })
      const aiMessage: Message = {
        type: "ai",
        text: result.answer,
        sources: result.sources,
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error("Query error:", error)
      const errorMessage: Message = {
        type: "ai",
        text: "Sorry, there was an error processing your question. Please try again.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsQuerying(false)
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

  return (
    <div className="chat-page">
      <div className="chat-header">
        <h1>Ask Questions</h1>
        <p>Get AI-powered answers from your indexed files</p>
      </div>
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.type}`}>
            <div className="message-avatar">
              {msg.type === "user" ? <User size={24} /> : <Bot size={24} />}
            </div>
            <div className="message-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
              {msg.sources && msg.sources.length > 0 && (
                <div className="message-sources">
                  <h4>Sources:</h4>
                  <ul>
                    {msg.sources.map((source, i) => (
                      <li key={i}>
                        <FileText size={14} />
                        <span>{source.file_path}</span>
                        <span className="relevance">
                          ({Math.round(source.similarity_score * 100)}% relevant)
                        </span>
                        <div className="source-actions">
                          <button className="open-source-btn" onClick={() => openFile(source.file_path)}>
                            <ExternalLink size={14} />
                          </button>
                          <button className="show-folder-btn" onClick={() => showInFolder(source.file_path)}>
                            <FolderOpen size={14} />
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        {isQuerying && (
          <div className="chat-message ai">
            <div className="message-avatar">
              <Bot size={24} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="chat-form">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your files..."
            className="chat-input"
            rows={1}
            disabled={isQuerying}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                handleSubmit(e)
              }
            }}
          />
          <button type="submit" className="chat-send-btn" disabled={isQuerying || !input.trim()}>
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  )
}

export default Query
