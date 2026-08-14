import { useNavigate, useLocation } from 'react-router'
import Logo from './Logo'
import { useAuth } from '../context/AuthContext'

function tabs(pathname) {
  return [
    { path: '/home', label: 'Dicta', icon: '●' },
    ...(pathname === '/record' ? [{ path: '/record', label: 'Direct', icon: '~', live: true }] : []),
    { path: '/recap', label: 'Récaps', icon: '▤' },
    { path: '/settings', label: 'Réglages', icon: '⚙' },
  ]
}

export default function Sidebar() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { logout } = useAuth()

  return (
    <aside className="hidden md:flex flex-col w-[88px] shrink-0 h-[100dvh] sticky top-0 border-r-4 border-ink bg-paper">
      <div className="flex items-center justify-center py-5 border-b-4 border-ink">
        <Logo size={14} />
      </div>

      {tabs(pathname).map(({ path, label, icon, live }) => {
        const active = pathname === path
        return (
          <button
            key={path}
            onClick={() => navigate(path)}
            className="cursor-pointer border-none py-[22px] px-1.5 border-b-4 border-ink text-center"
            style={{
              background: active ? (live ? '#ff2e00' : '#0a0a0a') : '#ffffff',
              color: active ? '#ffffff' : '#0a0a0a',
            }}
          >
            <div className="font-display text-[22px] leading-none">{icon}</div>
            <div className="font-mono text-[9px] uppercase tracking-[1px] mt-1.5">{label}</div>
          </button>
        )
      })}

      <button
        onClick={() => { logout(); navigate('/') }}
        className="cursor-pointer border-none mt-auto py-5 px-1.5 text-center font-mono text-[9px] uppercase bg-transparent hover:bg-accent hover:text-white transition-none"
      >
        Quitter
      </button>
    </aside>
  )
}
