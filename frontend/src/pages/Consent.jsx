import { useState } from 'react'
import { useNavigate } from 'react-router'
import Logo from '../components/Logo'

function ShieldIcon() {
  return (
    <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </svg>
  )
}

function ArrowIcon() {
  return (
    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <line x1="5" y1="12" x2="19" y2="12"/>
      <polyline points="12 5 19 12 12 19"/>
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  )
}

function Checkbox({ checked, onChange, children }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <button
        role="checkbox"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`mt-0.5 w-5 h-5 rounded-[6px] border-2 flex items-center justify-center shrink-0 transition-all cursor-pointer ${
          checked
            ? 'bg-accent border-accent text-white'
            : 'bg-transparent border-[rgba(255,255,255,0.20)]'
        }`}
      >
        {checked && <CheckIcon />}
      </button>
      <span className="text-[13px] leading-[1.5] text-ink">{children}</span>
    </label>
  )
}

export default function Consent() {
  const [required, setRequired]   = useState(false)
  const [analytics, setAnalytics] = useState(false)
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-page flex flex-col items-center justify-start md:justify-center px-5 md:px-0">
      <div className="w-full max-w-[430px] bg-bg md:rounded-[24px] md:border md:border-[rgba(255,255,255,0.08)] md:shadow-[0_32px_80px_rgba(0,0,0,0.5)] px-[22px] md:px-10 py-10 md:py-12">

        {/* Brand */}
        <div className="flex flex-col items-center mb-8">
          <Logo />
          <div className="mt-4 font-display text-[28px] font-bold tracking-[-0.02em] text-ink">
            recapp<span className="text-accent">.</span>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-2">
          <span className="text-accent"><ShieldIcon /></span>
          <h1 className="font-display text-[21px] font-bold tracking-[-0.02em] text-ink">
            Consentement RGPD
          </h1>
        </div>
        <p className="text-[13px] text-muted leading-[1.6] mb-6">
          Avant d'utiliser Scribe, nous avons besoin de votre accord pour enregistrer et traiter vos réunions.
        </p>

        <div className="flex flex-col gap-4 bg-surface rounded-[18px] p-5 mb-6">
          <Checkbox checked={required} onChange={setRequired}>
            J'autorise l'enregistrement et la transcription de mes réunions{' '}
            <span className="text-accent font-semibold">(requis)</span>
          </Checkbox>
          <div className="h-px bg-[rgba(255,255,255,0.08)]" />
          <Checkbox checked={analytics} onChange={setAnalytics}>
            Accepter les données d'analyse anonymes pour améliorer le service (optionnel)
          </Checkbox>
        </div>

        <p className="text-[12px] text-muted leading-[1.5] mb-6">
          Vos données sont hébergées en Europe et ne sont jamais revendues. Vous pouvez révoquer votre consentement à tout moment dans les réglages.
        </p>

        <button
          disabled={!required}
          onClick={() => required && navigate('/home')}
          className={`w-full h-12 flex items-center justify-center gap-2 rounded-[13px] text-[15px] font-bold transition-all border-none ${
            required
              ? 'bg-accent text-white hover:opacity-90 cursor-pointer'
              : 'bg-[rgba(255,255,255,0.08)] text-muted cursor-not-allowed'
          }`}
        >
          Accepter &amp; continuer
          {required && <ArrowIcon />}
        </button>

      </div>
    </div>
  )
}
