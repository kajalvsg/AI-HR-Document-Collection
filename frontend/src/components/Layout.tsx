import { Link, NavLink, Outlet } from 'react-router-dom'
import { FileText, LayoutDashboard, Upload } from 'lucide-react'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? 'bg-indigo-600 text-white'
      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
  }`

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">HR Document Collector</p>
              <p className="text-xs text-slate-500">AI-powered candidate onboarding</p>
            </div>
          </Link>
          <nav className="flex flex-wrap gap-2">
            <NavLink to="/" end className={navLinkClass}>
              <Upload className="h-4 w-4" />
              Upload Resume
            </NavLink>
            <NavLink to="/dashboard" className={navLinkClass}>
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
