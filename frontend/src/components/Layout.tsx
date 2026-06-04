import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, GitCompare, AlertTriangle,
  MessageSquare, ScrollText, Scale, ShieldCheck
} from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/reconciliation', icon: GitCompare,      label: 'Recon Workbench' },
  { to: '/disputes',      icon: AlertTriangle,    label: 'Dispute Workbench' },
  { to: '/query',         icon: MessageSquare,    label: 'AI Query' },
  { to: '/audit',         icon: ScrollText,       label: 'Audit Trail' },
  { to: '/policy',        icon: ShieldCheck,      label: 'IC Policy' },
]

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 flex flex-col bg-brand-950 text-white shrink-0">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-brand-800">
          <Scale className="w-7 h-7 text-indigo-300" />
          <div>
            <div className="text-lg font-bold tracking-tight">IC Resolve</div>
            <div className="text-xs text-indigo-300">AI Recon Orchestrator</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-700 text-white'
                    : 'text-indigo-200 hover:bg-brand-800 hover:text-white',
                )
              }
            >
              <Icon className="w-4.5 h-4.5 shrink-0" size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Period badge */}
        <div className="px-4 py-4 border-t border-brand-800">
          <div className="text-xs text-indigo-400 mb-1">Active Period</div>
          <div className="text-sm font-semibold text-indigo-100">March 2024</div>
          <div className="text-xs text-indigo-400 mt-0.5">Nexora Group</div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
