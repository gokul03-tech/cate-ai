/**
 * LexOrch-KG — Explainability Viewer Page
 * Transparent AI reasoning with confidence breakdown, evidence, and disclaimers.
 */

import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Lightbulb, AlertCircle, CheckCircle, Link,
  Shield, ChevronRight, Scale, BarChart2,
} from 'lucide-react'
import { casesApi } from '@/lib/api'

function ConfidenceMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.7 ? '#10b981' : score >= 0.4 ? '#f59e0b' : '#ef4444'
  const label = score >= 0.7 ? 'High' : score >= 0.4 ? 'Moderate' : 'Low'

  return (
    <div className="flex items-center gap-4">
      <div className="relative w-24 h-24">
        <svg viewBox="0 0 100 100" className="rotate-[-90deg]">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#1e293b" strokeWidth="10" />
          <circle
            cx="50" cy="50" r="40" fill="none"
            stroke={color} strokeWidth="10"
            strokeDasharray={`${2.51 * pct} 251`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold text-dark-100">{pct}%</span>
          <span className="text-xs" style={{ color }}>{label}</span>
        </div>
      </div>
      <div>
        <p className="font-semibold text-dark-200">Confidence Score</p>
        <p className="text-dark-500 text-xs mt-0.5">Based on evidence quality,<br />debate consensus, and precedents</p>
      </div>
    </div>
  )
}

export default function ExplainabilityViewer() {
  const { id } = useParams<{ id: string }>()

  const { data: explain, isLoading, error } = useQuery({
    queryKey: ['explain', id],
    queryFn: async () => {
      const { data } = await casesApi.explainability(id!)
      return data
    },
  })

  return (
    <div className="space-y-6 animate-slide-up max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-dark-100 flex items-center gap-2">
          <Lightbulb className="w-6 h-6 text-amber-400" />
          Explainability Report
        </h1>
        <p className="text-dark-400 mt-0.5 text-sm">
          Transparent explanation of how the AI reached its recommendation
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => (
            <div key={i} className="glass p-6 rounded-xl animate-pulse space-y-3">
              <div className="h-4 bg-dark-700 rounded w-1/3" />
              <div className="h-3 bg-dark-800 rounded" />
              <div className="h-3 bg-dark-800 rounded w-5/6" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-16">
          <AlertCircle className="w-10 h-10 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">Explainability report not yet generated</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Confidence + Recommendation */}
          <div className="glass p-6 rounded-2xl">
            <div className="flex flex-col md:flex-row gap-6 items-start">
              <ConfidenceMeter score={explain?.confidence_score || 0} />
              <div className="flex-1">
                <h2 className="font-semibold text-dark-100 mb-2">AI Recommendation</h2>
                <p className="text-dark-200 text-sm leading-relaxed">
                  {explain?.recommendation || 'No recommendation generated'}
                </p>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="disclaimer-banner">
            <Shield className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p className="text-xs">{explain?.disclaimer}</p>
          </div>

          {/* Reasoning Chain */}
          {explain?.reasoning_chain?.length > 0 && (
            <div className="glass p-6 rounded-2xl">
              <h2 className="font-semibold text-dark-100 flex items-center gap-2 mb-4">
                <ChevronRight className="w-4 h-4 text-primary-400" />
                Reasoning Chain
              </h2>
              <div className="space-y-3">
                {explain.reasoning_chain.map((step: string, i: number) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary-500/20 text-primary-400 text-xs flex items-center justify-center font-bold flex-shrink-0">
                      {i + 1}
                    </div>
                    <p className="text-dark-300 text-sm pt-0.5">{step}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence Breakdown */}
          {explain?.confidence_breakdown && (
            <div className="glass p-6 rounded-2xl">
              <h2 className="font-semibold text-dark-100 flex items-center gap-2 mb-4">
                <BarChart2 className="w-4 h-4 text-primary-400" />
                Confidence Breakdown
              </h2>
              <div className="space-y-3">
                {Object.entries(explain.confidence_breakdown).map(([factor, score]: [string, any]) => (
                  <div key={factor}>
                    <div className="flex justify-between text-xs mb-1 text-dark-400">
                      <span className="capitalize">{factor.replace(/_/g, ' ')}</span>
                      <span>{(Number(score) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${Number(score) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evidence & Sections */}
          <div className="grid md:grid-cols-2 gap-4">
            {/* Evidence */}
            {explain?.evidence_used?.length > 0 && (
              <div className="glass p-5 rounded-xl">
                <h3 className="font-semibold text-dark-100 flex items-center gap-2 mb-3 text-sm">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  Evidence Used
                </h3>
                <ul className="space-y-2">
                  {explain.evidence_used.map((ev: any, i: number) => (
                    <li key={i} className="flex gap-2 text-xs text-dark-400">
                      <span className="text-emerald-400 mt-0.5">•</span>
                      {typeof ev === 'string' ? ev : ev.description || JSON.stringify(ev)}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Sections */}
            {explain?.sections_applied?.length > 0 && (
              <div className="glass p-5 rounded-xl">
                <h3 className="font-semibold text-dark-100 flex items-center gap-2 mb-3 text-sm">
                  <Link className="w-4 h-4 text-blue-400" />
                  Legal Sections Applied
                </h3>
                <div className="flex flex-wrap gap-2">
                  {explain.sections_applied.map((section: string, i: number) => (
                    <span key={i} className="badge badge-blue text-xs">{section}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Precedents */}
          {explain?.precedents_cited?.length > 0 && (
            <div className="glass p-6 rounded-2xl">
              <h2 className="font-semibold text-dark-100 mb-3 text-sm flex items-center gap-2">
                <Scale className="w-4 h-4 text-amber-400" />
                Precedents Cited
              </h2>
              <div className="space-y-2">
                {explain.precedents_cited.map((prec: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-dark-800/40">
                    <Scale className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span className="text-dark-300 text-sm flex-1">
                      {prec.title || `Precedent ${i + 1}`}
                    </span>
                    {prec.relevance && (
                      <span className="text-xs text-dark-500">
                        {(prec.relevance * 100).toFixed(0)}% relevant
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Limitations */}
          {explain?.limitations?.length > 0 && (
            <div className="glass p-5 rounded-xl border border-yellow-500/20 bg-yellow-500/5">
              <h3 className="font-semibold text-yellow-300 flex items-center gap-2 mb-3 text-sm">
                <AlertCircle className="w-4 h-4" />
                Known Limitations
              </h3>
              <ul className="space-y-1.5">
                {explain.limitations.map((lim: string, i: number) => (
                  <li key={i} className="flex gap-2 text-xs text-yellow-200/70">
                    <span className="mt-0.5">⚠</span>
                    {lim}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
