import { useState } from 'react'
import { useNavigate } from 'react-router'
import AppShell from '../components/AppShell'

function VideoIcon() {
  return (
    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <polygon points="23 7 16 12 23 17 23 7"/>
      <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
    </svg>
  )
}

function MicIcon({ size = 20 }) {
  return (
    <svg width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="23"/>
      <line x1="8" y1="23" x2="16" y2="23"/>
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  )
}

export default function Home() {
  const [tab, setTab] = useState('dictaphone')
  const navigate = useNavigate()

  return (
    <AppShell>
      <div className="px-[18px] md:px-10 py-6 md:py-8 max-w-[700px]">

        {/* Mobile header (hidden on desktop — AppShell topbar takes over) */}
        <div className="flex items-start justify-between pb-6 md:hidden">
          <div>
            <h1 className="font-display text-[22px] font-bold tracking-[-0.02em] text-ink">
              Bonjour, Alex
            </h1>
            <p className="text-[13px] text-muted mt-0.5">Prêt à enregistrer une réunion ?</p>
          </div>
          <button className="w-9 h-9 rounded-full bg-surface flex items-center justify-center text-muted hover:bg-[rgba(255,255,255,0.08)] transition-colors cursor-pointer border-none mt-1">
            <MoonIcon />
          </button>
        </div>

        {/* Segmented control */}
        <div className="flex bg-surface rounded-[12px] p-1 mb-4 md:max-w-[320px]">
          {[
            { id: 'visio',      label: 'Visio',      Icon: () => <VideoIcon /> },
            { id: 'dictaphone', label: 'Dictaphone', Icon: () => <MicIcon size={14} /> },
          ].map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex-1 flex items-center justify-center gap-2 h-8 rounded-[10px] text-[13px] font-bold transition-all cursor-pointer border-none ${
                tab === id ? 'bg-bg text-accent shadow-sm' : 'bg-transparent text-muted'
              }`}
            >
              <Icon />
              {label}
            </button>
          ))}
        </div>

        {/* Card */}
        {tab === 'dictaphone' ? (
          <div className="bg-surface rounded-[18px] border border-[rgba(255,255,255,0.10)] shadow-[0_20px_50px_rgba(0,0,0,0.4)] p-[18px] md:p-8 flex flex-col items-center text-center">
            <div className="w-[74px] h-[74px] rounded-full flex items-center justify-center mb-4 animate-pulse-ring bg-[rgba(239,68,68,0.16)]">
              <span className="text-accent"><MicIcon size={28} /></span>
            </div>
            <h2 className="font-display text-[16px] font-bold tracking-[-0.02em] text-ink mb-2">
              Enregistrement présentiel
            </h2>
            <p className="text-[13px] text-muted leading-[1.5] mb-5 max-w-[220px]">
              Micro local chiffré. Idéal pour les réunions en salle, sans visio.
            </p>
            <button
              onClick={() => navigate('/record')}
              className="w-full md:max-w-[280px] h-12 flex items-center justify-center gap-2 bg-accent rounded-[13px] text-white text-[14px] font-bold hover:opacity-90 transition-opacity cursor-pointer border-none"
            >
              <span className="text-base leading-none">●</span>
              Démarrer l'enregistrement
            </button>
          </div>
        ) : (
          <div className="bg-surface rounded-[18px] p-8 flex items-center justify-center border border-[rgba(255,255,255,0.10)]">
            <p className="text-[13px] text-muted text-center">
              La fonctionnalité Visio sera disponible prochainement.
            </p>
          </div>
        )}
      </div>
    </AppShell>
  )
}
