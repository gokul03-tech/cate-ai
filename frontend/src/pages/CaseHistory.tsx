/**
 * LexOrch-KG — Case History Page
 * Searchable, filterable table of all cases.
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  FolderOpen, Search, Filter, ChevronRight,
  Clock, CheckCircle, Zap, AlertCircle, Brain,
  Eye, Upload,
} from 'lucide-react'
import { format } from 'date-fns'
import { casesApi } from '@/lib/api'

const statusConfig: Record<string, { color: string; label: string; icon: typeof CheckCircle }> = {
  uploaded:   { color: 'badge-blue',   label: 'Uploaded',   icon: Clock },
  processing: { color: 'badge-yellow', label: 'Processing', icon: Zap },
  analyzing:  { color: 'badge-yellow', label: 'Analyzing',  icon: Brain },
  debating:   { color: 'badge-purple', label: 'Debating',   icon: Brain },
  review:     { color: 'badge-blue',   label: 'In Review',  icon: Eye },
  completed:  { color: 'badge-green',  label: 'Completed',  icon: CheckCircle },
  failed:     { color: 'badge-red',    label: 'Failed',     icon: AlertCircle },
}

export default function CaseHistory() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)

  const { data: cases, isLoading } = useQuery({
    queryKey: ['cases', page],
    queryFn: async () => {
      const { data } = await casesApi.list(page, 20)
      return data
    },
    refetchInterval: 15000,
  })

  const filtered = (cases || []).filter((c: any) => {
    const matchSearch = !search ||
      c.title.toLowerCase().includes(search.toLowerCase())
    const matchStatus = statusFilter === 'all' || c.status === statusFilter
    return matchSearch && matchStatus
  })

  return (
    <div className="space-y-6 animate-slide-up max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-100">Case History</h1>
          <p className="text-dark-400 mt-0.5">All uploaded and analyzed legal cases</p>
        </div>
        <Link to="/upload" className="btn-primary">
          <Upload className="w-4 h-4" />
          New Case
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input pl-10"
            placeholder="Search cases..."
          />
        </div>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="input w-40"
        >
          <option value="all">All Statuses</option>
          {Object.keys(statusConfig).map(s => (
            <option key={s} value={s}>{statusConfig[s].label}</option>
          ))}
        </select>
      </div>

      {/* Cases Table */}
      <div className="glass rounded-2xl overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-3 text-xs font-semibold text-dark-500 uppercase tracking-wider border-b border-dark-700/50">
          <div className="col-span-5">Case Title</div>
          <div className="col-span-2 hidden md:block">Type</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2 hidden md:block">Uploaded</div>
          <div className="col-span-1">Actions</div>
        </div>

        {/* Rows */}
        {isLoading ? (
          <div className="space-y-0">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="px-6 py-4 border-b border-dark-700/30 animate-pulse">
                <div className="h-4 bg-dark-700 rounded w-3/4 mb-2" />
                <div className="h-3 bg-dark-800 rounded w-1/4" />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <FolderOpen className="w-12 h-12 text-dark-700 mx-auto mb-3" />
            <p className="text-dark-400 font-medium">
              {search || statusFilter !== 'all' ? 'No cases match your filters' : 'No cases yet'}
            </p>
            {!search && statusFilter === 'all' && (
              <Link to="/upload" className="btn-primary mt-4 mx-auto text-sm py-2 px-5">
                Upload First Case
              </Link>
            )}
          </div>
        ) : (
          filtered.map((c: any) => {
            const sc = statusConfig[c.status] || statusConfig.uploaded
            const Icon = sc.icon
            return (
              <Link
                key={c.id}
                to={`/cases/${c.id}`}
                className="grid grid-cols-12 gap-4 px-6 py-4 border-b border-dark-700/30 hover:bg-dark-800/40 transition-colors group items-center"
              >
                <div className="col-span-5 flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-primary-500/15 flex items-center justify-center flex-shrink-0">
                    <FolderOpen className="w-4 h-4 text-primary-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-dark-200 truncate text-sm group-hover:text-white transition-colors">
                      {c.title}
                    </p>
                    <p className="text-dark-500 text-xs">{(c.file_size_bytes / 1024).toFixed(0)} KB</p>
                  </div>
                </div>
                <div className="col-span-2 hidden md:block">
                  <span className="badge badge-gray">{c.file_type.toUpperCase()}</span>
                </div>
                <div className="col-span-2">
                  <span className={`badge ${sc.color}`}>
                    <Icon className="w-3 h-3" />
                    {sc.label}
                  </span>
                </div>
                <div className="col-span-2 hidden md:block text-xs text-dark-500">
                  {format(new Date(c.created_at), 'MMM d, yyyy')}
                </div>
                <div className="col-span-1 flex justify-end">
                  <ChevronRight className="w-4 h-4 text-dark-600 group-hover:text-primary-400 transition-colors" />
                </div>
              </Link>
            )
          })
        )}
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center text-sm text-dark-400">
        <span>Showing {filtered.length} cases</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary text-sm py-1.5 px-3 disabled:opacity-40"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={!cases || cases.length < 20}
            className="btn-secondary text-sm py-1.5 px-3 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
