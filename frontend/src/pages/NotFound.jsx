import { useNavigate } from 'react-router'
import Logo from '../components/Logo'

export default function NotFound() {
  const navigate = useNavigate()

  return (
    <div className="min-h-[100dvh] bg-paper text-ink font-body flex flex-col">
      <div className="px-5 py-5">
        <Logo size={22} />
      </div>

      <div id="main-content" tabIndex={-1} className="flex-1 flex flex-col items-center justify-center gap-5 px-5 text-center animate-slam">
        <div className="font-display text-[96px] leading-none tracking-[-2px]">404</div>
        <div>
          <p className="font-mono text-sm font-bold uppercase tracking-[1px]">Page introuvable</p>
          <p className="font-mono text-[13px] text-muted mt-1">Ce lien n&apos;existe pas ou plus.</p>
        </div>
        <button
          onClick={() => navigate('/')}
          className="cursor-pointer mt-2 px-6 py-3.5 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:bg-accent transition-none active:scale-[0.98]"
        >
          ← Retour à l&apos;accueil
        </button>
      </div>
    </div>
  )
}
