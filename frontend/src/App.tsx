import React from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { StudentDashboardPage } from './pages/StudentDashboardPage'
import { CoursesPage } from './pages/CoursesPage'
import { AssessmentsPage } from './pages/AssessmentsPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { AssistantPage } from './pages/AssistantPage'
import { ReportsPage } from './pages/ReportsPage'
import { AdminDashboardPage } from './pages/AdminDashboardPage'
import { AdminStudentsPage } from './pages/AdminStudentsPage'
import { AdminMLPage } from './pages/AdminMLPage'

const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: Array<'student' | 'admin'> }> = ({
  children,
  allowedRoles,
}) => {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen bg-navy-950 flex items-center justify-center text-sm text-cyan-300 font-mono">
        Initializing Gayatri AI session...
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === 'admin' ? '/admin' : '/dashboard'} replace />
  }
  return <>{children}</>
}

const HomeRedirect: React.FC = () => {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.role === 'admin' ? '/admin' : '/dashboard'} replace />
}

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<HomeRedirect />} />

          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            {/* Student routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute allowedRoles={['student']}>
                  <StudentDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute allowedRoles={['student']}>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />

            {/* Shared authenticated routes */}
            <Route path="/courses" element={<CoursesPage />} />
            <Route path="/assessments" element={<AssessmentsPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/reports" element={<ReportsPage />} />

            {/* Admin routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/students"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminStudentsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/ml-models"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminMLPage />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route path="*" element={<HomeRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
