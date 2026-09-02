import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { useAuth } from '../context/AuthContext'
import { disconnectGoogleIntegration, getGoogleAuthorizeUrl, getGoogleIntegrationStatus } from '../api'

const SCOPES = [
  "Envoyer à Google Calendar le titre, l'horaire et le récap de tes réunions.",
  'Lire les événements de ton agenda pour préparer les récaps à venir.',
  "Rafraîchir ces infos automatiquement à chaque changement d'agenda.",
]

const GOOGLE_ERROR_MESSAGES = {
  oauth_denied: "Tu as refusé l'autorisation Google.",
  missing_params: 'Réponse Google incomplète, réessaie.',
  bad_state: 'Session expirée, reconnecte-toi puis réessaie.',
  no_refresh_token:
    "Google n'a pas renvoyé d'autorisation durable. Révoque l'accès sur myaccount.google.com/permissions puis réessaie.",
  mb_limit: 'Limite de connexions calendrier atteinte côté MeetingBaaS. Supprime une connexion inutilisée.',
  connect_failed: 'La connexion au calendrier a échoué côté serveur, réessaie.',
}

function formatLastSync(iso) {
  if (!iso) return ''
  const minutes = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 60000))
  return minutes === 0 ? "Rafraîchi à l'instant" : `Rafraîchi il y a ${minutes} min`
}

function AuthorizeModal({ accountEmail, onAuthorize, onCancel, authorizing }) {
  return (
    <div className="fixed inset-0 bg-[rgba(10,10,10,.55)] z-[100] flex items-start justify-center p-6 overflow-y-auto">
      <div className="w-full max-w-[520px] m-auto bg-paper border-[6px] border-ink shadow-[14px_14px_0_#ff2e00] animate-slam">
        <div className="flex items-center justify-between gap-3 p-3 px-4.5 border-b-4 border-ink bg-[#f2f2f2]">
          <span className="font-mono text-[11px] uppercase tracking-[1px] text-muted">accounts.google.com</span>
          <button
            type="button"
            onClick={onCancel}
            className="cursor-pointer w-[26px] h-[26px] border-[3px] border-ink bg-paper font-display text-xs leading-none p-0 flex-shrink-0 hover:bg-accent hover:text-white hover:border-accent"
          >
            ✕
          </button>
        </div>

        <div className="bg-accent text-white px-4.5 py-2.5 border-b-4 border-ink font-mono text-[11px] font-bold uppercase tracking-[2px]">
          ● Autorisation requise
        </div>

        <div className="p-[26px] px-4.5">
          <div className="font-display text-[22px] uppercase tracking-[-1px] leading-[1.05] mb-2">
            Autoriser<br />What&apos;s On Meeting
          </div>
          <p className="font-mono text-xs leading-[1.6] text-muted mb-[18px]">
            L&apos;application enverra les infos de tes réunions et lira ton agenda pour les tenir à jour.
          </p>

          <div className="flex items-center gap-3.5 border-4 border-ink p-3.5 px-4 mb-5">
            <span className="w-[34px] h-[34px] border-[3px] border-ink flex items-center justify-center font-display text-sm flex-shrink-0">
              {accountEmail.charAt(0).toUpperCase()}
            </span>
            <span className="min-w-0">
              <span className="block font-mono text-[10px] uppercase tracking-[1px] text-muted">
                Compte What&apos;s On Meeting
              </span>
              <span className="block font-body font-extrabold text-sm truncate">{accountEmail}</span>
            </span>
          </div>

          <div className="font-mono text-[10px] uppercase tracking-[1px] text-muted mb-2.5">Accès demandé</div>
          <div className="border-[3px] border-ink mb-6">
            {SCOPES.map(scope => (
              <div key={scope} className="flex gap-3 p-3 px-3.5 border-t-2 border-ink first:border-t-0">
                <span className="font-display text-[13px] text-[#1a56ff] flex-shrink-0">→</span>
                <span className="font-mono text-xs leading-[1.5]">{scope}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-3 flex-wrap">
            <button
              type="button"
              onClick={onAuthorize}
              disabled={authorizing}
              className="cursor-pointer px-[26px] py-3.5 bg-ink text-white font-mono font-bold text-[13px] uppercase tracking-[1px] border-4 border-ink shadow-[6px_6px_0_#ff2e00] hover:enabled:shadow-[2px_2px_0_#ff2e00] hover:enabled:translate-x-1 hover:enabled:translate-y-1 transition-none disabled:opacity-50 disabled:cursor-wait"
            >
              {authorizing ? 'Un instant…' : 'Autoriser →'}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="cursor-pointer px-[22px] py-3.5 bg-paper text-ink font-mono font-bold text-[13px] uppercase tracking-[1px] border-4 border-ink hover:bg-ink hover:text-white transition-none"
            >
              Annuler
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function GoogleCalendarIntegration() {
  const { user, token } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()

  const [step, setStep] = useState('idle')
  const [linkedEmail, setLinkedEmail] = useState(null)
  const [lastSyncAt, setLastSyncAt] = useState(null)
  const [error, setError] = useState('')
  const [authorizing, setAuthorizing] = useState(false)

  useEffect(() => {
    let cancelled = false
    const googleParam = searchParams.get('google')

    if (googleParam === 'connected') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStep('connecting')
      setSearchParams(params => { params.delete('google'); return params }, { replace: true })
      getGoogleIntegrationStatus(token)
        .then(data => {
          if (cancelled) return
          if (data.connected) {
            setLinkedEmail(data.email)
            setLastSyncAt(data.last_sync_at)
            setStep('connected')
          } else {
            setStep('idle')
          }
        })
        .catch(() => { if (!cancelled) { setError('Impossible de confirmer la connexion.'); setStep('idle') } })
      return () => { cancelled = true }
    }

    if (googleParam === 'error') {
      const reason = searchParams.get('reason')
      setError(GOOGLE_ERROR_MESSAGES[reason] || 'La connexion à Google Calendar a échoué, réessaie.')
      setSearchParams(params => { params.delete('google'); params.delete('reason'); return params }, { replace: true })
      setStep('idle')
      return () => { cancelled = true }
    }

    getGoogleIntegrationStatus(token)
      .then(data => {
        if (cancelled) return
        if (data.connected) {
          setLinkedEmail(data.email)
          setLastSyncAt(data.last_sync_at)
          setStep('connected')
        }
      })
      .catch(() => {})

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  async function handleAuthorize() {
    setAuthorizing(true)
    setError('')
    try {
      const url = await getGoogleAuthorizeUrl(token)
      window.location.href = url
    } catch (err) {
      setError(err.message || "Impossible d'ouvrir la fenêtre d'autorisation.")
      setAuthorizing(false)
    }
  }

  async function handleDisconnect() {
    setError('')
    try {
      await disconnectGoogleIntegration(token)
    } catch (err) {
      setError(err.message || 'Déconnexion refusée.')
      return
    }
    setLinkedEmail(null)
    setLastSyncAt(null)
    setStep('idle')
  }

  const isConnected = step === 'connected'
  const isConnecting = step === 'connecting'
  const isChoosing = step === 'choose'

  const statusLine = isConnected
    ? 'Agenda associé · lu et rafraîchi en continu'
    : isConnecting || isChoosing
      ? 'Autorisation en cours'
      : 'Non connecté'

  return (
    <>
      <div className="flex items-center justify-between gap-4 mb-3.5 flex-wrap">
        <h3 className="font-display text-[22px] uppercase tracking-[-1px] m-0">Intégrations</h3>
        <span className="font-mono text-[10px] uppercase tracking-[1px] text-muted">
          {isConnected ? '1 active · 2 disponibles' : '0 active · 3 disponibles'}
        </span>
      </div>

      {error && (
        <div className="mb-3.5 px-3.5 py-2.5 border-[3px] border-accent bg-accent/10 font-mono text-xs text-accent">
          {error}
        </div>
      )}

      <div className="border-4 border-ink mb-10">
        <div className="flex items-center justify-between gap-5 p-5 flex-wrap">
          <div className="flex items-center gap-4 min-w-0">
            <div className="w-[54px] h-[54px] border-4 border-ink bg-[#1a56ff] text-white flex items-center justify-center flex-shrink-0 font-display text-[22px] leading-none">
              31
            </div>
            <div className="min-w-0">
              <div className="font-body font-extrabold text-[17px]">Google Calendar</div>
              <div className="font-mono text-xs text-muted mt-0.5">{statusLine}</div>
            </div>
          </div>

          {!isConnected && (
            <button
              type="button"
              onClick={() => setStep('choose')}
              className="cursor-pointer px-6 py-3.5 bg-ink text-white font-mono font-bold text-[13px] uppercase tracking-[1px] border-4 border-ink shadow-[6px_6px_0_#ff2e00] hover:shadow-[2px_2px_0_#ff2e00] hover:translate-x-1 hover:translate-y-1 transition-none flex-shrink-0"
            >
              Connecter →
            </button>
          )}

          {isConnected && (
            <div className="flex items-center gap-2.5 flex-shrink-0">
              <span className="font-mono text-[10px] font-bold uppercase tracking-[1px] bg-ink text-white px-2.5 py-1.5 border-[3px] border-ink animate-check-in">
                ✓ Connecté
              </span>
              <button
                type="button"
                onClick={handleDisconnect}
                className="cursor-pointer px-2.5 py-1.5 bg-paper text-ink font-mono font-bold text-[10px] uppercase tracking-[1px] border-[3px] border-ink hover:bg-accent hover:text-white hover:border-accent"
              >
                Déconnecter
              </button>
            </div>
          )}
        </div>

        {isConnecting && (
          <div className="border-t-4 border-ink p-5 flex items-center gap-3.5 animate-state-in">
            <span className="font-display text-[22px] text-accent animate-blink">●</span>
            <span className="font-mono text-[13px] uppercase tracking-[1px]">Lecture de l&apos;agenda…</span>
          </div>
        )}

        {isConnected && (
          <div className="border-t-4 border-ink animate-state-in">
            <div className="flex items-center justify-between gap-4 px-5 py-4 flex-wrap">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[1px] text-muted">Compte associé</div>
                <div className="font-body font-extrabold text-[15px] mt-0.5">{linkedEmail}</div>
              </div>
              <div className="font-mono text-[11px] text-muted">{formatLastSync(lastSyncAt)}</div>
            </div>
          </div>
        )}
      </div>

      {isChoosing && (
        <AuthorizeModal
          accountEmail={user?.email || ''}
          onAuthorize={handleAuthorize}
          onCancel={() => setStep('idle')}
          authorizing={authorizing}
        />
      )}
    </>
  )
}
