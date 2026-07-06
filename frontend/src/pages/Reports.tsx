/**
 * LexOrch-KG — Reports Page
 * List and download PDF, JSON, HTML reports for a case.
 */

import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FileText, Download, AlertCircle, Clock, CheckCircle } from 'lucide-react'
import { format } from 'date-fns'
import { reportsApi } from '@/lib/api'
import { toast } from 'sonner'

const formatConfig: Record<string, { icon: string; color: string; label: string }> = {
  pdf:  { icon: '📄', color: 'badge-red',   label: 'PDF Report' },
  json: { icon: '📊', color: 'badge-blue',  label: 'JSON Data' },
  html: { icon: '🌐', color: 'badge-green', label: 'HTML Report' },
}

export default function Reports() {
  const { id } = useParams<{ id: string }>()

  const { data: reports, isLoading } = useQuery({
    queryKey: ['reports', id],
    queryFn: async () => {
      const { data } = await reportsApi.list(id!)
      return data
    },
  })

  const handleDownload = async (reportId: string, format: string, caseId: string) => {
    try {
      const { data } = await reportsApi.download(reportId)
      const url = window.URL.createObjectURL(new Blob([data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `lexorch_report_${caseId.substring(0, 8)}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      toast.success(`${format.toUpperCase()} report downloaded!`)
    } catch {
      toast.error('Failed to download report')
    }
  }

  return (
    <div className="space-y-6 animate-slide-up max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-dark-100 flex items-center gap-2">
          <FileText className="w-6 h-6 text-primary-400" />
          Case Reports
        </h1>
        <p className="text-dark-400 mt-0.5 text-sm">
          Download professional reports in PDF, JSON, or HTML format
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => (
            <div key={i} className="glass p-5 rounded-xl animate-pulse">
              <div className="h-5 bg-dark-700 rounded w-1/3 mb-2" />
              <div className="h-3 bg-dark-800 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : !reports?.length ? (
        <div className="text-center py-16">
          <FileText className="w-10 h-10 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">No reports generated yet</p>
          <p className="text-dark-600 text-sm">Reports are generated at the end of the AI pipeline</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report: any) => {
            const fc = formatConfig[report.format] || { icon: '📁', color: 'badge-gray', label: report.format }
            return (
              <div key={report.id} className="glass p-5 rounded-xl flex items-center gap-4 group hover:border-primary-500/30 transition-all">
                <div className="text-3xl">{fc.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-dark-200">{fc.label}</h3>
                    <span className={`badge ${fc.color} text-[10px]`}>{report.format.toUpperCase()}</span>
                  </div>
                  <p className="text-dark-500 text-xs">
                    Generated {format(new Date(report.created_at), 'MMM d, yyyy h:mm a')}
                    {report.file_size_bytes && (
                      <> · {(report.file_size_bytes / 1024).toFixed(0)} KB</>
                    )}
                    {report.download_count > 0 && (
                      <> · {report.download_count} downloads</>
                    )}
                  </p>
                </div>
                <button
                  onClick={() => handleDownload(report.id, report.format, id!)}
                  className="btn-primary text-sm py-2 px-4 flex-shrink-0"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>
            )
          })}

          {/* Info */}
          <div className="glass-light p-4 rounded-xl">
            <p className="text-dark-500 text-xs">
              📋 All reports include the mandatory legal disclaimer that AI recommendations
              are for decision support only and require human expert review.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
