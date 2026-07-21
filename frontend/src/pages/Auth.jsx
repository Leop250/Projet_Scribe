import { useState } from 'react'
import { useNavigate } from 'react-router'
import TopNav from '../components/TopNav'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
function pwdValid(p) {
  return p.length >= 8 && /[A-Z]/.test(p) && /[^A-Za-z0-9]/.test(p)
}

function Field({ label, error, children }) {
  return (
    <div className="mb-5 last:mb-0">
      <label className="font-mono text-xs uppercase tracking-[1px] font-bold text-ink">{label}</label>
      {children}
      <div className="font-mono text-[11px] text-accent min-h-[16px] mt-1.5">{error}</div>
    </div>
  )
}

export default function Auth() {
  const [signup, setSignup] = useState(false)
  const [name, setName]     = useState('')
  const [email, setEmail]   = useState('')
  const [pwd, setPwd]       = useState('')
  const [emailTouched, setEmailTouched] = useState(false)
  const [pwdTouched, setPwdTouched]     = useState(false)
  const navigate = useNavigate()

  const emailOk = EMAIL_RE.test(email)
  const passOk  = pwdValid(pwd)
  const emailShowErr = emailTouched && !emailOk
  const pwdShowErr   = pwdTouched && !passOk

  function submit() {
    setEmailTouched(true)
    setPwdTouched(true)
    if (emailOk && passOk) navigate('/token', { state: { email } })
  }

  return (
    <div className="min-h-screen bg-paper text-ink font-body">
      <TopNav />
      <div className="max-w-[560px] mx-auto px-5 py-14 animate-slam">
        <div
          className="font-mono text-xs uppercase tracking-[2px] mb-3.5 cursor-pointer inline-block"
          onClick={() => navigate('/')}
        >
          ← Retour
        </div>
        <h1 className="font-display text-5xl uppercase tracking-[-2px] m-0 mb-1">
          {signup ? 'Créer un compte' : 'Connexion'}
        </h1>
        <p className="font-mono text-sm m-0 mb-7">
          {signup ? 'Deux minutes, pas de carte bancaire.' : 'Content de vous revoir.'}
        </p>

        <div className="border-4 border-ink shadow-[10px_10px_0_#0a0a0a] px-6 py-7 bg-paper">
          {signup && (
            <Field label="Nom complet">
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Jean Dupont"
                className="block w-full my-2 p-3.5 border-4 border-ink font-mono text-[15px] bg-paper"
              />
            </Field>
          )}

          <Field label="E-mail" error={emailShowErr ? 'E-mail invalide.' : ''}>
            <input
              value={email}
              onChange={e => { setEmail(e.target.value); setEmailTouched(true) }}
              placeholder="vous@entreprise.fr"
              className="block w-full my-2 p-3.5 font-mono text-[15px] bg-paper border-4"
              style={{ borderColor: emailShowErr ? '#ff2e00' : '#0a0a0a' }}
            />
          </Field>

          <Field label="Mot de passe" error={pwdShowErr ? '8+ caractères, 1 majuscule, 1 caractère spécial.' : ''}>
            <input
              type="password"
              value={pwd}
              onChange={e => { setPwd(e.target.value); setPwdTouched(true) }}
              placeholder="••••••••"
              className="block w-full my-2 p-3.5 font-mono text-[15px] bg-paper border-4"
              style={{ borderColor: pwdShowErr ? '#ff2e00' : '#0a0a0a' }}
            />
          </Field>

          <button
            onClick={submit}
            className="cursor-pointer w-full mt-3.5 text-center py-4 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:bg-accent hover:text-ink transition-none"
          >
            {signup ? "S'inscrire →" : 'Se connecter →'}
          </button>
        </div>

        <div
          onClick={() => setSignup(s => !s)}
          className="cursor-pointer mt-5 font-mono text-[13px] text-center"
        >
          {signup ? 'Déjà un compte ? Se connecter' : "Pas de compte ? S'inscrire"}
        </div>
      </div>
    </div>
  )
}
