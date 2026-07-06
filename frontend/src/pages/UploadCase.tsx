/**
 * LexOrch-KG — Upload Case Page
 * Drag & drop file upload with progress and pipeline trigger.
 */

import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Upload, File, X, CheckCircle, AlertCircle,
  FileText, Loader2, Brain, Scale,
} from 'lucide-react'
import { toast } from 'sonner'
import { casesApi } from '@/lib/api'

const uploadSchema = z.object({
  title: z.string().min(3, 'Title must be at least 3 characters').max(500),
  description: z.string().max(2000).optional(),
})
type UploadForm = z.infer<typeof uploadSchema>

const ALLOWED_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
const ALLOWED_EXT = ['.pdf', '.docx', '.txt']
const MAX_SIZE = 50 * 1024 * 1024 // 50MB

export default function UploadCase() {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const navigate = useNavigate()

  const { register, handleSubmit, formState: { errors } } = useForm<UploadForm>({
    resolver: zodResolver(uploadSchema),
  })

  const validateFile = (f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXT.includes(ext)) {
      return `File type not supported. Use: ${ALLOWED_EXT.join(', ')}`
    }
    if (f.size > MAX_SIZE) {
      return `File too large. Maximum size: 50MB`
    }
    return null
  }

  const handleFileDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      const error = validateFile(droppedFile)
      if (error) { toast.error(error); return }
      setFile(droppedFile)
    }
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      const error = validateFile(selectedFile)
      if (error) { toast.error(error); return }
      setFile(selectedFile)
    }
  }

  const onSubmit = async (formData: UploadForm) => {
    if (!file) { toast.error('Please select a file to upload'); return }

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(p => Math.min(p + 10, 85))
      }, 200)

      const fd = new FormData()
      fd.append('title', formData.title)
      if (formData.description) fd.append('description', formData.description)
      fd.append('file', file)

      const { data: caseData } = await casesApi.upload(fd)
      clearInterval(progressInterval)
      setUploadProgress(100)

      toast.success('Case uploaded successfully!')

      // Trigger AI pipeline
      setIsAnalyzing(true)
      await casesApi.analyze(caseData.id)
      toast.success('AI pipeline triggered! Analysis is running in the background.')

      setTimeout(() => navigate(`/cases/${caseData.id}`), 1000)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Upload failed. Please try again.')
      setUploadProgress(0)
    } finally {
      setIsUploading(false)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const fileIcon = file?.name.endsWith('.pdf') ? '📄' :
                   file?.name.endsWith('.docx') ? '📝' : '📃'

  return (
    <div className="max-w-3xl mx-auto animate-slide-up space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-dark-100">Upload Legal Case</h1>
        <p className="text-dark-400 mt-1">
          Upload a case document to begin AI-powered analysis
        </p>
      </div>

      {/* Disclaimer */}
      <div className="disclaimer-banner">
        <Scale className="w-4 h-4 flex-shrink-0" />
        <span className="text-xs">
          All AI analysis is for decision SUPPORT only.
          Human legal professionals must review all recommendations before any legal action.
        </span>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Case Details */}
        <div className="glass p-6 rounded-2xl space-y-4">
          <h2 className="font-semibold text-dark-100 flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary-400" />
            Case Information
          </h2>

          <div>
            <label className="text-sm text-dark-300 block mb-1.5">Case Title *</label>
            <input
              {...register('title')}
              className="input"
              placeholder="e.g., State vs. John Doe — Criminal Case No. 2024/001"
            />
            {errors.title && <p className="text-red-400 text-xs mt-1">{errors.title.message}</p>}
          </div>

          <div>
            <label className="text-sm text-dark-300 block mb-1.5">Description (Optional)</label>
            <textarea
              {...register('description')}
              className="input resize-none"
              rows={3}
              placeholder="Brief description of the case, jurisdiction, or special notes..."
            />
          </div>
        </div>

        {/* File Upload */}
        <div className="glass p-6 rounded-2xl">
          <h2 className="font-semibold text-dark-100 flex items-center gap-2 mb-4">
            <Upload className="w-4 h-4 text-primary-400" />
            Document Upload
          </h2>

          {/* Drop Zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleFileDrop}
            className={`
              relative border-2 border-dashed rounded-xl p-10 text-center transition-all
              ${isDragging
                ? 'border-primary-500 bg-primary-500/10'
                : file
                ? 'border-emerald-500/50 bg-emerald-500/5'
                : 'border-dark-600/50 hover:border-dark-500/80 hover:bg-dark-800/30'}
            `}
          >
            <input
              type="file"
              id="file-upload"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept=".pdf,.docx,.txt"
              onChange={handleFileInput}
            />

            {file ? (
              <div className="flex flex-col items-center gap-3">
                <div className="text-5xl">{fileIcon}</div>
                <div>
                  <p className="font-medium text-dark-200">{file.name}</p>
                  <p className="text-dark-400 text-sm mt-1">{formatSize(file.size)}</p>
                </div>
                <span className="badge badge-green">
                  <CheckCircle className="w-3 h-3" />
                  File selected
                </span>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setFile(null) }}
                  className="flex items-center gap-1 text-red-400 hover:text-red-300 text-xs transition-colors"
                >
                  <X className="w-3 h-3" /> Remove file
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 rounded-2xl bg-dark-700/60 flex items-center justify-center">
                  <Upload className="w-7 h-7 text-dark-400" />
                </div>
                <div>
                  <p className="font-medium text-dark-200">Drop your file here</p>
                  <p className="text-dark-400 text-sm mt-1">or click to browse</p>
                </div>
                <div className="flex gap-2">
                  {['PDF', 'DOCX', 'TXT'].map(ext => (
                    <span key={ext} className="badge badge-gray">{ext}</span>
                  ))}
                </div>
                <p className="text-dark-600 text-xs">Maximum 50MB · OCR applied for scanned PDFs</p>
              </div>
            )}
          </div>
        </div>

        {/* Upload Progress */}
        {isUploading && (
          <div className="glass p-4 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-dark-300">
                {isAnalyzing ? 'Triggering AI pipeline...' : 'Uploading document...'}
              </span>
              <span className="text-sm text-primary-400">{uploadProgress}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
            {isAnalyzing && (
              <div className="flex items-center gap-2 mt-3 text-sm text-emerald-400">
                <Brain className="w-4 h-4 animate-pulse" />
                <span>AI agents are being initialized...</span>
              </div>
            )}
          </div>
        )}

        {/* AI Pipeline Preview */}
        <div className="glass p-5 rounded-2xl">
          <h3 className="text-sm font-semibold text-dark-300 mb-3 flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary-400" />
            What happens after upload?
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[
              { label: 'Parse & OCR', step: 1 },
              { label: 'Extract Entities', step: 2 },
              { label: 'Build KG', step: 3 },
              { label: 'RAG Search', step: 4 },
              { label: 'Legal Reasoning', step: 5 },
              { label: 'Debate', step: 6 },
              { label: 'Explain', step: 7 },
              { label: 'Generate Report', step: 8 },
            ].map(({ label, step }) => (
              <div key={step} className="flex items-center gap-2 text-xs text-dark-400">
                <span className="w-5 h-5 rounded-full bg-primary-500/20 text-primary-400 flex items-center justify-center text-[10px] font-bold">
                  {step}
                </span>
                {label}
              </div>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isUploading || !file}
          className="btn-primary w-full justify-center py-4 text-base"
        >
          {isUploading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> Processing...</>
          ) : (
            <><Upload className="w-5 h-5" /> Upload & Analyze Case</>
          )}
        </button>
      </form>
    </div>
  )
}
