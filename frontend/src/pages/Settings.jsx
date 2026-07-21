import { useNavigate } from 'react-router'
import AppShell from '../components/AppShell'

export default function Settings() {
  const navigate = useNavigate()

  return (
    <AppShell>
      <div className="p-6 md:p-10 max-w-[820px]">
        <h2 className="font-display text-[40px] uppercase tracking-[-2px] m-0 mb-7 leading-none">
          Réglages
        </h2>
        <button
          onClick={() => navigate('/home')}
          className="cursor-pointer px-6 py-3.5 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:bg-accent transition-none"
        >
          ← Retour à l'accueil
        </button>
      </div>
    </AppShell>
  )
}
