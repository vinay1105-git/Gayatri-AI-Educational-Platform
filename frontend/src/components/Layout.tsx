import React, { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  BarChart3,
  BookOpen,
  ClipboardCheck,
  Cpu,
  FileSpreadsheet,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareText,
  ShieldCheck,
  Users,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { BrandLogo } from './BrandLogo'

interface NavItem {
  to: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  end?: boolean
}

export const Layout: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  if (!user) return null

  const studentNav: NavItem[] = [
    { to: '/dashboard', label: 'Intelligence Hub', icon: LayoutDashboard, end: true },
    { to: '/courses', label: 'Courses & Modules', icon: BookOpen },
    { to: '/assessments', label: 'Assessments', icon: ClipboardCheck },
    { to: '/analytics', label: 'Learning Analytics', icon: BarChart3 },
    { to: '/assistant', label: 'Academic Assistant', icon: MessageSquareText },
    { to: '/reports', label: 'Export Reports', icon: FileSpreadsheet },
  ]

  const adminNav: NavItem[] = [
    { to: '/admin', label: 'Command Center', icon: LayoutDashboard, end: true },
    { to: '/admin/students', label: 'Student Directory', icon: Users },
    { to: '/assessments', label: 'Assessment Studio', icon: ClipboardCheck },
    { to: '/courses', label: 'Curriculum Catalog', icon: BookOpen },
    { to: '/admin/ml-models', label: 'ML Engine & Eval', icon: Cpu },
    { to: '/assistant', label: 'Intelligence Assistant', icon: MessageSquareText },
    { to: '/reports', label: 'Executive Reports', icon: FileSpreadsheet },
  ]

  const navItems = user.role === 'admin' ? adminNav : studentNav

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const sidebarContent = (
    <div className="flex h-full flex-col justify-between bg-navy-900/95 border-r border-slate-800/80 px-3.5 py-5">
      <div>
        <div className="px-2 pb-6 border-b border-slate-800/80">
          <BrandLogo size={34} showSubtitle />
        </div>

        <div className="mt-5 px-2">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2.5">
            {user.role === 'admin' ? 'Enterprise Governance' : 'Learner Workspace'}
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-sm'
                      : 'text-slate-400 hover:bg-navy-800 hover:text-slate-100 border border-transparent'
                  }`
                }
              >
                <item.icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      <div className="border-t border-slate-800/80 pt-4 px-1">
        <div className="rounded-xl bg-navy-850/90 border border-slate-800 p-3 mb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan-500/15 border border-cyan-500/30 font-mono text-xs font-semibold text-cyan-300">
              {user.avatar_initials}
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-slate-100">{user.full_name}</div>
              <div className="flex items-center gap-1.5 text-[10px] text-slate-400 whitespace-nowrap">
                <ShieldCheck className="h-3 w-3 text-emerald-400 shrink-0" />
                <span className="uppercase tracking-wide font-medium">{user.role}</span>
                {user.student_code && <span className="font-mono text-slate-500">{user.student_code}</span>}
              </div>
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-800 bg-navy-850 px-3 py-2 text-xs font-medium text-slate-300 hover:border-rose-500/40 hover:bg-rose-500/10 hover:text-rose-200 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign Out
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 flex">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 sticky top-0 h-screen">{sidebarContent}</aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="relative z-10 w-68 max-w-[82vw] h-full">
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-4 rounded-lg p-1.5 text-slate-400 hover:bg-navy-800 hover:text-slate-100"
              aria-label="Close navigation"
            >
              <X className="h-5 w-5" />
            </button>
            {sidebarContent}
          </div>
        </div>
      )}

      {/* Main Content Shell */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-800/80 bg-navy-950/90 backdrop-blur-md px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="lg:hidden rounded-lg border border-slate-800 bg-navy-900 p-2 text-slate-300 hover:text-white"
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="text-xs font-medium text-slate-400 hidden sm:block">
              <span className="text-slate-500">Department:</span>{' '}
              <span className="text-slate-200">{user.department}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Telemetry Active
            </span>
            <span className="hidden md:inline-block font-mono text-xs text-slate-400">{user.email}</span>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1440px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
