'use client'

import React, { useState, useEffect } from 'react'
import { KeyIcon, EyeIcon, EyeSlashIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'

interface ApiKeySettingsProps {
  onApiKeyChange?: (apiKey: string) => void
}

export default function ApiKeySettings({ onApiKeyChange }: ApiKeySettingsProps) {
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [isValid, setIsValid] = useState<boolean | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  // Load API key from localStorage on component mount
  useEffect(() => {
    const savedApiKey = localStorage.getItem('gemini_api_key')
    if (savedApiKey) {
      setApiKey(savedApiKey)
      setIsValid(true) // Assume it's valid if it was saved
      onApiKeyChange?.(savedApiKey)
    }
  }, [onApiKeyChange])

  const handleApiKeyChange = (value: string) => {
    setApiKey(value)
    setIsValid(null) // Reset validation status when key changes
    
    // Save to localStorage
    if (value) {
      localStorage.setItem('gemini_api_key', value)
    } else {
      localStorage.removeItem('gemini_api_key')
    }
    
    onApiKeyChange?.(value)
  }

  const validateApiKey = async () => {
    if (!apiKey.trim()) {
      toast.error('Please enter an API key')
      return
    }

    setIsValidating(true)
    try {
      // Test the API key by making a simple request to the backend
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://contrag.onrender.com'}/validate-api-key`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ api_key: apiKey }),
        }
      )

      if (response.ok) {
        setIsValid(true)
        toast.success('API key is valid!')
      } else {
        setIsValid(false)
        toast.error('Invalid API key')
      }
    } catch (error) {
      setIsValid(false)
      toast.error('Failed to validate API key')
      console.error('API key validation error:', error)
    } finally {
      setIsValidating(false)
    }
  }

  const clearApiKey = () => {
    setApiKey('')
    setIsValid(null)
    localStorage.removeItem('gemini_api_key')
    onApiKeyChange?.('')
    toast.success('API key cleared')
  }

  const getStatusIcon = () => {
    if (isValid === true) {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />
    } else if (isValid === false) {
      return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
    }
    return <KeyIcon className="h-5 w-5 text-gray-400" />
  }

  const getStatusColor = () => {
    if (isValid === true) return 'border-green-300 focus:ring-green-500 focus:border-green-500'
    if (isValid === false) return 'border-red-300 focus:ring-red-500 focus:border-red-500'
    return 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 space-y-4">
      <div className="flex items-center space-x-3">
        <KeyIcon className="h-6 w-6 text-blue-600" />
        <h2 className="text-xl font-semibold text-gray-900">API Configuration</h2>
      </div>
      
      <div className="space-y-4">
        <div>
          <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 mb-2">
            Google Gemini API Key
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              {getStatusIcon()}
            </div>
            <input
              id="api-key"
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder="Enter your Gemini API key..."
              className={`block w-full pl-10 pr-20 py-3 border rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 ${getStatusColor()}`}
            />
            <div className="absolute inset-y-0 right-0 flex items-center space-x-1 pr-3">
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
              >
                {showApiKey ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
          
          {isValid === true && (
            <p className="mt-2 text-sm text-green-600 flex items-center">
              <CheckCircleIcon className="h-4 w-4 mr-1" />
              API key is valid and ready to use
            </p>
          )}
          
          {isValid === false && (
            <p className="mt-2 text-sm text-red-600 flex items-center">
              <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
              Invalid API key. Please check and try again.
            </p>
          )}
          
          <p className="mt-2 text-xs text-gray-500">
            Get your free API key from{' '}
            <a
              href="https://makersuite.google.com/app/apikey"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 underline"
            >
              Google AI Studio
            </a>
          </p>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={validateApiKey}
            disabled={!apiKey.trim() || isValidating}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
          >
            {isValidating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Validating...</span>
              </>
            ) : (
              <>
                <CheckCircleIcon className="h-4 w-4" />
                <span>Validate Key</span>
              </>
            )}
          </button>
          
          <button
            onClick={clearApiKey}
            disabled={!apiKey}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
          >
            Clear
          </button>
        </div>
      </div>
      
      <div className="bg-blue-50 p-4 rounded-lg">
        <div className="flex items-start space-x-3">
          <KeyIcon className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-blue-900 mb-1">Security Note</p>
            <p className="text-blue-800">
              Your API key is stored locally in your browser and is only sent to the processing server. 
              It is never stored on our servers or shared with third parties.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
} 