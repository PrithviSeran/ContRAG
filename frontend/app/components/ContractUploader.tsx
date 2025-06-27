'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { DocumentArrowUpIcon, TrashIcon, PlayIcon } from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'
import axios from 'axios'

interface UploadedFile {
  file: File
  preview?: string
  error?: string
}

interface ContractUploaderProps {
  onUploadComplete: () => void
  onProcessingStart: () => void
  apiKey: string
}

export default function ContractUploader({ onUploadComplete, onProcessingStart, apiKey }: ContractUploaderProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      rejectedFiles.forEach((file) => {
        toast.error(`File "${file.file.name}" rejected: ${file.errors[0].message}`)
      })
    }

    // Add accepted files, but check for duplicates
    const newFiles = acceptedFiles.filter(file => {
      const exists = uploadedFiles.some(existing => existing.file.name === file.name && existing.file.size === file.size)
      if (exists) {
        toast.error(`File "${file.name}" is already selected`)
        return false
      }
      return true
    }).map(file => ({
      file,
      preview: file.name
    }))

    setUploadedFiles(prev => [...prev, ...newFiles])
  }, [uploadedFiles])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/html': ['.html', '.htm'],
      'text/plain': ['.txt']
    },
    multiple: true,
    maxSize: 10 * 1024 * 1024, // 10MB
  })

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const clearAllFiles = () => {
    setUploadedFiles([])
  }

  const uploadAndProcessFiles = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please select files to upload')
      return
    }

    if (!apiKey) {
      toast.error('Please set your Gemini API key first')
      return
    }

    setIsUploading(true)
    
    try {
      // Step 1: Clear any existing files in upload directory
      try {
        await axios.delete(
          'https://contrag.onrender.com/reset',
          {
            headers: {
              'X-API-Key': apiKey
            }
          }
        )
      } catch (error) {
        console.warn('Could not clear existing files:', error)
      }

      // Step 2: Upload files
      const formData = new FormData()
      uploadedFiles.forEach(({ file }) => {
        formData.append('files', file)
      })

      await axios.post(
        'https://contrag.onrender.com/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'X-API-Key': apiKey
          },
        }
      )

      toast.success(`Successfully uploaded ${uploadedFiles.length} files`)
      onUploadComplete()
      
      // Step 3: Start processing immediately
      setIsUploading(false)
      setIsProcessing(true)
      onProcessingStart() // This will trigger the loading screen

      const response = await axios.post(
        'https://contrag.onrender.com/process',
        {},
        {
          headers: {
            'X-API-Key': apiKey
          }
        }
      )

      toast.success('Processing started!')
      
      // Clear uploaded files since they're now being processed
      setUploadedFiles([])
      
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload and processing failed')
      console.error('Upload and processing error:', error)
    } finally {
      setIsUploading(false)
      setIsProcessing(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const isLoading = isUploading || isProcessing

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 space-y-6">
      <div className="text-center">
        <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h2 className="mt-2 text-xl font-semibold text-gray-900">Upload Contract Files</h2>
        <p className="mt-1 text-sm text-gray-600">
          Upload HTML, HTM, or TXT contract files for processing
        </p>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive 
            ? 'border-blue-400 bg-blue-50' 
            : isLoading 
            ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} disabled={isLoading} />
        <DocumentArrowUpIcon className={`mx-auto h-8 w-8 ${isLoading ? 'text-gray-300' : 'text-gray-400'}`} />
        {isDragActive ? (
          <p className="mt-2 text-blue-600">Drop the files here...</p>
        ) : (
          <div className="mt-2">
            <p className={`${isLoading ? 'text-gray-400' : 'text-gray-600'}`}>
              {isLoading ? 'Processing in progress...' : (
                <>
                  Drag & drop contract files here, or <span className="text-blue-600 font-medium">click to browse</span>
                </>
              )}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Supports: HTML, HTM, TXT files (max 10MB each)
            </p>
          </div>
        )}
      </div>

      {/* File List */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">Selected Files ({uploadedFiles.length})</h3>
            <button
              onClick={clearAllFiles}
              disabled={isLoading}
              className="text-sm text-red-600 hover:text-red-800 disabled:text-gray-400"
            >
              Clear All
            </button>
          </div>
          <div className="max-h-40 overflow-y-auto space-y-2">
            {uploadedFiles.map((uploadedFile, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {uploadedFile.file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(uploadedFile.file.size)}
                  </p>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  disabled={isLoading}
                  className="ml-2 p-1 text-red-500 hover:text-red-700 disabled:text-gray-300"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
          
          {/* Action Button */}
          <div className="pt-4">
            <button
              onClick={uploadAndProcessFiles}
              disabled={isLoading || uploadedFiles.length === 0}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-3 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>
                    {isUploading ? 'Uploading...' : 'Starting Processing...'}
                  </span>
                </>
              ) : (
                <>
                  <PlayIcon className="h-4 w-4" />
                  <span>Upload & Process Contracts</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
} 