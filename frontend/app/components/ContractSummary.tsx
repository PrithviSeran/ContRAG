'use client'

import React, { useState, useEffect } from 'react'
import { DocumentTextIcon, ArrowDownTrayIcon, UsersIcon, BanknotesIcon, ClockIcon, ArchiveBoxIcon } from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'
import axios from 'axios'

interface Contract {
  title: string
  contract_type: string
  summary: string
  execution_date?: string
  parties_count: number
  securities_count: number
  file_path: string
}

interface ContractData {
  current_session: {
    contracts: Contract[]
    total: number
  }
  all_contracts: {
    contracts: Contract[]
    total: number
  }
  contracts: Contract[]
  total: number
}

export default function ContractSummary() {
  const [contractData, setContractData] = useState<ContractData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDownloading, setIsDownloading] = useState(false)
  const [viewMode, setViewMode] = useState<'current' | 'all'>('current')

  useEffect(() => {
    fetchContracts()
  }, [])

  const fetchContracts = async () => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://contrag.onrender.com'}/contracts/summary`
      )
      setContractData(response.data)
    } catch (error: any) {
      toast.error('Failed to fetch contract summary')
      console.error('Fetch error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const downloadProcessedData = async () => {
    setIsDownloading(true)
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://contrag.onrender.com'}/download/processed-data`,
        { responseType: 'blob' }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `processed_contracts_${new Date().toISOString().split('T')[0]}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      toast.success('Download started!')
    } catch (error: any) {
      toast.error('Failed to download data')
      console.error('Download error:', error)
    } finally {
      setIsDownloading(false)
    }
  }

  const downloadBackup = async () => {
    setIsDownloading(true)
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://contrag.onrender.com'}/download/backup`,
        { responseType: 'blob' }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `neo4j_backup_${new Date().toISOString().split('T')[0]}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      toast.success('Backup download started!')
    } catch (error: any) {
      toast.error('Failed to download backup')
      console.error('Backup download error:', error)
    } finally {
      setIsDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!contractData) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="text-center py-8 text-gray-500">
          <DocumentTextIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Failed to load contract data</p>
        </div>
      </div>
    )
  }

  const currentContracts = contractData.current_session.contracts
  const allContracts = contractData.all_contracts.contracts
  const displayContracts = viewMode === 'current' ? currentContracts : allContracts

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <DocumentTextIcon className="h-6 w-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Contract Analysis Results</h2>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={downloadProcessedData}
            disabled={isDownloading}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors text-sm"
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            <span>Download Data</span>
          </button>
          
          <button
            onClick={downloadBackup}
            disabled={isDownloading}
            className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors text-sm"
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            <span>Download Backup</span>
          </button>
        </div>
      </div>

      {/* View Mode Toggle */}
      <div className="flex items-center space-x-2 mb-6 p-1 bg-gray-100 rounded-lg">
        <button
          onClick={() => setViewMode('current')}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            viewMode === 'current'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <ClockIcon className="h-4 w-4" />
          <span>This Session ({contractData.current_session.total})</span>
        </button>
        <button
          onClick={() => setViewMode('all')}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            viewMode === 'all'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <ArchiveBoxIcon className="h-4 w-4" />
          <span>All Contracts ({contractData.all_contracts.total})</span>
        </button>
      </div>

      {displayContracts.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <DocumentTextIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>
            {viewMode === 'current' 
              ? 'No contracts processed in this session yet' 
              : 'No contracts found in database'
            }
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2">
                <DocumentTextIcon className="h-5 w-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">
                  {viewMode === 'current' ? 'Session' : 'Total'} Contracts
                </span>
              </div>
              <p className="text-2xl font-bold text-blue-600 mt-1">{displayContracts.length}</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2">
                <UsersIcon className="h-5 w-5 text-green-600" />
                <span className="text-sm font-medium text-green-900">Total Parties</span>
              </div>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {displayContracts.reduce((sum, contract) => sum + contract.parties_count, 0)}
              </p>
            </div>
            
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2">
                <BanknotesIcon className="h-5 w-5 text-purple-600" />
                <span className="text-sm font-medium text-purple-900">Total Securities</span>
              </div>
              <p className="text-2xl font-bold text-purple-600 mt-1">
                {displayContracts.reduce((sum, contract) => sum + contract.securities_count, 0)}
              </p>
            </div>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {displayContracts.map((contract, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">{contract.title}</h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        {contract.contract_type}
                      </span>
                      {contract.execution_date && (
                        <span>{new Date(contract.execution_date).toLocaleDateString()}</span>
                      )}
                    </div>
                    {contract.summary && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">{contract.summary}</p>
                    )}
                    <div className="flex items-center space-x-4 text-xs text-gray-500 mt-2">
                      <span>{contract.parties_count} parties</span>
                      <span>{contract.securities_count} securities</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 