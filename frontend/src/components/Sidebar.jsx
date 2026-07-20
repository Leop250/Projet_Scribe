import { useNavigate, useLocation } from 'react-router'
import Logo from './Logo'

function HomeIcon() {
  return (
    <svg width="19" height="19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>
    </svg>
  )
}

function FileTextIcon() {
  return (
    <svg width="19" height="19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/>
      <rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>
    </svg>
  )
}

function SettingsIcon() {
  return (
    <svg width="19" height="19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>
  )
}

function DotsIcon() {
  return (
    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" viewBox="0 0 24 24">
      <circle cx="12" cy="5" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="12" cy="19" r="1.4"/>
    </svg>
  )
}

const TABS = [
  { path: '/home',     label: 'Accueil',        Icon: HomeIcon },
  { path: '/recap',    label: 'Comptes-rendus',  Icon: FileTextIcon },
  { path: '/settings', label: 'Réglages',        Icon: SettingsIcon },
]

function NavItem({ path, label, Icon }) {
  const navigate  = useNavigate()
  const { pathname } = useLocation()
  const active = pathname === path

  return (
    <button
      onClick={() => navigate(path)}
      className={`w-full flex items-center gap-3 px-[14px] h-12 rounded-[13px] text-[15px] font-semibold border-none cursor-pointer transition-all text-left ${
        active
          ? 'bg-accent text-white'
          : 'bg-transparent text-muted hover:bg-[rgba(255,255,255,0.05)] hover:text-ink'
      }`}
    >
      <Icon />
      {label}
    </button>
  )
}

export default function Sidebar() {
  return (
    <aside className="hidden md:flex flex-col w-[248px] shrink-0 h-[100dvh] sticky top-0 bg-bg border-r border-[rgba(255,255,255,0.06)] px-[18px] py-6 overflow-y-auto">
      {/* Brand */}
      <div className="flex items-center gap-3 px-2 pb-6">
        <Logo size={18} />
        <span className="font-display text-[22px] font-bold tracking-[-0.02em] text-ink">
          recapp<span className="text-accent">.</span>
        </span>
      </div>

      {/* Nav */}
      <div className="text-[11px] font-bold uppercase tracking-[0.10em] text-muted px-[14px] pb-2">
        Espace de travail
      </div>
      <nav className="flex flex-col gap-1 flex-1">
        {TABS.map(tab => <NavItem key={tab.path} {...tab} />)}
      </nav>

      {/* User profile */}
      <div className="flex items-center gap-3 p-3 rounded-[14px] bg-surface mt-4">
        <div
          className="w-[34px] h-[34px] rounded-full flex items-center justify-center text-white font-bold text-[13px] shrink-0"
          style={{ background: 'linear-gradient(135deg, #ef4444, #f87171)' }}
        >
          AL
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[14px] font-bold text-ink truncate">Alex Laurent</div>
          <div className="text-[12px] text-muted">Plan Pro</div>
        </div>
        <span className="text-muted shrink-0"><DotsIcon /></span>
      </div>
    </aside>
  )
}
