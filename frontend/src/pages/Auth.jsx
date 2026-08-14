import { useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate } from 'react-router'
import TopNav from '../components/TopNav'
import { useAuth } from '../context/AuthContext'
import { login, registerUser, checkEmailExists, verifyCode, resendCode, forgotPassword, resetPassword } from '../api'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const MAX_PWD_BYTES = 72
function pwdValid(p) {
  return (
    p.length >= 8 &&
    new TextEncoder().encode(p).length <= MAX_PWD_BYTES &&
    /[A-Z]/.test(p) &&
    /[^A-Za-z0-9]/.test(p)
  )
}

function Field({ label, error, shakeKey, children }) {
  const wrapperRef = useRef(null)
  // Lu de façon impérative dans l'effet plutôt que mis en dépendance : on ne
  // veut réagir qu'à un vrai événement shakeKey (soumission échouée), jamais
  // au fait que `error` devienne vrai pendant la frappe.
  const errorRef = useRef(error)
  errorRef.current = error

  useEffect(() => {
    if (!shakeKey || !errorRef.current) return
    const el = wrapperRef.current
    el.classList.remove('animate-glitch')
    void el.offsetWidth // force le reflow pour pouvoir rejouer l'animation
    el.classList.add('animate-glitch')
  }, [shakeKey])

  return (
    <div className="mb-5 last:mb-0">
      <label className="font-mono text-xs uppercase tracking-[1px] font-bold text-ink">{label}</label>
      <div ref={wrapperRef}>{children}</div>
      <div className="font-mono text-[11px] text-accent min-h-[16px] mt-1.5">{error}</div>
    </div>
  )
}

function EyeIcon({ open }) {
  return open ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a18.5 18.5 0 0 1 5.06-5.94M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 7 11 7a18.5 18.5 0 0 1-2.16 3.19M14.12 14.12a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
}

function CodeCells({ cells, onInput, inputsRef }) {
  return (
    <div className="flex gap-2.5 mb-5">
      {cells.map((v, i) => (
        <input
          key={i}
          ref={el => { inputsRef.current[i] = el }}
          value={v}
          onChange={e => onInput(i, e.target.value)}
          inputMode="numeric"
          className="w-full aspect-square text-center border-4 border-ink font-display text-[28px] bg-paper focus:bg-accent"
        />
      ))}
    </div>
  )
}

function ErrorBanner({ error, errorKey }) {
  if (!error) return null
  return (
    <div key={errorKey} className="animate-glitch mb-3.5 px-3.5 py-2.5 border-[3px] border-accent bg-accent/10 font-mono text-[12px] text-accent">
      {error}
    </div>
  )
}

function ResendMessage({ message }) {
  if (!message) return null
  return <div className="mb-3.5 font-mono text-[12px] text-muted">{message}</div>
}

function SubmitButton({ loading, disabled, topMargin, children }) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className={`cursor-pointer w-full ${topMargin ? 'mt-3.5 ' : ''}text-center py-4 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:enabled:bg-accent hover:enabled:text-ink transition-none disabled:opacity-50 disabled:cursor-wait`}
    >
      {loading ? 'Un instant…' : children}
    </button>
  )
}

function ResendLink({ onClick }) {
  return (
    <div onClick={onClick} className="cursor-pointer mt-[18px] font-mono text-[13px] text-center underline">
      Réessayer / renvoyer le code
    </div>
  )
}

function PasswordField({ label, error, shakeKey, value, onChange, showPwd, onToggle }) {
  return (
    <Field label={label} error={error} shakeKey={shakeKey}>
      <div className="relative">
        <input
          type={showPwd ? 'text' : 'password'}
          value={value}
          onChange={onChange}
          placeholder="••••••••"
          className="block w-full my-2 p-3.5 pr-12 font-mono text-[15px] bg-paper border-4"
          style={{ borderColor: error ? '#ff2e00' : '#0a0a0a' }}
        />
        <button
          type="button"
          onClick={onToggle}
          tabIndex={-1}
          aria-label={showPwd ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
          className="cursor-pointer absolute right-3.5 top-1/2 -translate-y-1/2 bg-transparent border-none p-0 text-ink"
        >
          <EyeIcon open={showPwd} />
        </button>
      </div>
    </Field>
  )
}

// POST /token renvoie la même erreur générique pour "mot de passe faux" et
// "compte inexistant" (volontairement, pour la sécurité) — donc on ne peut
// pas s'appuyer dessus pour savoir si l'email existe. Après un échec, on
// interroge GET /users/exists : si l'email est connu, on reste sur place
// avec un message clair (mauvais mot de passe) ; sinon on bascule vers la
// création de compte.
export default function Auth() {
  const [phase, setPhase] = useState('login') // 'login' | 'confirm' | 'code' | 'forgot' | 'reset'
  const [email, setEmail]   = useState('')
  const [pwd, setPwd]       = useState('')
  const [pwd2, setPwd2]     = useState('')
  const [codeCells, setCodeCells] = useState(['', '', '', '', '', ''])
  const codeInputsRef = useRef([])
  const [showPwd, setShowPwd]   = useState(false)
  const [showPwd2, setShowPwd2] = useState(false)
  const [emailTouched, setEmailTouched] = useState(false)
  const [pwdTouched, setPwdTouched]     = useState(false)
  const [pwd2Touched, setPwd2Touched]   = useState(false)
  const [apiError, setApiError] = useState('')
  const [errorKey, setErrorKey] = useState(0)
  const [shakeKey, setShakeKey] = useState(0)
  const [resendMsg, setResendMsg] = useState('')
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()
  const { setToken, isAuthenticated } = useAuth()

  // Un token valide existe déjà (ex: nouvel onglet, ou fenêtre rouverte) —
  // inutile de repasser par le formulaire de connexion.
  if (isAuthenticated) return <Navigate to="/home" replace />

  // Passe par un compteur pour forcer le remount du bandeau d'erreur (donc
  // rejouer l'animation "glitch") même quand deux erreurs de suite ont le
  // même message.
  function showError(msg) {
    setApiError(msg)
    setErrorKey(k => k + 1)
  }

  // Même principe que showError, mais pour faire "glitcher" les champs eux-
  // mêmes quand une tentative de soumission échoue à la validation côté
  // client (email/mot de passe invalide). Sans effet sur un champ qui n'est
  // pas en erreur au moment du clic.
  function shakeInvalidFields() {
    setShakeKey(k => k + 1)
  }

  const emailOk = EMAIL_RE.test(email)
  const passOk  = pwdValid(pwd)
  const pwd2Ok  = pwd === pwd2 && pwd2.length > 0
  const emailShowErr = emailTouched && !emailOk
  const pwdShowErr   = pwdTouched && !passOk
  const pwd2ShowErr  = (phase === 'confirm' || phase === 'reset') && pwd2Touched && !pwd2Ok

  async function submit() {
    setEmailTouched(true)
    setPwdTouched(true)
    setApiError('')
    if (!emailOk || !passOk) {
      shakeInvalidFields()
      return
    }
    if (phase === 'confirm') {
      setPwd2Touched(true)
      if (!pwd2Ok) {
        shakeInvalidFields()
        return
      }
    }

    setLoading(true)
    try {
      if (phase === 'login') {
        try {
          const { access_token } = await login(email, pwd)
          setToken(access_token)
          navigate('/home')
        } catch (err) {
          if (err.status === 403) {
            // Compte connu, mot de passe correct, mais e-mail pas encore
            // vérifié — on renvoie un code frais (l'ancien a pu expirer) et
            // on bascule sur l'écran de vérification, plutôt que de laisser
            // l'utilisateur bloqué sur le formulaire de connexion sans issue.
            try {
              await resendCode(email)
            } catch {
              // Le renvoi peut échouer (rate limit) ; l'utilisateur garde la
              // main via le lien "Réessayer / renvoyer le code" sur l'écran.
            }
            setCodeCells(['', '', '', '', '', ''])
            setPhase('code')
            return
          }
          if (err.status === 429) {
            showError('Trop de tentatives, réessayez plus tard.')
            return
          }
          const known = await checkEmailExists(email)
          if (known) {
            showError('Mot de passe incorrect.')
          } else {
            setPhase('confirm')
          }
        }
      } else {
        const username = email.split('@')[0]
        try {
          await registerUser({ username, email, password: pwd })
        } catch (err) {
          if (err.status === 409) {
            // Le compte existe déjà (précheck ou conflit d'unicité en base) :
            // l'échec de connexion initial venait donc bien d'un mauvais
            // mot de passe.
            showError('Ce compte existe déjà — mot de passe incorrect.')
            setPhase('login')
            return
          }
          throw err
        }
        // Le compte est créé mais pas encore vérifié : il faut entrer le
        // code reçu par e-mail avant de pouvoir se connecter.
        setCodeCells(['', '', '', '', '', ''])
        setPhase('code')
      }
    } catch (err) {
      showError(err.message || 'Une erreur est survenue.')
    } finally {
      setLoading(false)
    }
  }

  function onCodeInput(i, raw) {
    const digits = raw.replace(/\D/g, '')
    if (digits.length > 1) {
      // Collage d'un code complet — on le répartit sur les cases à partir d'ici.
      setCodeCells(cs => {
        const next = [...cs]
        for (let j = 0; j < digits.length && i + j < 6; j++) next[i + j] = digits[j]
        return next
      })
      codeInputsRef.current[Math.min(i + digits.length, 6) - 1]?.focus()
      return
    }
    const v = digits.slice(0, 1)
    setCodeCells(cs => {
      const next = [...cs]
      next[i] = v
      return next
    })
    if (v && i < 5) codeInputsRef.current[i + 1]?.focus()
  }

  async function submitCode() {
    const code = codeCells.join('')
    if (code.length < 6) return
    setApiError('')
    setLoading(true)
    try {
      const { access_token } = await verifyCode(email, code)
      setToken(access_token)
      navigate('/consent')
    } catch (err) {
      showError(err.message || 'Code invalide.')
    } finally {
      setLoading(false)
    }
  }

  async function handleResend() {
    setApiError('')
    setResendMsg('')
    try {
      if (phase === 'reset') await forgotPassword(email)
      else await resendCode(email)
      setCodeCells(['', '', '', '', '', ''])
      codeInputsRef.current[0]?.focus()
      setResendMsg('Nouveau code envoyé.')
    } catch (err) {
      showError(err.message || "Le renvoi a échoué.")
    }
  }

  async function submitForgotPassword() {
    setEmailTouched(true)
    setApiError('')
    if (!emailOk) {
      shakeInvalidFields()
      return
    }

    setLoading(true)
    try {
      await forgotPassword(email)
      setCodeCells(['', '', '', '', '', ''])
      setPwd('')
      setPwd2('')
      setPwdTouched(false)
      setPwd2Touched(false)
      setPhase('reset')
    } catch (err) {
      showError(err.message || 'Une erreur est survenue.')
    } finally {
      setLoading(false)
    }
  }

  async function submitResetPassword() {
    setPwdTouched(true)
    setPwd2Touched(true)
    const code = codeCells.join('')
    if (code.length < 6 || !passOk || !pwd2Ok) {
      shakeInvalidFields()
      return
    }

    setApiError('')
    setLoading(true)
    try {
      const { access_token } = await resetPassword(email, code, pwd)
      setToken(access_token)
      navigate('/home')
    } catch (err) {
      showError(err.message || 'Code invalide ou expiré.')
    } finally {
      setLoading(false)
    }
  }

  function backToLogin() {
    setPhase('login')
    setApiError('')
    setResendMsg('')
    setPwd2('')
    setPwd2Touched(false)
  }

  function goToForgotPassword() {
    setPhase('forgot')
    setApiError('')
    setResendMsg('')
    setPwd('')
    setPwd2('')
    setPwdTouched(false)
    setPwd2Touched(false)
  }

  return (
    <div className="min-h-screen bg-paper text-ink font-body">
      <TopNav />
      <div className="min-h-[calc(100dvh-4rem)] flex items-start justify-center px-5 pt-[8vh] pb-10">
      <div key={phase} className="w-full max-w-[560px] animate-slam">
        <div
          className="font-mono text-xs uppercase tracking-[2px] mb-3.5 cursor-pointer inline-block"
          onClick={() => navigate('/')}
        >
          ← Retour
        </div>
        <h1 className="font-display text-[40px] uppercase tracking-[-2px] m-0 mb-1 leading-none">
          {phase === 'confirm' ? 'Créer un compte'
            : phase === 'code' ? 'Vérification'
            : phase === 'forgot' ? 'Mot de passe oublié'
            : phase === 'reset' ? 'Nouveau mot de passe'
            : 'Authentification'}
        </h1>
        <p className="font-mono text-sm m-0 mb-7">
          {phase === 'confirm' && 'Connexion refusée — créer un compte avec cet e-mail ?'}
          {phase === 'code' && `Code à 6 chiffres envoyé à ${email}.`}
          {phase === 'forgot' && "Indique ton e-mail, on t'envoie un code de réinitialisation."}
          {phase === 'reset' && `Code envoyé à ${email}. Choisis un nouveau mot de passe.`}
          {phase === 'login' && 'Content de vous revoir.'}
        </p>

        {phase === 'code' ? (
          <form onSubmit={e => { e.preventDefault(); submitCode() }} className="border-4 border-ink shadow-[10px_10px_0_#ff2e00] px-6 py-7 bg-paper">
            <CodeCells cells={codeCells} onInput={onCodeInput} inputsRef={codeInputsRef} />

            <ErrorBanner error={apiError} errorKey={errorKey} />
            {!apiError && <ResendMessage message={resendMsg} />}

            <SubmitButton loading={loading} disabled={loading || codeCells.join('').length < 6}>
              Valider →
            </SubmitButton>
            <ResendLink onClick={handleResend} />
          </form>
        ) : phase === 'forgot' ? (
          <form onSubmit={e => { e.preventDefault(); submitForgotPassword() }} className="border-4 border-ink shadow-[10px_10px_0_#ff2e00] px-6 py-7 bg-paper">
            <Field label="E-mail" error={emailShowErr ? 'E-mail invalide.' : ''} shakeKey={shakeKey}>
              <input
                value={email}
                onChange={e => { setEmail(e.target.value); setEmailTouched(true); setApiError('') }}
                placeholder="vous@entreprise.fr"
                className="block w-full my-2 p-3.5 font-mono text-[15px] bg-paper border-4"
                style={{ borderColor: emailShowErr ? '#ff2e00' : '#0a0a0a' }}
              />
            </Field>

            <ErrorBanner error={apiError} errorKey={errorKey} />

            <SubmitButton loading={loading} disabled={loading} topMargin>
              Envoyer le code →
            </SubmitButton>
          </form>
        ) : phase === 'reset' ? (
          <form onSubmit={e => { e.preventDefault(); submitResetPassword() }} className="border-4 border-ink shadow-[10px_10px_0_#ff2e00] px-6 py-7 bg-paper">
            <CodeCells cells={codeCells} onInput={onCodeInput} inputsRef={codeInputsRef} />

            <PasswordField
              label="Nouveau mot de passe"
              error={pwdShowErr ? '8-72 caractères, 1 majuscule, 1 caractère spécial.' : ''}
              shakeKey={shakeKey}
              value={pwd}
              onChange={e => { setPwd(e.target.value); setPwdTouched(true) }}
              showPwd={showPwd}
              onToggle={() => setShowPwd(s => !s)}
            />

            <PasswordField
              label="Confirmer le mot de passe"
              error={pwd2ShowErr ? 'Les mots de passe ne correspondent pas.' : ''}
              shakeKey={shakeKey}
              value={pwd2}
              onChange={e => { setPwd2(e.target.value); setPwd2Touched(true) }}
              showPwd={showPwd2}
              onToggle={() => setShowPwd2(s => !s)}
            />

            <ErrorBanner error={apiError} errorKey={errorKey} />
            {!apiError && <ResendMessage message={resendMsg} />}

            <SubmitButton loading={loading} disabled={loading || codeCells.join('').length < 6}>
              Réinitialiser →
            </SubmitButton>
            <ResendLink onClick={handleResend} />
          </form>
        ) : (
          <form onSubmit={e => { e.preventDefault(); submit() }} className="border-4 border-ink shadow-[10px_10px_0_#ff2e00] px-6 py-7 bg-paper">
            <Field label="E-mail" error={emailShowErr ? 'E-mail invalide.' : ''} shakeKey={shakeKey}>
              <input
                value={email}
                onChange={e => { setEmail(e.target.value); setEmailTouched(true); setApiError(''); if (phase === 'confirm') backToLogin() }}
                placeholder="vous@entreprise.fr"
                className="block w-full my-2 p-3.5 font-mono text-[15px] bg-paper border-4"
                style={{ borderColor: emailShowErr ? '#ff2e00' : '#0a0a0a' }}
              />
            </Field>

            <PasswordField
              label="Mot de passe"
              error={pwdShowErr ? '8-72 caractères, 1 majuscule, 1 caractère spécial.' : ''}
              shakeKey={shakeKey}
              value={pwd}
              onChange={e => { setPwd(e.target.value); setPwdTouched(true) }}
              showPwd={showPwd}
              onToggle={() => setShowPwd(s => !s)}
            />

            {phase === 'confirm' && (
              <PasswordField
                label="Confirmer le mot de passe"
                error={pwd2ShowErr ? 'Les mots de passe ne correspondent pas.' : ''}
                value={pwd2}
                onChange={e => { setPwd2(e.target.value); setPwd2Touched(true) }}
                showPwd={showPwd2}
                onToggle={() => setShowPwd2(s => !s)}
              />
            )}

            {phase === 'login' && (
              <div
                onClick={goToForgotPassword}
                className="cursor-pointer -mt-1.5 mb-3.5 font-mono text-[12px] text-right underline"
              >
                Mot de passe oublié ?
              </div>
            )}

            <ErrorBanner error={apiError} errorKey={errorKey} />

            <SubmitButton loading={loading} disabled={loading} topMargin>
              {phase === 'confirm' ? 'Créer mon compte →' : 'Continuer →'}
            </SubmitButton>
          </form>
        )}

        {(phase === 'confirm' || phase === 'forgot' || phase === 'reset') && (
          <div
            onClick={backToLogin}
            className="cursor-pointer mt-5 font-mono text-[13px] text-center"
          >
            {phase === 'confirm' ? "Ce n'est pas moi / mauvais e-mail — revenir à la connexion" : '← Revenir à la connexion'}
          </div>
        )}
      </div>
      </div>
    </div>
  )
}
