/**
 * LexOrch-KG — Main App Layout with Sidebar Navigation
 */

import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Upload, FolderOpen, Network, GitBranch,
  MessageSquare, Lightbulb, FileText, Shield, User,
  LogOut, Menu, X, Scale, ChevronRight,
  Bell, Settings,
} from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { toast } from 'sonner'

const navItems = [
  { to: '/dashboard',       icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload',          icon: Upload,           label: 'Upload Case' },
  { to: '/cases',           icon: FolderOpen,       label: 'Case History' },
]

const caseItems = [
  { icon: Network,        label: 'Knowledge Graph' },
  { icon: GitBranch,      label: 'Agent Timeline' },
  { icon: MessageSquare,  label: 'Debate Viewer' },
  { icon: Lightbulb,      label: 'Explainability' },
  { icon: FileText,       label: 'Reports' },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    toast.success('Logged out successfully')
    navigate('/login')
  }

  const roleColor = {
    admin:    'badge-red',
    judge:    'badge-purple',
    lawyer:   'badge-blue',
    analyst:  'badge-green',
    viewer:   'badge-gray',
  }[user?.role ?? 'viewer'] ?? 'badge-gray'

  return (
    <div className="flex h-screen bg-dark-950 overflow-hidden">

      {/* ── Sidebar ─────────────────────────────────────────────── */}
      <aside
        className={`
          flex flex-col transition-all duration-300 ease-in-out
          ${sidebarOpen ? 'w-64' : 'w-16'}
          bg-dark-900 border-r border-dark-700/50 flex-shrink-0
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-dark-700/50">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
            <Scale className="w-4 h-4 text-white" />
          </div>
          {sidebarOpen && (
            <div className="animate-fade-in min-w-0">
              <span className="font-bold text-sm gradient-text">LexOrch-KG</span>
              <p className="text-[10px] text-dark-500 truncate">Legal AI Platform</p>
            </div>
          )}
        </div>

        {/* Nav Items */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {sidebarOpen && (
            <p className="text-[10px] text-dark-600 uppercase tracking-widest px-3 pt-2 pb-1 font-semibold">
              Navigation
            </p>
          )}
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''} ${!sidebarOpen ? 'justify-center' : ''}`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {sidebarOpen && <span className="animate-fade-in">{label}</span>}
            </NavLink>
          ))}

          {sidebarOpen && (
            <>
              <p className="text-[10px] text-dark-600 uppercase tracking-widest px-3 pt-4 pb-1 font-semibold">
                Analysis Tools
              </p>
              <div className="space-y-0.5 pl-2">
                {caseItems.map(({ icon: Icon, label }) => (
                  <div key={label} className="sidebar-link opacity-50 cursor-default text-xs">
                    <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>{label}</span>
                    <ChevronRight className="w-3 h-3 ml-auto opacity-50" />
                  </div>
                ))}
              </div>
            </>
          )}

          {user?.role === 'admin' && (
            <>
              {sidebarOpen && (
                <p className="text-[10px] text-dark-600 uppercase tracking-widest px-3 pt-4 pb-1 font-semibold">
                  Admin
                </p>
              )}
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? 'active' : ''} ${!sidebarOpen ? 'justify-center' : ''}`
                }
              >
                <Shield className="w-4 h-4 flex-shrink-0" />
                {sidebarOpen && <span className="animate-fade-in">Admin Panel</span>}
              </NavLink>
            </>
          )}
        </nav>

        {/* User Profile */}
        <div className="p-3 border-t border-dark-700/50 space-y-1">
          <NavLink
            to="/profile"
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'active' : ''} ${!sidebarOpen ? 'justify-center' : ''}`
            }
          >
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            {sidebarOpen && (
              <div className="animate-fade-in min-w-0">
                <p className="text-xs font-medium text-dark-200 truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <span className={`badge text-[9px] mt-0.5 ${roleColor}`}>
                  {user?.role}
                </span>
              </div>
            )}
          </NavLink>

          <button
            onClick={handleLogout}
            className={`sidebar-link w-full text-red-400 hover:text-red-300 hover:bg-red-500/10 ${!sidebarOpen ? 'justify-center' : ''}`}
          >
            <LogOut className="w-4 h-4 flex-shrink-0" />
            {sidebarOpen && <span className="animate-fade-in">Logout</span>}
          </button>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="h-14 bg-dark-900/60 backdrop-blur border-b border-dark-700/50 flex items-center px-4 gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-dark-700/60 text-dark-400 hover:text-dark-100 transition-colors"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          <div className="flex-1" />

          {/* Disclaimer pill */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
            <span className="text-[11px] text-red-400 font-medium">Decision Support Only — Human Review Required</span>
          </div>

          <button className="p-2 rounded-lg hover:bg-dark-700/60 text-dark-400 hover:text-dark-100 transition-colors">
            <Bell className="w-4 h-4" />
          </button>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 grid-bg">
          <div className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
