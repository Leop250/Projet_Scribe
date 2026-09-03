import { useNavigate, useLocation } from 'react-router'

function tabs(pathname) {
  return [
    { path: '/home', label: 'Dicta', icon: '●' },
    ...(pathname === '/record' ? [{ path: '/record', label: 'Direct', icon: '~', live: true }] : []),
    { path: '/recap', label: 'Récaps', icon: '▤' },
    { path: '/settings', label: 'Réglages', icon: '⚙' },
  ]
}

export default function BottomNav() {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  return (
    <nav className="flex shrink-0 border-t-4 border-ink bg-paper">
      {tabs(pathname).map(({ path, label, icon, live }) => {
        const active = pathname === path
        return (
          <button
            key={path}
            onClick={() => navigate(path)}
            className="cursor-pointer border-none flex-1 flex flex-col items-center gap-1 py-2.5 active:scale-[0.94]"
            style={{
              background: active ? (live ? '#ff2e00' : '#0a0a0a') : '#ffffff',
              color: active ? '#ffffff' : '#0a0a0a',
            }}
          >
            <span className="font-display text-base leading-none">{icon}</span>
            <span className="font-mono text-[9px] uppercase tracking-[1px]">{label}</span>
          </button>
        )
      })}
    </nav>
  )
}
