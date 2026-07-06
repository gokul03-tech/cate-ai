/**
 * LexOrch-KG — App Router
 * Defines all routes, protected routes, and layout wrappers.
 */

import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/lib/auth'
import Layout from '@/components/Layout'
import Landing from '@/pages/Landing'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Dashboard from '@/pages/Dashboard'
import UploadCase from '@/pages/UploadCase'
import CaseHistory from '@/pages/CaseHistory'
import CaseDetail from '@/pages/CaseDetail'
import KnowledgeGraph from '@/pages/KnowledgeGraph'
import AgentTimeline from '@/pages/AgentTimeline'
import DebateViewer from '@/pages/DebateViewer'
import ExplainabilityViewer from '@/pages/ExplainabilityViewer'
import Reports from '@/pages/Reports'
import Admin from '@/pages/Admin'
import Profile from '@/pages/Profile'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-950">
        <div className="text-center animate-fade-in">
          <div className="spinner mx-auto mb-4" style={{ width: 48, height: 48 }} />
          <p className="text-dark-400">Loading LexOrch-KG...</p>
        </div>
      </div>
    )
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function PublicOnlyRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return null
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
        <Route path="/register" element={<PublicOnlyRoute><Register /></PublicOnlyRoute>} />

        {/* Protected routes — inside sidebar Layout */}
        <Route
          path="/"
          element={<ProtectedRoute><Layout /></ProtectedRoute>}
        >
          <Route path="dashboard"     element={<Dashboard />} />
          <Route path="upload"        element={<UploadCase />} />
          <Route path="cases"         element={<CaseHistory />} />
          <Route path="cases/:id"     element={<CaseDetail />} />
          <Route path="cases/:id/graph"    element={<KnowledgeGraph />} />
          <Route path="cases/:id/timeline" element={<AgentTimeline />} />
          <Route path="cases/:id/debate"   element={<DebateViewer />} />
          <Route path="cases/:id/explain"  element={<ExplainabilityViewer />} />
          <Route path="cases/:id/reports"  element={<Reports />} />
          <Route path="admin"         element={<Admin />} />
          <Route path="profile"       element={<Profile />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
