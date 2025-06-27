'use client'

import React from 'react'
import { CheckCircleIcon, ExclamationTriangleIcon, PlayIcon } from '@heroicons/react/24/outline'

interface ProcessingStatusProps {
  status: {
    status: 'idle' | 'processing' | 'completed' | 'error'
    progress: number
    current_file?: string
    total_files: number
    processed_files: number
    message: string
    job_id?: string
  }
}

export default function ProcessingStatus({ status }: ProcessingStatusProps) {
  const getStatusColor = () => {
    switch (status.status) {
      case 'processing': return 'text-blue-600'
      case 'completed': return 'text-green-600'
      case 'error': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'processing': return <PlayIcon className="h-6 w-6" />
      case 'completed': return <CheckCircleIcon className="h-6 w-6" />
      case 'error': return <ExclamationTriangleIcon className="h-6 w-6" />
      default: return <PlayIcon className="h-6 w-6" />
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className={getStatusColor()}>
          {getStatusIcon()}
        </div>
        <h2 className="text-xl font-semibold text-gray-900">Processing Status</h2>
      </div>

      <div className="space-y-4">
        {/* Progress Bar */}
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{status.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-300 ${
                status.status === 'error' ? 'bg-red-500' :
                status.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${status.progress}%` }}
            />
          </div>
        </div>

        {/* File Progress */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Files Processed:</span>
          <span className="font-medium">{status.processed_files} / {status.total_files}</span>
        </div>

        {/* Current File */}
        {status.current_file && (
          <div>
            <span className="text-sm text-gray-600">Current File:</span>
            <div className="mt-1 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium text-blue-900 truncate">
                {status.current_file}
              </p>
            </div>
          </div>
        )}

        {/* Status Message */}
        <div>
          <span className="text-sm text-gray-600">Status:</span>
          <div className="mt-1 p-3 bg-gray-50 rounded-lg">
            <p className={`text-sm font-medium ${getStatusColor()}`}>
              {status.message}
            </p>
          </div>
        </div>

        {/* Job ID */}
        {status.job_id && (
          <div className="text-xs text-gray-500">
            Job ID: {status.job_id}
          </div>
        )}
      </div>

      {/* Processing Animation */}
      {status.status === 'processing' && (
        <div className="mt-4 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-sm text-gray-600">Processing contracts...</span>
        </div>
      )}
    </div>
  )
} 