"use client"

import React, { useState, useEffect, useRef } from "react"
import { MessageSquare, Send, FileText, RefreshCw, ThumbsUp, ThumbsDown, Bot, User, ExternalLink, FolderOpen, PlusCircle, Trash2, Copy } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { coldarkDark } from "react-syntax-highlighter/dist/esm/styles/prism"
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

interface ChatSession {
  id: number;
  session_name: string;
  created_at: string;
}

const Query: React.FC = () => {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [copied, setCopied] = useState(false)
  const [isQuerying, setIsQuerying] = useState(false)
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const loadSessions = async () => {
    try {
      const fetchedSessions = await ApiService.getChatSessions();
      setSessions(fetchedSessions);
      if (fetchedSessions.length > 0) {
        setActiveSessionId(fetchedSessions[0].id);
      } else {
        createNewSession();
      }
    } catch (error) {
      console.error("Failed to load sessions:", error);
    }
  };

  const loadMessages = async (sessionId: number) => {
    try {
      const fetchedMessages = await ApiService.getChatMessages(sessionId);
      const formattedMessages: Message[] = fetchedMessages.map((msg: any) => ({
        type: msg.role === 'user' ? 'user' : 'ai',
        text: msg.content,
        sources: msg.sources,
      })).reverse();
      setMessages(formattedMessages);
    } catch (error) {
      console.error(`Failed to load messages for session ${sessionId}:`, error);
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await ApiService.createChatSession({ session_name: `New Chat...` });
      setSessions([newSession, ...sessions]);
      setActiveSessionId(newSession.id);
    } catch (error) {
      console.error("Failed to create new session:", error);
    }
  };

  const handleDeleteSession = async (sessionId: number) => {
    try {
      await ApiService.deleteChatSession(sessionId);
      const updatedSessions = sessions.filter(session => session.id !== sessionId);
      setSessions(updatedSessions);
      if (activeSessionId === sessionId) {
        setActiveSessionId(updatedSessions.length > 0 ? updatedSessions[0].id : null);
      }
    } catch (error) {
      console.error(`Failed to delete session ${sessionId}:`, error);
    }
  };

  const updateSessionName = async (sessionId: number, firstMessage: string) => {
    try {
      const generatedName = await ApiService.generateChatName(firstMessage, sessionId);
      const updatedSessions = sessions.map(session =>
        session.id === sessionId ? { ...session, session_name: generatedName } : session
      );
      setSessions(updatedSessions);
    } catch (error) {
      console.error("Failed to update session name:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isQuerying || !activeSessionId) return

    const userMessage: Message = { type: "user", text: input.trim() }
    const currentSession = sessions.find(s => s.id === activeSessionId);
    const isNewChat = currentSession?.session_name === "New Chat...";

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsQuerying(true)

    try {
      if (isNewChat && activeSessionId) {
        updateSessionName(activeSessionId, userMessage.text);
      }
      const result = await ApiService.queryWithLLM({ question: userMessage.text, session_id: activeSessionId })
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
    <div className="chat-page-container">
      <div className="chat-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
<img src="/smartfilesAI.png" alt="Smart Files AI" className="logo-image" />
          </div>
          <h2>Chat History</h2>
          <button onClick={createNewSession} className="new-chat-btn">
            <PlusCircle size={20} />
          </button>
        </div>
        <div className="session-list">
          {sessions.map(session => (
            <div
              key={session.id}
              className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
              onClick={() => setActiveSessionId(session.id)}
            >
              <span className="session-name">{session.session_name}</span>
              <button onClick={(e) => { e.stopPropagation(); handleDeleteSession(session.id); }} className="delete-session-btn">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
      <div className="chat-page">
        <div className="chat-header">
          <div className="chat-header-content">
            <div className="chat-header-logo">
<img src="/smartfilesAI.png" alt="Smart Files AI" className="logo-image" />
            </div>
            <div className="chat-header-text">
              <h1>Ask Questions</h1>
              <p>Get AI-powered answers from your indexed files</p>
            </div>
          </div>
        </div>
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.type}`}>
              <div className="message-avatar">
                {msg.type === "user" ? <User size={24} /> : <Bot size={24} />}
              </div>
              <div className="message-content">
                <div className="message-header">
                  {msg.type === 'ai' && (
                    <button className="copy-response-btn" onClick={() => {
                      navigator.clipboard.writeText(msg.text)
                      setCopied(true)
                      setTimeout(() => setCopied(false), 2000)
                    }}>
                      {copied ? "Copied!" : <Copy size={16} />}
                    </button>
                  )}
                </div>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
code({ node, className, children, ...props }: any) {
                      const match = /language-(\w+)/.exec(className || "")
                      const codeText = String(children).replace(/\n$/, "")
                      return match ? (
                        <div className="code-block">
                          <SyntaxHighlighter
                            style={coldarkDark}
                            language={match[1]}
                            PreTag="div"
                            {...props}
                          >
                            {codeText}
                          </SyntaxHighlighter>
                          <button className="copy-btn" onClick={() => navigator.clipboard.writeText(codeText)}>
                            <Copy size={16} />
                          </button>
                        </div>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      )
                    },
                  }}
                >
                  {msg.text}
                </ReactMarkdown>
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
              disabled={isQuerying || !activeSessionId}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  handleSubmit(e)
                }
              }}
            />
            <button type="submit" className="chat-send-btn" disabled={isQuerying || !input.trim() || !activeSessionId}>
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Query
