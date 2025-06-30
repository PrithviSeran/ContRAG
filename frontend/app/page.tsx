'use client'

import { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import ContractUploader from './components/ContractUploader'
import ProcessingStatus from './components/ProcessingStatus'
import ChatInterface from './components/ChatInterface'
import ContractSummary from './components/ContractSummary'
import LogViewer from './components/LogViewer'
import Header from './components/Header'
import ApiKeySettings from './components/ApiKeySettings'

export type ProcessingState = 'idle' | 'processing' | 'completed' | 'error'

export interface ProcessingStatus {
  status: ProcessingState
  progress: number
  current_file?: string
  total_files: number
  processed_files: number
  message: string
  job_id?: string
}

export interface LogMessage {
  type: 'log' | 'status'
  level?: 'info' | 'error' | 'warning'
  message: string
  timestamp: string
  data?: any
}

export default function Home() {
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
    status: 'idle',
    progress: 0,
    total_files: 0,
    processed_files: 0,
    message: 'Ready to process contracts'
  })
  
  const [logs, setLogs] = useState<LogMessage[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isServerStarting, setIsServerStarting] = useState(true)
  const [serverConnectionAttempts, setServerConnectionAttempts] = useState(0)
  const [apiKey, setApiKey] = useState('')

  // Server health check function
  const checkServerHealth = async () => {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const response = await fetch('https://contrag.onrender.com/health', {
        method: 'GET',
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)
      
      if (response.ok) {
        setIsServerStarting(false)
        return true
      }
      return false
    } catch (error) {
      console.log('Server health check failed:', error)
      return false
    }
  }

  // Initial server connection check
  useEffect(() => {
    const initialServerCheck = async () => {
      console.log('Checking server availability...')
      
      const isHealthy = await checkServerHealth()
      
      if (!isHealthy) {
        // Server not ready, start polling
        const checkInterval = setInterval(async () => {
          setServerConnectionAttempts(prev => prev + 1)
          const healthy = await checkServerHealth()
          
          if (healthy) {
            clearInterval(checkInterval)
            setIsServerStarting(false)
            console.log('Server is now available!')
          }
        }, 5000) // Check every 5 seconds

        // Timeout after 3 minutes
        setTimeout(() => {
          clearInterval(checkInterval)
          if (isServerStarting) {
            setIsServerStarting(false)
            console.warn('Server health check timeout - proceeding anyway')
          }
        }, 180000) // 3 minutes

        return () => clearInterval(checkInterval)
      }
    }

    initialServerCheck()
  }, [])

  // WebSocket connection for real-time updates
  useEffect(() => {
    // Don't try to connect WebSocket until server is available
    if (isServerStarting) return

    const connectWebSocket = () => {
      const apiBaseUrl = 'https://contrag.onrender.com'

      console.log('Connecting to WebSocket:', apiBaseUrl)
      const wsUrl = apiBaseUrl.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws'
      const websocket = new WebSocket(wsUrl)
      
      websocket.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setWs(websocket)
      }
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'log') {
          setLogs(prev => [...prev, data])
        } else if (data.type === 'status') {
          setProcessingStatus(data.data)
        }
      }
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        setWs(null)
        
        // Attempt to reconnect after 3 seconds (only if server is not starting)
        if (!isServerStarting) {
          setTimeout(connectWebSocket, 3000)
        }
      }
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }
    }
    
    connectWebSocket()
    
    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [isServerStarting])

  // Load API key from localStorage on page load
  useEffect(() => {
    const savedApiKey = localStorage.getItem('gemini_api_key')
    if (savedApiKey) {
      setApiKey(savedApiKey)
    }
  }, [])

  const clearLogs = () => {
    setLogs([])
  }

  const showUploader = processingStatus.status === 'idle'
  const showProcessing = processingStatus.status === 'processing'
  const showResults = processingStatus.status === 'completed'
  const showApiKeySettings = processingStatus.status === 'idle' && !apiKey

  // Show server connection loading screen
  if (isServerStarting) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <Header isConnected={false} />
        
        <main className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center min-h-[500px]">
            <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
              <div className="mb-6">
                <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Connecting to Server</h2>
                <p className="text-gray-600 mb-4">
                  Please wait while we establish connection to the backend server.
                </p>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="text-sm text-blue-800 text-left">
                    <p className="font-medium mb-1">First-time connection may take 2-3 minutes</p>
                    <p>Our server is hosted on Render and may need a moment to start up if it hasn't been used recently. Thank you for your patience!</p>
                  </div>
                </div>
              </div>
              
              
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header isConnected={isConnected} />
      
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* API Key Settings - Show when no API key is set */}
            {showApiKeySettings && (
              <div className="animate-fade-in">
                <ApiKeySettings onApiKeyChange={setApiKey} />
              </div>
            )}

            {/* Upload Section */}
            {showUploader && apiKey && (
              <div className="animate-fade-in">
                <ContractUploader 
                  onUploadComplete={() => {
                    // Optionally refresh status
                  }}
                  onProcessingStart={() => {
                    // Update processing status to show loading screen
                    setProcessingStatus(prev => ({
                      ...prev,
                      status: 'processing',
                      progress: 0,
                      message: 'Starting contract processing...'
                    }))
                  }}
                  apiKey={apiKey}
                />
              </div>
            )}
            
            {/* Processing Section */}
            {showProcessing && (
              <div className="animate-fade-in">
                <ProcessingStatus status={processingStatus} />
              </div>
            )}
            
            {/* Results Section */}
            {showResults && (
              <div className="animate-fade-in space-y-8">
                {/* Primary: Chat Interface */}
                <div className="relative">
                  <div className="absolute -top-3 left-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-3 py-1 rounded-full text-xs font-medium">
                    🤖 AI Assistant Ready
                  </div>
                  <ChatInterface apiKey={apiKey} />
                </div>
                
                {/* Secondary: Contract Overview */}
                <div className="relative">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="h-px bg-gradient-to-r from-gray-300 via-gray-200 to-transparent flex-1"></div>
                    <span className="text-sm font-medium text-gray-500 bg-gray-50 px-4 py-2 rounded-full">
                      📊 Contract Overview
                    </span>
                    <div className="h-px bg-gradient-to-l from-gray-300 via-gray-200 to-transparent flex-1"></div>
                  </div>
                  <ContractSummary />
                </div>
              </div>
            )}
          </div>
          
          {/* Sidebar - Log Viewer */}
          <div className="lg:col-span-1">
            <LogViewer 
              logs={logs} 
              onClear={clearLogs}
              isConnected={isConnected}
            />
          </div>
        </div>
      </main>
      
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />
    </div>
  )
} 