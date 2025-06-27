'use client'

import React, { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon, UserIcon, CpuChipIcon } from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'
import axios from 'axios'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatInterfaceProps {
  apiKey: string
}

export default function ChatInterface({ apiKey }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Remove automatic scrolling - let user control scroll position
  // useEffect(() => {
  //   // Disabled automatic scrolling to prevent unwanted scroll behavior
  // }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    if (!apiKey) {
      toast.error('Please set your Gemini API key first')
      return
    }

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await axios.post(
        'https://contrag.onrender.com/chat',
        { message: userMessage.content },
        {
          headers: {
            'X-API-Key': apiKey
          }
        }
      )

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send message')
      console.error('Chat error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="bg-white rounded-xl shadow-lg h-[600px] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <CpuChipIcon className="h-6 w-6 text-blue-600" />
          <h3 className="font-semibold text-gray-900">Contract Analysis Chat</h3>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Ask questions about your processed contracts
        </p>
      </div>

      {/* Messages */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-full p-4 w-20 h-20 mx-auto mb-4 flex items-center justify-center">
              <CpuChipIcon className="h-10 w-10 text-blue-600" />
            </div>
            <p className="text-xl font-semibold text-gray-700 mb-2">🎉 Your contracts are ready!</p>
            <p className="text-sm text-gray-600 mb-4">I've analyzed your contracts and I'm ready to answer questions.</p>
            <div className="mt-6 space-y-2 text-left max-w-lg mx-auto">
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-xl border border-blue-100">
                <p className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <span className="mr-2">💡</span>
                  Try asking me:
                </p>
                                 <div className="grid grid-cols-1 gap-2">
                   <button 
                     onClick={() => setInputMessage("What are the key terms of the securities purchase agreements?")}
                     className="bg-white p-2 rounded-lg text-xs text-gray-600 hover:bg-blue-50 transition-colors cursor-pointer border text-left"
                   >
                     "What are the key terms of the securities purchase agreements?"
                   </button>
                   <button 
                     onClick={() => setInputMessage("Who are the main parties involved across all contracts?")}
                     className="bg-white p-2 rounded-lg text-xs text-gray-600 hover:bg-blue-50 transition-colors cursor-pointer border text-left"
                   >
                     "Who are the main parties involved across all contracts?"
                   </button>
                   <button 
                     onClick={() => setInputMessage("What types of securities were issued and when?")}
                     className="bg-white p-2 rounded-lg text-xs text-gray-600 hover:bg-blue-50 transition-colors cursor-pointer border text-left"
                   >
                     "What types of securities were issued and when?"
                   </button>
                   <button 
                     onClick={() => setInputMessage("Summarize the closing conditions across contracts")}
                     className="bg-white p-2 rounded-lg text-xs text-gray-600 hover:bg-blue-50 transition-colors cursor-pointer border text-left"
                   >
                     "Summarize the closing conditions across contracts"
                   </button>
                 </div>
              </div>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex items-start space-x-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <CpuChipIcon className="h-4 w-4 text-white" />
                  </div>
                </div>
              )}
              
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p
                  className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}
                >
                  {formatTime(message.timestamp)}
                </p>
              </div>

              {message.role === 'user' && (
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-gray-300 rounded-full flex items-center justify-center">
                    <UserIcon className="h-4 w-4 text-gray-600" />
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center">
                <CpuChipIcon className="h-4 w-4 text-white" />
              </div>
            </div>
            <div className="bg-gray-100 px-4 py-3 rounded-lg">
              <div className="flex space-x-1">
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your contracts..."
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
          >
            <PaperAirplaneIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
} 