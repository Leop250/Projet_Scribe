import { useState } from 'react'
import { useNavigate } from 'react-router'
import TopNav from '../components/TopNav'

const POINTS = [
  { n: 'A.', t: 'Vous décidez quelles réunions sont enregistrées.' },
  { n: 'B.', t: 'Données chiffrées, supprimables à tout moment.' },
  { n: 'C.', t: 'Aucun partage à des tiers, jamais.' },
]

export default function Consent() {
  const [consent, setConsent] = useState(false)
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-paper text-ink font-body">
      <TopNav />
      <div className="max-w-[620px] mx-auto px-5 py-14 animate-slam">
        <h1 className="font-display text-[44px] uppercase tracking-[-2px] m-0 mb-5 leading-none">
          Consentement
        </h1>

        <div className="border-4 border-ink p-6 font-mono text-sm leading-[1.7]">
          <p className="m-0 mb-3.5">
            Scribe enregistre et transcrit vos réunions pour produire des comptes-rendus.
            Les données sont <b>chiffrées</b> et vous en gardez le contrôle total.
          </p>
          {POINTS.map(p => (
            <div key={p.n} className="flex gap-3 py-2.5 border-t-[3px] border-ink">
              <span className="font-display shrink-0">{p.n}</span>
              <span>{p.t}</span>
            </div>
          ))}
        </div>

        <label
          onClick={() => setConsent(c => !c)}
          className="flex items-start gap-3 mt-[22px] cursor-pointer font-mono text-sm"
        >
          <span
            className="shrink-0 w-[26px] h-[26px] border-4 border-ink flex items-center justify-center font-display text-base"
            style={{ background: consent ? '#ff2e00' : '#ffffff', color: '#ffffff' }}
          >
            {consent ? '✕' : ''}
          </span>
          <span>J&apos;accepte l&apos;enregistrement et le traitement de mes réunions par Scribe.</span>
        </label>

        <button
          disabled={!consent}
          onClick={() => consent && navigate('/home')}
          style={{ opacity: consent ? 1 : 0.4, cursor: consent ? 'pointer' : 'not-allowed' }}
          className="w-full mt-[26px] text-center py-4 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:enabled:bg-accent hover:enabled:text-ink transition-none"
        >
          Entrer dans Scribe →
        </button>
      </div>
    </div>
  )
}
