import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import ScrollSequence3D from '../components/ScrollSequence3D'
import TopNav from '../components/TopNav'

const FEATURES = [
  { n: '01', t: 'Enregistre', d: "Meet, Zoom, Teams ou dictaphone. Un clic, ça tourne. Aucune install côté invités." },
  { n: '02', t: 'Transcrit', d: 'Chaque intervenant identifié, horodaté. Transcription brute, fidèle, exportable.' },
  { n: '03', t: 'Rédige', d: 'Résumé, décisions et actions générés à la fin. Livrés, pas résumés à moitié.' },
]

const MARQUEE_TEXT = 'PARLEZ ● ON ÉCRIT ● GOOGLE MEET ● ZOOM ● TEAMS ● DICTAPHONE ● RÉSUMÉ ● ACTIONS ● TRANSCRIPTION ● '

function CtaButton({ children, onClick, className = '' }) {
  return (
    <button
      onClick={onClick}
      className={`cursor-pointer px-[30px] py-[18px] bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink shadow-[8px_8px_0_#ff2e00] hover:shadow-[2px_2px_0_#ff2e00] hover:translate-x-1.5 hover:translate-y-1.5 transition-none active:scale-[0.98] ${className}`}
    >
      {children}
    </button>
  )
}

export default function Landing() {
  const navigate = useNavigate()
  const go = () => navigate('/login')

  const [tabHidden, setTabHidden] = useState(document.hidden)
  useEffect(() => {
    const onVisibility = () => setTabHidden(document.hidden)
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [])

  return (
    <div className="min-h-screen bg-paper text-ink font-body">
      <TopNav />

      <div id="main-content" tabIndex={-1} className="animate-slam">
        <div
          className="pt-16 px-5 max-w-[1200px] mx-auto grid gap-12 items-center"
          style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))' }}
        >
          <div>
            <div className="font-mono text-[13px] uppercase tracking-[2px] border-[3px] border-ink inline-block px-3 py-1.5 mb-7">
              ● Assistant de réunion — audio → compte-rendu
            </div>
            <h1 className="font-display text-[clamp(48px,9vw,128px)] leading-[0.92] tracking-[-3px] uppercase m-0">
              Parlez.<br />On écrit le<br />
              <span className="bg-accent text-white px-2.5 border-4 border-ink [box-decoration-break:clone] [-webkit-box-decoration-break:clone]">
                compte-rendu
              </span>
            </h1>
            <p className="font-mono text-base max-w-[520px] mt-8 leading-[1.6]">
              What&apos;s On Meeting enregistre, transcrit et rédige. Résumé, décisions, actions — livrés à la fin de chaque réunion. Chiffré. Privé. Brut.
            </p>
            <div className="flex gap-4 mt-8 flex-wrap">
              <CtaButton onClick={go}>Démarrer</CtaButton>
            </div>
          </div>

          <div className="relative pr-2 pb-2">
            <div className="absolute right-0 bottom-0 w-full h-full bg-accent border-4 border-ink" />
            <div className="relative border-4 border-ink bg-paper overflow-hidden">
              <img
                src="/hero-comptes-rendus.jpg"
                alt="Pile de comptes-rendus imprimés, une feuille en suspension, bloc d'encre rouge en fond"
                className="block w-full h-auto contrast-[1.12] saturate-[1.05]"
              />
              <div className="absolute left-0 bottom-0 bg-ink text-white font-mono text-[11px] uppercase tracking-[2px] px-3 py-2">
                Sortie · compte-rendu
              </div>
            </div>
          </div>
        </div>

        <div className="mt-14 border-t-4 border-b-4 border-ink bg-ink overflow-hidden whitespace-nowrap">
          <div className="inline-block animate-marq py-3" style={{ animationPlayState: tabHidden ? 'paused' : 'running' }}>
            <span className="font-display text-white text-[22px] uppercase tracking-[1px]">
              {MARQUEE_TEXT}{MARQUEE_TEXT}
            </span>
          </div>
        </div>

        <ScrollSequence3D />

        <div className="max-w-[1200px] mx-auto mt-20 px-5">
          <h2 className="font-display text-[clamp(32px,5vw,64px)] uppercase tracking-[-2px] m-0 mb-8 leading-[1]">
            Trois choses.<br />Rien de plus.
          </h2>
          <div className="grid gap-0 border-4 border-ink" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {FEATURES.map((f, i) => (
              <div
                key={f.n}
                className={`group p-7 px-6 hover:bg-accent hover:text-white ${i < FEATURES.length - 1 ? 'border-r-4 border-ink' : ''}`}
              >
                <div
                  className="font-display text-[40px] text-ink group-hover:text-white"
                  style={{ WebkitTextStroke: '2px currentColor', WebkitTextFillColor: 'transparent' }}
                >
                  {f.n}
                </div>
                <div className="font-display text-[22px] uppercase mt-3 mb-2">{f.t}</div>
                <div className="font-mono text-sm leading-[1.6]">{f.d}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="max-w-[1200px] mx-auto mt-16 mb-20 px-5">
          <button
            onClick={go}
            className="cursor-pointer w-full text-left border-4 border-ink bg-ink text-white hover:bg-accent hover:text-ink px-8 py-12 flex items-center justify-between flex-wrap gap-5"
          >
            <div className="font-display text-[clamp(28px,4vw,48px)] uppercase tracking-[-1px]">
              PRÊT À ENREGISTRER ?
            </div>
            <span className="cursor-pointer font-mono font-bold text-lg bg-white text-ink border-4 border-ink shadow-[8px_8px_0_#ff2e00] hover:shadow-[2px_2px_0_#ff2e00] hover:translate-x-1.5 hover:translate-y-1.5 transition-none active:scale-[0.98] px-[22px] py-3.5 uppercase">
              Se connecter →
            </span>
          </button>
        </div>

        <div className="border-t-4 border-ink px-5 py-6 flex justify-between items-center font-mono text-xs uppercase tracking-[1px] flex-wrap gap-4">
          <span>What&apos;s On Meeting© 2026</span>
          <div className="flex gap-4 flex-wrap">
            <Link to="/guidelines" className="underline">CGU</Link>
            <Link to="/mentions-legales" className="underline">Mentions légales</Link>
          </div>
          <span>Chiffré · Privé · Sans bla-bla</span>
        </div>
      </div>
    </div>
  )
}
