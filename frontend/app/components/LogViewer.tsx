'use client'

import React, { useRef, useEffect } from 'react'
import { TrashIcon, SignalIcon } from '@heroicons/react/24/outline'

interface LogMessage {
  type: 'log' | 'status'
  level?: 'info' | 'error' | 'warning'
  message: string
  timestamp: string
  data?: any
}

interface LogViewerProps {
  logs: LogMessage[]
  onClear: () => void
  isConnected: boolean
}

export default function LogViewer({ logs, onClear, isConnected }: LogViewerProps) {
  const logEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  const getLevelColor = (level?: string) => {
    switch (level) {
      case 'error': return 'text-red-600 bg-red-50'
      case 'warning': return 'text-yellow-600 bg-yellow-50'
      case 'info':
      default: return 'text-blue-600 bg-blue-50'
    }
  }

  const getLevelBadge = (level?: string) => {
    switch (level) {
      case 'error': return 'bg-red-500'
      case 'warning': return 'bg-yellow-500'
      case 'info':
      default: return 'bg-blue-500'
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-lg h-[600px] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <SignalIcon className="h-5 w-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Live Logs</h3>
          <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        </div>
        <button
          onClick={onClear}
          className="p-2 text-gray-400 hover:text-red-500 transition-colors"
          title="Clear logs"
        >
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Log Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-gray-50">
        {logs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <SignalIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No logs yet. Waiting for activity...</p>
          </div>
        ) : (
          logs.map((log, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg border-l-4 ${getLevelColor(log.level)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <div className={`h-2 w-2 rounded-full ${getLevelBadge(log.level)}`} />
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(log.timestamp)}
                    </span>
                    {log.level && (
                      <span className="text-xs font-medium text-gray-600 uppercase">
                        {log.level}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-800 break-words">
                    {log.message}
                  </p>
                  {log.data && (
                    <details className="mt-2">
                      <summary className="text-xs text-gray-500 cursor-pointer">
                        View details
                      </summary>
                      <pre className="text-xs text-gray-600 mt-1 p-2 bg-white rounded border overflow-auto">
                        {JSON.stringify(log.data, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{logs.length} log entries</span>
          <span className="flex items-center space-x-1">
            <div className={`h-1.5 w-1.5 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </span>
        </div>
      </div>
    </div>
  )
} 