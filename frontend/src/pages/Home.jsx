import { useNavigate } from 'react-router'
import AppShell from '../components/AppShell'
import { useRecap } from '../context/RecapContext'

const STEPS = [
  { n: '01', t: 'Présence', d: 'Générez un QR code, vos invités signent depuis leur téléphone.' },
  { n: '02', t: 'Enregistre', d: 'Un clic sur Rec, la réunion tourne, le waveform confirme que ça capte.' },
  { n: '03', t: 'Récupère', d: 'Résumé, actions et transcription arrivent dans Récaps à la fin.' },
]

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
            className="cursor-pointer w-[200px] h-[200px] border-[6px] border-ink bg-accent flex flex-col items-center justify-center shadow-[10px_10px_0_#0a0a0a] hover:shadow-[4px_4px_0_#0a0a0a] hover:translate-x-1.5 hover:translate-y-1.5 transition-none active:scale-[0.98]"
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
            <button
              type="button"
              onClick={() => navigate('/recap')}
              className="cursor-pointer w-full text-left bg-transparent border-none flex items-center justify-between px-5 py-4 hover:bg-accent hover:text-white transition-none active:scale-[0.99]"
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
            </button>
          ) : (
            <div className="px-5 py-6 font-mono text-[13px] text-muted">
              Aucun enregistrement pour le moment.
            </div>
          )}
        </div>

        <div className="flex items-center justify-between mt-10 mb-3.5">
          <h3 className="font-display text-[22px] uppercase tracking-[-1px] m-0">
            Comment ça marche
          </h3>
          <button
            type="button"
            onClick={() => navigate('/recap')}
            className="cursor-pointer bg-transparent border-none p-0 font-mono text-[11px] uppercase tracking-[1px] underline"
          >
            Voir tous les récaps →
          </button>
        </div>
        <div className="border-4 border-ink">
          {STEPS.map((s, i) => (
            <div
              key={s.n}
              className={`flex gap-4 px-5 py-4 ${i > 0 ? 'border-t-[3px] border-ink' : ''}`}
            >
              <span
                className="font-display text-lg shrink-0"
                style={{ WebkitTextStroke: '1.5px currentColor', WebkitTextFillColor: 'transparent' }}
              >
                {s.n}
              </span>
              <div>
                <div className="font-body font-extrabold text-sm uppercase">{s.t}</div>
                <div className="font-mono text-xs text-muted mt-0.5">{s.d}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  )
}
