'use client'

import { DocumentTextIcon, ServerIcon } from '@heroicons/react/24/outline'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid'

interface HeaderProps {
  isConnected: boolean
}

export default function Header({ isConnected }: HeaderProps) {
  return (
    <header className="gradient-bg text-white shadow-lg">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <DocumentTextIcon className="h-8 w-8" />
            <div>
              <h1 className="text-2xl font-bold">GraphRAG Contract Processor</h1>
              <p className="text-blue-100">AI-powered contract analysis and knowledge graph generation</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <ServerIcon className="h-5 w-5" />
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <>
                  <CheckCircleIcon className="h-5 w-5 text-green-300" />
                  <span className="text-sm">Connected</span>
                </>
              ) : (
                <>
                  <XCircleIcon className="h-5 w-5 text-red-300" />
                  <span className="text-sm">Disconnected</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
} 