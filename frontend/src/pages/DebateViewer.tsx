/**
 * LexOrch-KG — Debate Viewer Page
 * Multi-agent adversarial debate transcript display.
 */

import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MessageSquare, Sword, Shield, Scale, Handshake, AlertCircle } from 'lucide-react'
import { casesApi } from '@/lib/api'

function DebateSection({
  title, icon: Icon, colorClass, content, confidence
}: {
  title: string
  icon: typeof Sword
  colorClass: string
  content?: string
  confidence?: number
}) {
  if (!content) return null
  return (
    <div className={`debate-${colorClass} py-4 rounded-r-xl mb-4`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4" />
        <h3 className="font-semibold text-sm">{title}</h3>
        {confidence !== undefined && (
          <span className="ml-auto badge badge-gray text-[10px]">
            Confidence: {(confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
      <p className="text-dark-300 text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
    </div>
  )
}

export default function DebateViewer() {
  const { id } = useParams<{ id: string }>()

  const { data: debate, isLoading, error } = useQuery({
    queryKey: ['debate', id],
    queryFn: async () => {
      const { data } = await casesApi.debate(id!)
      return data
    },
  })

  return (
    <div className="space-y-6 animate-slide-up max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-dark-100 flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-primary-400" />
          Multi-Agent Debate
        </h1>
        <p className="text-dark-400 mt-0.5 text-sm">
          Adversarial debate between Prosecution, Defense, Judge, and Consensus agents
        </p>
      </div>

      {/* Disclaimer */}
      <div className="disclaimer-banner">
        <Scale className="w-4 h-4 flex-shrink-0" />
        <span className="text-xs">
          These arguments are AI-generated for analysis purposes only.
          They do not represent legal advice or binding opinions.
          Human legal professionals must review all findings.
        </span>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1,2,3,4].map(i => (
            <div key={i} className="glass p-6 rounded-xl animate-pulse">
              <div className="h-4 bg-dark-700 rounded w-1/4 mb-3" />
              <div className="space-y-2">
                <div className="h-3 bg-dark-800 rounded" />
                <div className="h-3 bg-dark-800 rounded w-4/5" />
                <div className="h-3 bg-dark-800 rounded w-3/5" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-16">
          <AlertCircle className="w-10 h-10 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">Debate not yet generated</p>
          <p className="text-dark-600 text-sm">Run the AI pipeline to generate debate arguments</p>
        </div>
      ) : (
        <div className="glass p-6 rounded-2xl space-y-2">
          {/* Confidence Bar */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <div className="flex justify-between text-xs mb-1 text-dark-400">
                <span className="flex items-center gap-1"><Sword className="w-3 h-3 text-red-400" /> Prosecution</span>
                <span>{((debate?.prosecution_confidence || 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${(debate?.prosecution_confidence || 0) * 100}%`, background: 'linear-gradient(90deg, #ef4444, #dc2626)' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1 text-dark-400">
                <span className="flex items-center gap-1"><Shield className="w-3 h-3 text-blue-400" /> Defense</span>
                <span>{((debate?.defense_confidence || 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${(debate?.defense_confidence || 0) * 100}%`, background: 'linear-gradient(90deg, #3b82f6, #2563eb)' }} />
              </div>
            </div>
          </div>

          <DebateSection
            title="⚔️ Prosecution Argument"
            icon={Sword}
            colorClass="prosecution"
            content={debate?.prosecution_argument}
            confidence={debate?.prosecution_confidence}
          />
          <DebateSection
            title="🛡️ Defense Argument"
            icon={Shield}
            colorClass="defense"
            content={debate?.defense_argument}
            confidence={debate?.defense_confidence}
          />
          <DebateSection
            title="⚖️ Judicial Assessment"
            icon={Scale}
            colorClass="judge"
            content={debate?.judge_assessment}
          />
          <DebateSection
            title="🤝 Consensus & Recommendation"
            icon={Handshake}
            colorClass="consensus"
            content={debate?.consensus}
            confidence={debate?.recommendation_confidence}
          />

          {/* Final Recommendation */}
          {debate?.final_recommendation && (
            <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Handshake className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold text-emerald-300 text-sm">Final AI Recommendation</span>
                <span className="ml-auto badge badge-green text-[10px]">
                  {((debate.recommendation_confidence || 0) * 100).toFixed(0)}% confidence
                </span>
              </div>
              <p className="text-dark-200 text-sm">{debate.final_recommendation}</p>
              <p className="text-red-400 text-xs mt-3 italic">
                ⚠️ This recommendation is AI-generated for support purposes only.
                Final legal decision must be made by a qualified human legal professional.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
