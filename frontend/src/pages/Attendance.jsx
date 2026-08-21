import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { useAuth } from '../context/AuthContext'
import { createAttendanceSession, getAttendanceSessionStatus, startAttendanceSession } from '../api'
import { QRCodeSVG } from 'qrcode.react'

const POLL_INTERVAL_MS = 2500

export default function Attendance() {
  const [headcount, setHeadcount] = useState('')
  const [step, setStep]           = useState('setup') // 'setup' | 'waiting'
  const [session, setSession]     = useState(null) // { sessionToken, signUrl, headcount }
  const [confirmedCount, setConfirmedCount] = useState(0)
  const [error, setError]         = useState('')
  const [loading, setLoading]     = useState(false)

  const { token } = useAuth()
  const navigate  = useNavigate()
  const pollRef   = useRef(null)

  useEffect(() => {
    return () => clearInterval(pollRef.current)
  }, [])

  async function handleCreateSession(e) {
    e.preventDefault()
    const n = parseInt(headcount, 10)
    if (!Number.isInteger(n) || n < 1) {
      setError('Indique un nombre de personnes valide.')
      return
    }

    setError('')
    setLoading(true)
    try {
      const data = await createAttendanceSession(n, token)
      setSession(data)
      setConfirmedCount(0)
      setStep('waiting')

      pollRef.current = setInterval(async () => {
        try {
          const status = await getAttendanceSessionStatus(data.session_token, token)
          setConfirmedCount(status.confirmed_count)
        } catch {
          // Un raté de poll isolé ne doit pas interrompre l'attente — on
          // réessaiera au prochain tick plutôt que de casser l'écran.
        }
      }, POLL_INTERVAL_MS)
    } catch (err) {
      setError(err.message || 'Impossible de créer la session.')
    } finally {
      setLoading(false)
    }
  }

  async function handleStart() {
    if (!session) return
    setError('')
    setLoading(true)
    try {
      await startAttendanceSession(session.session_token, token)
      clearInterval(pollRef.current)
      navigate('/record', { state: { sessionToken: session.session_token } })
    } catch (err) {
      setError(err.message || "Démarrage refusé.")
    } finally {
      setLoading(false)
    }
  }

  const ready = session && confirmedCount >= session.headcount

  return (
    <div className="h-[100dvh] flex flex-col bg-paper text-ink font-body">
      <div className="w-full max-w-[560px] mx-auto flex flex-col flex-1 px-5 md:px-8 py-10 animate-slam">
        <h2 className="font-display text-[32px] uppercase tracking-[-2px] m-0 mb-7 leading-none">
          Présence
        </h2>

        {step === 'setup' && (
          <form onSubmit={handleCreateSession} className="border-4 border-ink shadow-[10px_10px_0_#ff2e00] px-6 py-7 bg-paper">
            <label className="font-mono text-xs uppercase tracking-[1px] font-bold text-ink">
              Nombre de personnes présentes
            </label>
            <input
              type="number"
              min="1"
              inputMode="numeric"
              value={headcount}
              onChange={e => { setHeadcount(e.target.value); setError('') }}
              placeholder="ex: 8"
              className="block w-full my-2 p-3.5 font-mono text-[15px] bg-paper border-4 border-ink"
            />

            {error && (
              <div className="mb-3.5 px-3.5 py-2.5 border-[3px] border-accent bg-accent/10 font-mono text-[12px] text-accent">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="cursor-pointer w-full mt-3.5 text-center py-4 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:enabled:bg-accent hover:enabled:text-ink transition-none disabled:opacity-50 disabled:cursor-wait"
            >
              {loading ? 'Un instant…' : 'Générer le QR code →'}
            </button>
          </form>
        )}

        {step === 'waiting' && session && (
          <>
            <div className="border-4 border-ink p-6 flex flex-col items-center gap-5">
              <QRCodeSVG value={session.sign_url} size={220} bgColor="#ffffff" fgColor="#0a0a0a" />
              <div className="w-full break-all font-mono text-[11px] text-muted text-center">
                {session.sign_url}
              </div>
            </div>

            <div className="flex-1 flex flex-col items-center justify-center gap-1.5 py-6">
              <div className="font-mono text-[13px] uppercase tracking-[1px] text-muted">Signatures</div>
              <div className="font-display text-[52px] leading-none">
                {confirmedCount} / {session.headcount}
              </div>
            </div>

            {error && (
              <div className="mb-3.5 px-3.5 py-2.5 border-[3px] border-accent bg-accent/10 font-mono text-[12px] text-accent">
                {error}
              </div>
            )}

            <button
              onClick={handleStart}
              disabled={!ready || loading}
              className="cursor-pointer w-full py-4 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:enabled:bg-accent hover:enabled:text-ink transition-none disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? 'Un instant…' : ready ? "Démarrer l'enregistrement →" : 'En attente des signatures…'}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
