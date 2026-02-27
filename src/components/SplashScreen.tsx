'use client'

import { useEffect, useState } from 'react'
import './SplashScreen.css'

interface LoadingStep {
  id: number
  label: string
  completed: boolean
  active: boolean
}

export function SplashScreen() {
  const [steps, setSteps] = useState<LoadingStep[]>([
    { id: 1, label: 'Initializing Local AI Engine', completed: false, active: true },
    { id: 2, label: 'Indexing Your Files', completed: false, active: false },
    { id: 3, label: 'Preparing Smart Search', completed: false, active: false },
  ])

  const [progress, setProgress] = useState(0)
  const [logoScale, setLogoScale] = useState(0.95)
  const [logoGlow, setLogoGlow] = useState(false)

  // Simulate loading progression
  useEffect(() => {
    setLogoScale(1)
    setLogoGlow(true)

    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + Math.random() * 30
      })
    }, 1500)

    // Simulate step progression
    const stepTimers = [
      setTimeout(() => {
        setSteps((prev) =>
          prev.map((step, idx) =>
            idx === 0
              ? { ...step, completed: true, active: false }
              : idx === 1
                ? { ...step, active: true }
                : step
          )
        )
      }, 3000),
      setTimeout(() => {
        setSteps((prev) =>
          prev.map((step, idx) =>
            idx === 1
              ? { ...step, completed: true, active: false }
              : idx === 2
                ? { ...step, active: true }
                : step
          )
        )
      }, 5500),
      setTimeout(() => {
        setSteps((prev) =>
          prev.map((step, idx) =>
            idx === 2 ? { ...step, completed: true, active: false } : step
          )
        )
      }, 8000),
    ]

    return () => {
      clearInterval(progressInterval)
      stepTimers.forEach((timer) => clearTimeout(timer))
    }
  }, [])

  return (
    <div className="splash-container">
      {/* Animated background */}
      <div className="splash-background">
        <div className="gradient-bg"></div>
        <div className="grain-texture"></div>
        <div className="radial-glow"></div>
      </div>

      {/* Content */}
      <div className="splash-content">
        {/* Logo Section */}
        <div className="logo-section">
          <div
            className="logo-wrapper"
            style={{
              transform: `scale(${logoScale})`,
              opacity: logoScale > 0.95 ? 1 : 0,
            }}
          >
            <div className={`logo-container ${logoGlow ? 'glow-pulse' : ''}`}>
              <svg
                width="80"
                height="80"
                viewBox="0 0 80 80"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Smart Files AI Logo */}
                <circle cx="40" cy="40" r="38" fill="url(#gradient)" opacity="0.1" />
                <path
                  d="M40 16C27.268 16 17 26.268 17 39C17 51.732 27.268 62 40 62C52.732 62 63 51.732 63 39C63 26.268 52.732 16 40 16Z"
                  fill="none"
                  stroke="url(#gradientStroke)"
                  strokeWidth="2"
                />
                <g className="ai-icon">
                  <path
                    d="M32 38C31.448 38 31 38.448 31 39C31 39.552 31.448 40 32 40C32.552 40 33 39.552 33 39C33 38.448 32.552 38 32 38Z"
                    fill="url(#gradientStroke)"
                  />
                  <path
                    d="M40 32C39.448 32 39 32.448 39 33C39 33.552 39.448 34 40 34C40.552 34 41 33.552 41 33C41 32.448 40.552 32 40 32Z"
                    fill="url(#gradientStroke)"
                  />
                  <path
                    d="M48 38C47.448 38 47 38.448 47 39C47 39.552 47.448 40 48 40C48.552 40 49 39.552 49 39C49 38.448 48.552 38 48 38Z"
                    fill="url(#gradientStroke)"
                  />
                  <path d="M32 39L40 45L48 39" stroke="url(#gradientStroke)" strokeWidth="1.5" />
                </g>
                <defs>
                  <linearGradient
                    id="gradient"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                  <linearGradient
                    id="gradientStroke"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#d946ef" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>

        {/* Title */}
        <div className="title-section">
          <h1 className="app-title">Smart Files AI</h1>
          <p className="app-tagline">AI-powered file intelligence. Completely private.</p>
        </div>

        {/* Loading Steps */}
        <div className="steps-section">
          {steps.map((step, idx) => (
            <div
              key={step.id}
              className={`loading-step ${step.active ? 'active' : ''} ${
                step.completed ? 'completed' : ''
              }`}
              style={{
                animationDelay: `${idx * 0.15}s`,
              }}
            >
              <div className="step-indicator">
                {step.completed ? (
                  <svg
                    className="checkmark"
                    width="20"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                  >
                    <path
                      d="M17 6L8 15L3 10"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <div className="step-dot"></div>
                )}
              </div>
              <span className="step-label">{step.label}</span>
            </div>
          ))}
        </div>

        {/* Progress Bar */}
        <div className="progress-section">
          <div className="progress-track">
            <div
              className="progress-bar"
              style={{
                width: `${Math.min(progress, 100)}%`,
              }}
            ></div>
            <div className="progress-glow"></div>
          </div>
          <p className="progress-text">{Math.round(Math.min(progress, 100))}%</p>
        </div>

        {/* Trust Signals */}
        <div className="trust-signals">
          <div className="trust-item">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M8 1L10.39 6.26H16L11.81 9.74L14.2 15H8L3.81 11.26L6.2 6H1L3.39 1H8Z"
                fill="currentColor"
              />
            </svg>
            <span>Runs 100% locally</span>
          </div>
          <div className="trust-divider"></div>
          <div className="trust-item">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M8 1C4.14 1 1 4.14 1 8C1 11.86 4.14 15 8 15C11.86 15 15 11.86 15 8C15 4.14 11.86 1 8 1Z"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path d="M8 4V8L11 10" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <span>No cloud upload</span>
          </div>
          <div className="trust-divider"></div>
          <div className="trust-item">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M8 0C3.58 0 0 3.58 0 8C0 12.42 3.58 16 8 16C12.42 16 16 12.42 16 8C16 3.58 12.42 0 8 0Z"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path
                d="M7 10.5L5 8.5M9 10.5L7 8.5M7 5V6"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
            <span>Privacy-first by design</span>
          </div>
        </div>
      </div>
    </div>
  )
}
