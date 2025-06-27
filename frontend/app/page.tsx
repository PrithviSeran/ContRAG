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
  const [apiKey, setApiKey] = useState('')

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      const websocket = new WebSocket('ws://localhost:8000/ws')
      
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
        
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000)
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
  }, [])

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