import { useNavigate } from 'react-router'
import AppShell from '../components/AppShell'
import { useRecap } from '../context/RecapContext'

export default function Home() {
  const navigate = useNavigate()
  const { recap } = useRecap()

  return (
    <AppShell>
      <div className="p-6 md:p-10 max-w-[820px] mx-auto">
        <h2 className="font-display text-[40px] uppercase tracking-[-2px] m-0 mb-7 leading-none">
          Dictaphone
        </h2>

        <div className="flex items-center gap-8 flex-wrap">
          <button
            onClick={() => navigate('/attendance')}
            className="cursor-pointer w-[200px] h-[200px] border-[6px] border-ink bg-accent flex flex-col items-center justify-center shadow-[10px_10px_0_#0a0a0a]"
          >
            <div className="font-display text-[52px] text-ink leading-none">●</div>
            <div className="font-mono text-xs uppercase tracking-[1px] mt-2 text-ink">Rec</div>
          </button>
          <div>
            <div className="font-mono text-[13px] uppercase tracking-[1px] text-muted">Statut</div>
            <div className="font-display text-[34px]">PRÊT</div>
            <div className="font-mono text-[15px] mt-2">00:00</div>
          </div>
        </div>

        <h3 className="font-display text-[22px] uppercase tracking-[-1px] mt-10 mb-3.5">
          Enregistrements récents
        </h3>
        <div className="border-4 border-ink">
          {recap ? (
            <div
              onClick={() => navigate('/recap')}
              className="cursor-pointer flex items-center justify-between px-5 py-4 hover:bg-accent hover:text-white transition-none"
            >
              <div>
                <div className="font-body font-extrabold text-[17px]">
                  {recap.title || 'Dernier enregistrement'}
                </div>
                <div className="font-mono text-xs text-muted">
                  {recap.speaker_count ? `${recap.speaker_count} participants` : 'Analyse disponible'}
                </div>
              </div>
              <div className="font-mono text-xs uppercase border-[3px] border-ink px-2.5 py-1">Ouvrir →</div>
            </div>
          ) : (
            <div className="px-5 py-6 font-mono text-[13px] text-muted">
              Aucun enregistrement pour le moment.
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}
