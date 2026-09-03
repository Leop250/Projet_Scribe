import { useNavigate } from 'react-router'
import Logo from './Logo'

export default function LegalPageShell({ title, lastUpdated, children }) {
  const navigate = useNavigate()

  return (
    <div className="min-h-[100dvh] bg-paper text-ink font-body flex flex-col">
      <div className="px-5 py-5">
        <Logo size={22} />
      </div>

      <div id="main-content" tabIndex={-1} className="flex-1 px-5 pb-14 max-w-[680px] w-full mx-auto animate-slam">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="cursor-pointer bg-transparent border-none p-0 font-mono text-xs uppercase tracking-[2px] mb-3.5 inline-block"
        >
          ← Retour
        </button>

        <h1 className="font-display text-[34px] uppercase tracking-[-2px] m-0 mb-1.5 leading-none">
          {title}
        </h1>
        <p className="font-mono text-[13px] text-muted mb-6">Dernière mise à jour : {lastUpdated}</p>

        {children}
      </div>
    </div>
  )
}
