/**
 * LexOrch-KG — Dashboard Page
 * Overview stats, recent cases, quick actions.
 */

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  FolderOpen, Upload, TrendingUp, CheckCircle, Clock,
  AlertCircle, Zap, ChevronRight, Scale, BarChart2,
  Users, FileText, Brain,
} from 'lucide-react'
import { format } from 'date-fns'
import { adminApi } from '@/lib/api'
import { useAuth } from '@/lib/auth'

const statusConfig: Record<string, { color: string; label: string; icon: typeof CheckCircle }> = {
  uploaded:   { color: 'badge-blue',   label: 'Uploaded',   icon: Clock },
  processing: { color: 'badge-yellow', label: 'Processing', icon: Zap },
  analyzing:  { color: 'badge-yellow', label: 'Analyzing',  icon: Brain },
  completed:  { color: 'badge-green',  label: 'Completed',  icon: CheckCircle },
  failed:     { color: 'badge-red',    label: 'Failed',     icon: AlertCircle },
}

export default function Dashboard() {
  const { user } = useAuth()
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const { data } = await adminApi.stats()
      return data
    },
    refetchInterval: 30000, // Auto-refresh every 30s
  })

  const quickActions = [
    { to: '/upload', icon: Upload,     label: 'Upload New Case', color: 'from-blue-500 to-indigo-600' },
    { to: '/cases',  icon: FolderOpen, label: 'View All Cases',  color: 'from-purple-500 to-pink-600' },
  ]

  if (user?.role === 'admin') {
    quickActions.push({ to: '/admin', icon: Users, label: 'Manage Users', color: 'from-emerald-500 to-teal-600' })
  }

  const greeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="space-y-6 max-w-7xl animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-100">
            {greeting()}, {user?.first_name} 👋
          </h1>
          <p className="text-dark-400 mt-0.5">
            {format(new Date(), 'EEEE, MMMM d, yyyy')} · LexOrch-KG Dashboard
          </p>
        </div>
        <Link to="/upload" className="btn-primary">
          <Upload className="w-4 h-4" />
          Upload Case
        </Link>
      </div>

      {/* Disclaimer */}
      <div className="disclaimer-banner">
        <Scale className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <span className="text-xs">
          <strong>Reminder:</strong> All AI-generated recommendations are for decision SUPPORT only.
          Final legal decisions must be made by qualified human legal professionals.
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: 'Total Cases',
            value: isLoading ? '...' : stats?.total_cases ?? 0,
            icon: FolderOpen,
            color: 'text-blue-400',
            bg: 'bg-blue-500/10',
          },
          {
            label: 'Total Users',
            value: isLoading ? '...' : stats?.total_users ?? 0,
            icon: Users,
            color: 'text-purple-400',
            bg: 'bg-purple-500/10',
          },
          {
            label: 'Reports Generated',
            value: isLoading ? '...' : stats?.total_reports ?? 0,
            icon: FileText,
            color: 'text-emerald-400',
            bg: 'bg-emerald-500/10',
          },
          {
            label: 'Agent Success Rate',
            value: isLoading ? '...' : `${((stats?.agent_success_rate ?? 0) * 100).toFixed(0)}%`,
            icon: TrendingUp,
            color: 'text-amber-400',
            bg: 'bg-amber-500/10',
          },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="card">
            <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center mb-3`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div className="text-2xl font-bold text-dark-100">{value}</div>
            <div className="text-dark-400 text-sm mt-1">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Recent Cases */}
        <div className="lg:col-span-2 glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-dark-100">Recent Cases</h2>
            <Link to="/cases" className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
              View all <ChevronRight className="w-3 h-3" />
            </Link>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => (
                <div key={i} className="h-16 rounded-xl bg-dark-800/40 animate-pulse" />
              ))}
            </div>
          ) : stats?.recent_cases?.length ? (
            <div className="space-y-3">
              {stats.recent_cases.map((c: any) => {
                const sc = statusConfig[c.status] || statusConfig.uploaded
                const Icon = sc.icon
                return (
                  <Link
                    key={c.id}
                    to={`/cases/${c.id}`}
                    className="flex items-center gap-4 p-3 rounded-xl bg-dark-800/40 hover:bg-dark-700/50 transition-colors group"
                  >
                    <div className="w-9 h-9 rounded-lg bg-primary-500/15 flex items-center justify-center">
                      <FolderOpen className="w-4 h-4 text-primary-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-dark-200 truncate text-sm">{c.title}</p>
                      <p className="text-dark-500 text-xs">
                        {format(new Date(c.created_at), 'MMM d, yyyy')} · {c.file_type.toUpperCase()}
                      </p>
                    </div>
                    <span className={`badge ${sc.color}`}>
                      <Icon className="w-3 h-3" />
                      {sc.label}
                    </span>
                    <ChevronRight className="w-4 h-4 text-dark-600 group-hover:text-dark-400 transition-colors" />
                  </Link>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-12">
              <FolderOpen className="w-10 h-10 text-dark-600 mx-auto mb-3" />
              <p className="text-dark-400">No cases yet</p>
              <Link to="/upload" className="btn-primary mt-4 mx-auto text-sm py-2 px-4">
                Upload Your First Case
              </Link>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Quick Actions */}
          <div className="glass rounded-2xl p-5">
            <h2 className="font-semibold text-dark-100 mb-4">Quick Actions</h2>
            <div className="space-y-2">
              {quickActions.map(({ to, icon: Icon, label, color }) => (
                <Link
                  key={to}
                  to={to}
                  className="flex items-center gap-3 p-3 rounded-xl bg-dark-800/40 hover:bg-dark-700/50 transition-colors group"
                >
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center`}>
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-sm text-dark-300 group-hover:text-dark-100 transition-colors">{label}</span>
                  <ChevronRight className="w-3 h-3 text-dark-600 ml-auto group-hover:text-dark-400" />
                </Link>
              ))}
            </div>
          </div>

          {/* Cases by Status */}
          {stats?.cases_by_status && (
            <div className="glass rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <BarChart2 className="w-4 h-4 text-primary-400" />
                <h2 className="font-semibold text-dark-100">By Status</h2>
              </div>
              <div className="space-y-2">
                {Object.entries(stats.cases_by_status).map(([status, count]: [string, any]) => {
                  const sc = statusConfig[status] || statusConfig.uploaded
                  const total = stats.total_cases || 1
                  const pct = Math.round((count / total) * 100)
                  return (
                    <div key={status}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-dark-400 capitalize">{status}</span>
                        <span className="text-dark-300">{count}</span>
                      </div>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
