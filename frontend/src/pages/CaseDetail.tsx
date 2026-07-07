/**
 * LexOrch-KG — Case Detail Page
 * Overview, navigation to sub-pages (timeline, graph, debate, explainability, reports).
 */

import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Network, GitBranch, MessageSquare, Lightbulb, FileText,
  Zap, CheckCircle, AlertCircle, Clock, ChevronRight,
  FolderOpen, Brain, Scale, Play,
} from 'lucide-react'
import { format } from 'date-fns'
import { casesApi } from '@/lib/api'
import { toast } from 'sonner'

const statusConfig: Record<string, { color: string; label: string; icon: typeof CheckCircle }> = {
  uploaded:   { color: 'badge-blue',   label: 'Uploaded',   icon: Clock },
  processing: { color: 'badge-yellow', label: 'Processing', icon: Zap },
  completed:  { color: 'badge-green',  label: 'Completed',  icon: CheckCircle },
  failed:     { color: 'badge-red',    label: 'Failed',     icon: AlertCircle },
}

const analysisLinks = [
  { to: 'timeline', icon: GitBranch,      label: 'Agent Timeline',     desc: 'View step-by-step agent execution' },
  { to: 'graph',    icon: Network,        label: 'Knowledge Graph',     desc: 'Visualize entity relationships' },
  { to: 'debate',   icon: MessageSquare,  label: 'Debate Viewer',       desc: 'Prosecution vs Defense arguments' },
  { to: 'explain',  icon: Lightbulb,      label: 'Explainability',      desc: 'Why this recommendation was made' },
  { to: 'reports',  icon: FileText,       label: 'Reports',             desc: 'Download PDF / JSON / HTML' },
]

export default function CaseDetail() {
  const { id } = useParams<{ id: string }>()

  const { data: caseData, isLoading, refetch } = useQuery({
    queryKey: ['case', id],
    queryFn: async () => {
      const { data } = await casesApi.get(id!)
      return data
    },
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.status
      return status === 'processing' || status === 'analyzing' || status === 'debating' ? 5000 : false
    },
  })

  const handleReanalyze = async () => {
    try {
      await casesApi.analyze(id!)
      toast.success('Re-analysis triggered!')
      refetch()
    } catch {
      toast.error('Failed to trigger analysis')
    }
  }

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <div className="spinner" style={{ width: 40, height: 40 }} />
    </div>
  )

  if (!caseData) return (
    <div className="text-center py-20">
      <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
      <p className="text-dark-400">Case not found</p>
    </div>
  )

  const sc = statusConfig[caseData.status] || statusConfig.uploaded
  const StatusIcon = sc.icon
  const meta = caseData.metadata_

  return (
    <div className="space-y-6 max-w-6xl animate-slide-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary-500/15 flex items-center justify-center flex-shrink-0">
            <FolderOpen className="w-6 h-6 text-primary-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-dark-100 leading-snug">{caseData.title}</h1>
            {caseData.description && (
              <p className="text-dark-400 text-sm mt-1">{caseData.description}</p>
            )}
            <div className="flex items-center gap-3 mt-2">
              <span className={`badge ${sc.color}`}>
                <StatusIcon className="w-3 h-3" />
                {sc.label}
              </span>
              <span className="badge badge-gray">{caseData.file_type.toUpperCase()}</span>
              <span className="text-dark-500 text-xs">
                Uploaded {format(new Date(caseData.created_at), 'MMM d, yyyy h:mm a')}
              </span>
            </div>
          </div>
        </div>
        <button onClick={handleReanalyze} className="btn-secondary text-sm flex-shrink-0">
          <Play className="w-4 h-4" />
          Re-Analyze
        </button>
      </div>

      {/* Disclaimer */}
      <div className="disclaimer-banner">
        <Scale className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <span className="text-xs">
          AI analysis complete. All recommendations require human expert review.
          This is a decision support tool only — not a substitute for legal judgment.
        </span>
      </div>

      {/* Document Stats */}
      {meta && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Pages', value: meta.page_count ?? '—' },
            { label: 'Words', value: meta.word_count?.toLocaleString() ?? '—' },
            { label: 'Chunks', value: meta.chunks_count ?? '—' },
            { label: 'OCR Applied', value: meta.ocr_applied ? 'Yes' : 'No' },
          ].map(({ label, value }) => (
            <div key={label} className="glass p-4 rounded-xl">
              <div className="text-lg font-bold text-dark-100">{value}</div>
              <div className="text-dark-500 text-xs mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {meta?.summary && (
        <div className="glass p-6 rounded-2xl">
          <h2 className="font-semibold text-dark-100 flex items-center gap-2 mb-3">
            <Brain className="w-4 h-4 text-primary-400" />
            AI Case Summary
          </h2>
          <p className="text-dark-300 text-sm leading-relaxed">{meta.summary}</p>
        </div>
      )}

      {/* Key Facts */}
      {meta?.key_facts?.length > 0 && (
        <div className="glass p-6 rounded-2xl">
          <h2 className="font-semibold text-dark-100 mb-3">Key Facts</h2>
          <ol className="space-y-2">
            {meta.key_facts.map((fact: string, i: number) => (
              <li key={i} className="flex gap-3 text-sm text-dark-300">
                <span className="w-5 h-5 rounded-full bg-primary-500/20 text-primary-400 text-xs flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                {fact}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Analysis Navigation */}
      <div>
        <h2 className="font-semibold text-dark-100 mb-4">Analysis Results</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {analysisLinks.map(({ to, icon: Icon, label, desc }) => (
            <Link
              key={to}
              to={`/cases/${id}/${to}`}
              className="card group hover:border-primary-500/40"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-lg bg-primary-500/15 flex items-center justify-center">
                  <Icon className="w-4 h-4 text-primary-400" />
                </div>
                <span className="font-medium text-dark-200 group-hover:text-white transition-colors">
                  {label}
                </span>
                <ChevronRight className="w-4 h-4 text-dark-600 group-hover:text-primary-400 ml-auto transition-colors" />
              </div>
              <p className="text-dark-500 text-xs">{desc}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Agent Executions */}
      {caseData.agent_executions?.length > 0 && (
        <div className="glass p-6 rounded-2xl">
          <h2 className="font-semibold text-dark-100 mb-4 flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-primary-400" />
            Agent Pipeline Status
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {caseData.agent_executions.map((exec: any) => (
              <div key={exec.id} className="flex items-center gap-2 text-sm">
                {exec.status === 'completed' ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                ) : exec.status === 'failed' ? (
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                ) : (
                  <Zap className="w-4 h-4 text-yellow-400 flex-shrink-0 animate-pulse" />
                )}
                <span className="text-dark-400 truncate">{exec.agent_name.replace('Agent', '')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
