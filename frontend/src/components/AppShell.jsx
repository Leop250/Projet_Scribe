import Sidebar from './Sidebar'
import BottomNav from './BottomNav'
import { useLocation } from 'react-router'

const PAGE_INFO = {
  '/home':     { title: 'Accueil',         sub: 'Prêt à enregistrer une réunion ?' },
  '/recap':    { title: 'Comptes-rendus',   sub: 'Vos comptes-rendus générés automatiquement' },
  '/settings': { title: 'Réglages',         sub: 'Gérez vos préférences' },
}

export default function AppShell({ children }) {
  const { pathname } = useLocation()
  const info = PAGE_INFO[pathname] ?? { title: '', sub: '' }

  return (
    <div className="flex h-[100dvh] bg-page">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-bg">
        {/* Desktop topbar */}
        <header className="hidden md:flex items-center justify-between px-8 py-5 border-b border-[rgba(255,255,255,0.06)] shrink-0">
          <div>
            <h1 className="font-display text-[21px] font-bold tracking-[-0.02em] text-ink">
              {info.title}
            </h1>
            <p className="text-[13px] text-muted mt-0.5">{info.sub}</p>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          {children}
        </main>

        <div className="md:hidden">
          <BottomNav />
        </div>
      </div>
    </div>
  )
}
