/**
 * LexOrch-KG — Agent Timeline Page
 * Step-by-step execution view of the AI pipeline.
 */

import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle, Clock, Zap, Brain, GitBranch } from 'lucide-react'
import { casesApi } from '@/lib/api'

const AGENT_META: Record<string, { icon: typeof Brain; color: string; desc: string }> = {
  CaseUnderstandingAgent: { icon: Brain, color: '#3a70f5', desc: 'Extracts text, applies OCR, chunks document, generates summary' },
  EntityExtractionAgent:  { icon: Brain, color: '#8b5cf6', desc: 'Identifies judges, courts, laws, evidence, dates using spaCy + LLM' },
  KnowledgeGraphAgent:    { icon: GitBranch, color: '#10b981', desc: 'Inserts entities into Neo4j, creates relationships' },
  RetrievalAgent:         { icon: Brain, color: '#f59e0b', desc: 'Encodes chunks in ChromaDB, retrieves similar precedents via RAG' },
  ReasoningAgent:         { icon: Brain, color: '#ef4444', desc: 'Applies legal logic, compares precedents, generates reasoning' },
  DebateAgent:            { icon: Brain, color: '#06b6d4', desc: 'Prosecution, Defense, Judge, Consensus sub-agents debate the case' },
  ExplainabilityAgent:    { icon: Brain, color: '#6366f1', desc: 'Generates XAI explanation with confidence breakdown and disclaimer' },
  ReportAgent:            { icon: Brain, color: '#84cc16', desc: 'Creates professional PDF, JSON, and HTML reports' },
}

export default function AgentTimeline() {
  const { id } = useParams<{ id: string }>()

  const { data: caseData, isLoading } = useQuery({
    queryKey: ['case', id],
    queryFn: async () => {
      const { data } = await casesApi.get(id!)
      return data
    },
    refetchInterval: 5000,
  })

  const executions = (caseData?.agent_executions || []).sort(
    (a: any, b: any) => a.agent_step - b.agent_step
  )

  return (
    <div className="space-y-6 animate-slide-up max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-dark-100 flex items-center gap-2">
          <GitBranch className="w-6 h-6 text-primary-400" />
          Agent Execution Timeline
        </h1>
        <p className="text-dark-400 mt-0.5 text-sm">
          Step-by-step AI pipeline execution for this case
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="flex gap-4 animate-pulse">
              <div className="w-10 h-10 rounded-full bg-dark-700" />
              <div className="flex-1 space-y-2 pt-2">
                <div className="h-4 bg-dark-700 rounded w-1/2" />
                <div className="h-3 bg-dark-800 rounded w-3/4" />
              </div>
            </div>
          ))}
        </div>
      ) : executions.length === 0 ? (
        <div className="text-center py-16">
          <Clock className="w-10 h-10 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">Pipeline not yet started</p>
          <p className="text-dark-600 text-sm">Go back and click "Re-Analyze" to start</p>
        </div>
      ) : (
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-5 top-5 bottom-5 w-0.5 bg-dark-700/60" />

          <div className="space-y-6">
            {executions.map((exec: any, idx: number) => {
              const meta = AGENT_META[exec.agent_name] || { icon: Brain, color: '#64748b', desc: '' }
              const Icon = meta.icon

              const isCompleted = exec.status === 'completed'
              const isFailed    = exec.status === 'failed'
              const isRunning   = exec.status === 'running'

              return (
                <div key={exec.id} className="flex gap-4 relative animate-slide-up" style={{ animationDelay: `${idx * 50}ms` }}>
                  {/* Step dot */}
                  <div
                    className={`
                      relative z-10 w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
                      border-2 transition-all
                      ${isCompleted ? 'border-emerald-500 bg-emerald-500/20'
                        : isFailed  ? 'border-red-500 bg-red-500/20'
                        : isRunning ? 'border-primary-500 bg-primary-500/20 animate-pulse'
                        :             'border-dark-600 bg-dark-800'}
                    `}
                  >
                    {isCompleted ? (
                      <CheckCircle className="w-5 h-5 text-emerald-400" />
                    ) : isFailed ? (
                      <XCircle className="w-5 h-5 text-red-400" />
                    ) : isRunning ? (
                      <Zap className="w-5 h-5 text-primary-400" />
                    ) : (
                      <span className="text-xs font-bold text-dark-500">{exec.agent_step}</span>
                    )}
                  </div>

                  {/* Content */}
                  <div className="glass flex-1 p-4 rounded-xl">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-5 h-5 rounded flex items-center justify-center"
                          style={{ background: meta.color + '30' }}
                        >
                          <Icon className="w-3 h-3" style={{ color: meta.color }} />
                        </div>
                        <h3 className="font-semibold text-sm text-dark-200">
                          {exec.agent_name.replace('Agent', ' Agent')}
                        </h3>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {exec.execution_time_seconds && (
                          <span className="text-xs text-dark-500">
                            {exec.execution_time_seconds.toFixed(1)}s
                          </span>
                        )}
                        {exec.tokens_used && (
                          <span className="badge badge-gray text-[10px]">
                            {exec.tokens_used} tokens
                          </span>
                        )}
                        <span className={`badge ${
                          isCompleted ? 'badge-green' :
                          isFailed    ? 'badge-red'   :
                          isRunning   ? 'badge-yellow' : 'badge-gray'
                        }`}>
                          {exec.status}
                        </span>
                      </div>
                    </div>

                    <p className="text-dark-500 text-xs">{meta.desc}</p>

                    {exec.error_message && (
                      <div className="mt-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
                        <p className="text-red-400 text-xs font-mono">{exec.error_message}</p>
                      </div>
                    )}

                    {exec.output_data && Object.keys(exec.output_data).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {Object.entries(exec.output_data).slice(0, 4).map(([k, v]) => (
                          <span key={k} className="badge badge-gray text-[10px]">
                            {k}: {String(v)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
