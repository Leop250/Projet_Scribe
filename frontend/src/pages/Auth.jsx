import { useState } from 'react'
import { useNavigate } from 'react-router'
import Logo from '../components/Logo'

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  )
}

function MicrosoftIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 21 21">
      <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
      <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
      <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
      <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
    </svg>
  )
}

function MailIcon() {
  return (
    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
      <polyline points="22,6 12,13 2,6"/>
    </svg>
  )
}

function LockIcon() {
  return (
    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
  )
}

function PersonIcon() {
  return (
    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
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

function Field({ label, icon, placeholder, type }) {
  return (
    <div>
      <div className="text-[12px] font-bold text-ink mb-1.5">{label}</div>
      <div className="flex items-center gap-2.5 bg-surface rounded-[12px] border border-[rgba(255,255,255,0.10)] px-3.5 h-[46px]">
        <span className="text-muted shrink-0">{icon}</span>
        <input
          type={type}
          placeholder={placeholder}
          className="flex-1 bg-transparent border-none outline-none text-[14px] text-ink placeholder:text-muted"
        />
      </div>
    </div>
  )
}

export default function Auth() {
  const [mode, setMode] = useState('login')
  const navigate = useNavigate()
  const go = () => navigate('/consent')

  return (
    <div className="min-h-screen bg-page flex flex-col items-center justify-start md:justify-center px-5 md:px-0">
      <div className="w-full max-w-[430px] bg-bg md:rounded-[24px] md:border md:border-[rgba(255,255,255,0.08)] md:shadow-[0_32px_80px_rgba(0,0,0,0.5)] px-[22px] md:px-10 py-10 md:py-12">

        {/* Brand */}
        <div className="flex flex-col items-center mb-8">
          <Logo />
          <div className="mt-4 font-display text-[28px] font-bold tracking-[-0.02em] text-ink">
            recapp<span className="text-accent">.</span>
          </div>
          <div className="mt-1 text-[13px] text-muted">
            Vos réunions, résumées automatiquement
          </div>
        </div>

        {/* Title */}
        <h1 className="font-display text-[21px] font-bold tracking-[-0.02em] text-ink mb-5">
          {mode === 'login' ? 'Connexion' : 'Créer un compte'}
        </h1>

        {/* SSO */}
        <div className="flex flex-col gap-[9px] mb-5">
          <button onClick={go} className="w-full h-12 flex items-center justify-center gap-3 bg-surface border border-[rgba(255,255,255,0.10)] rounded-[13px] text-[14px] font-bold text-ink hover:bg-[rgba(255,255,255,0.05)] transition-colors cursor-pointer">
            <GoogleIcon />
            Continuer avec Google
          </button>
          <button onClick={go} className="w-full h-12 flex items-center justify-center gap-3 bg-surface border border-[rgba(255,255,255,0.10)] rounded-[13px] text-[14px] font-bold text-ink hover:bg-[rgba(255,255,255,0.05)] transition-colors cursor-pointer">
            <MicrosoftIcon />
            Continuer avec Microsoft
          </button>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-5">
          <div className="flex-1 h-px bg-[rgba(255,255,255,0.10)]" />
          <span className="text-[11px] font-semibold text-muted">ou</span>
          <div className="flex-1 h-px bg-[rgba(255,255,255,0.10)]" />
        </div>

        {/* Fields */}
        <div className="flex flex-col gap-4 mb-5">
          {mode === 'signup' && (
            <Field label="Nom complet" icon={<PersonIcon />} placeholder="Alex Dupont" type="text" />
          )}
          <Field label="E-mail professionnel" icon={<MailIcon />} placeholder="vous@entreprise.fr" type="email" />
          <Field label="Mot de passe" icon={<LockIcon />} placeholder="••••••••" type="password" />
        </div>

        {/* CTA */}
        <button onClick={go} className="w-full h-12 flex items-center justify-center gap-2 bg-accent rounded-[13px] text-white text-[15px] font-bold hover:opacity-90 transition-opacity cursor-pointer border-none">
          {mode === 'login' ? 'Se connecter' : "S'inscrire"}
          <ArrowIcon />
        </button>

        {/* Mode switch */}
        <div className="text-center mt-5 text-[13px] text-muted">
          {mode === 'login' ? (
            <>Pas encore de compte ?{' '}
              <button onClick={() => setMode('signup')} className="text-accent font-bold bg-transparent border-none cursor-pointer">S'inscrire</button>
            </>
          ) : (
            <>Déjà un compte ?{' '}
              <button onClick={() => setMode('login')} className="text-accent font-bold bg-transparent border-none cursor-pointer">Se connecter</button>
            </>
          )}
        </div>

      </div>
    </div>
  )
}
