/**
 * LexOrch-KG — Admin Dashboard
 * User management, audit logs, and system statistics.
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users, Shield, Activity, UserCheck, UserX,
  ChevronDown, AlertCircle, TrendingUp,
} from 'lucide-react'
import { format } from 'date-fns'
import { adminApi } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Navigate } from 'react-router-dom'
import { toast } from 'sonner'

const roleColors: Record<string, string> = {
  admin:   'badge-red',
  judge:   'badge-purple',
  lawyer:  'badge-blue',
  analyst: 'badge-green',
  viewer:  'badge-gray',
}

export default function Admin() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<'users' | 'audit'>('users')

  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const { data } = await adminApi.users()
      return data
    },
  })

  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      const { data } = await adminApi.auditLogs(50)
      return data
    },
    enabled: tab === 'audit',
  })

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const { data } = await adminApi.stats()
      return data
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (userId: string) => adminApi.deactivateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      toast.success('User deactivated')
    },
    onError: () => toast.error('Failed to deactivate user'),
  })

  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      adminApi.updateUser(userId, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      toast.success('Role updated')
    },
  })

  return (
    <div className="space-y-6 animate-slide-up max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-100 flex items-center gap-2">
            <Shield className="w-6 h-6 text-red-400" />
            Admin Dashboard
          </h1>
          <p className="text-dark-400 mt-0.5 text-sm">System management and oversight</p>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Cases',    value: stats.total_cases,    icon: Activity, color: 'text-blue-400' },
            { label: 'Total Users',    value: stats.total_users,    icon: Users,    color: 'text-purple-400' },
            { label: 'Reports',        value: stats.total_reports,  icon: TrendingUp, color: 'text-emerald-400' },
            { label: 'Agent Success',  value: `${(stats.agent_success_rate * 100).toFixed(0)}%`, icon: UserCheck, color: 'text-amber-400' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="card">
              <Icon className={`w-5 h-5 ${color} mb-2`} />
              <div className="text-2xl font-bold text-dark-100">{value}</div>
              <div className="text-dark-500 text-sm">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-700/50 pb-0">
        {(['users', 'audit'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium transition-all border-b-2 -mb-px
              ${tab === t
                ? 'border-primary-500 text-primary-300'
                : 'border-transparent text-dark-500 hover:text-dark-300'}`}
          >
            {t === 'users' ? 'User Management' : 'Audit Logs'}
          </button>
        ))}
      </div>

      {/* Users Tab */}
      {tab === 'users' && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="grid grid-cols-12 gap-4 px-6 py-3 text-xs font-semibold text-dark-500 uppercase tracking-wider border-b border-dark-700/50">
            <div className="col-span-4">User</div>
            <div className="col-span-2">Role</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2">Joined</div>
            <div className="col-span-2">Actions</div>
          </div>

          {usersLoading ? (
            <div className="p-6 space-y-3">
              {[1,2,3,4].map(i => (
                <div key={i} className="h-12 bg-dark-800 rounded animate-pulse" />
              ))}
            </div>
          ) : (
            users?.map((u: any) => (
              <div key={u.id} className="grid grid-cols-12 gap-4 px-6 py-4 border-b border-dark-700/30 items-center hover:bg-dark-800/30 transition-colors">
                <div className="col-span-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                    {u.first_name?.[0]}{u.last_name?.[0]}
                  </div>
                  <div>
                    <p className="font-medium text-dark-200 text-sm">{u.first_name} {u.last_name}</p>
                    <p className="text-dark-500 text-xs">{u.email}</p>
                  </div>
                </div>
                <div className="col-span-2">
                  <select
                    value={u.role}
                    onChange={e => updateRoleMutation.mutate({ userId: u.id, role: e.target.value })}
                    className="bg-dark-800 text-dark-200 text-xs rounded-lg px-2 py-1 border border-dark-600/40 cursor-pointer"
                    disabled={u.id === user?.id}
                  >
                    {['admin', 'judge', 'lawyer', 'analyst', 'viewer'].map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
                <div className="col-span-2">
                  <span className={`badge ${u.is_active ? 'badge-green' : 'badge-red'}`}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="col-span-2 text-xs text-dark-500">
                  {format(new Date(u.created_at), 'MMM d, yyyy')}
                </div>
                <div className="col-span-2">
                  {u.id !== user?.id && u.is_active && (
                    <button
                      onClick={() => deactivateMutation.mutate(u.id)}
                      className="text-red-400 hover:text-red-300 transition-colors flex items-center gap-1 text-xs"
                    >
                      <UserX className="w-3 h-3" /> Deactivate
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Audit Logs Tab */}
      {tab === 'audit' && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="grid grid-cols-12 gap-4 px-6 py-3 text-xs font-semibold text-dark-500 uppercase tracking-wider border-b border-dark-700/50">
            <div className="col-span-3">Action</div>
            <div className="col-span-3">User</div>
            <div className="col-span-3">Resource</div>
            <div className="col-span-3">Timestamp</div>
          </div>

          {logsLoading ? (
            <div className="p-6 space-y-3">
              {[1,2,3,4].map(i => (
                <div key={i} className="h-10 bg-dark-800 rounded animate-pulse" />
              ))}
            </div>
          ) : logs?.length ? (
            logs.map((log: any) => (
              <div key={log.id} className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-dark-700/30 items-center hover:bg-dark-800/20 transition-colors text-xs">
                <div className="col-span-3">
                  <span className="badge badge-blue font-mono text-[10px]">{log.action}</span>
                </div>
                <div className="col-span-3 text-dark-400">{log.user_id?.substring(0, 12)}...</div>
                <div className="col-span-3 text-dark-500">{log.resource_type} {log.resource_id?.substring(0, 8)}</div>
                <div className="col-span-3 text-dark-600">
                  {format(new Date(log.created_at), 'MMM d, HH:mm')}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-10 text-dark-500">No audit logs yet</div>
          )}
        </div>
      )}
    </div>
  )
}
