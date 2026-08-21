import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router'
import Logo from '../components/Logo'
import { getPublicAttendanceSession, signAttendance } from '../api'

export default function Sign() {
  const { sessionToken } = useParams()
  const [status, setStatus]   = useState('loading') // 'loading' | 'ready' | 'notfound' | 'done'
  const [session, setSession] = useState(null)
  const [nom, setNom]         = useState('')
  const [hasSignature, setHasSignature] = useState(false)
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const canvasRef  = useRef(null)
  const drawingRef = useRef(false)
  const hasDrawnRef = useRef(false)

  useEffect(() => {
    getPublicAttendanceSession(sessionToken)
      .then(data => {
        setSession(data)
        setStatus(data.status === 'started' || data.status === 'closed' ? 'closed' : 'ready')
      })
      .catch(() => setStatus('notfound'))
  }, [sessionToken])

  useEffect(() => {
    if (status !== 'ready') return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    // Idem : taille physique = taille CSS × devicePixelRatio, sinon flou.
    const rect = canvas.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1
    canvas.width  = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)
    ctx.lineCap  = 'round'
    ctx.lineJoin = 'round'
    ctx.lineWidth = 2.5
    ctx.strokeStyle = '#0a0a0a'

    function pos(e) {
      const r = canvas.getBoundingClientRect()
      return [e.clientX - r.left, e.clientY - r.top]
    }
    function onPointerDown(e) {
      drawingRef.current = true
      const [x, y] = pos(e)
      ctx.beginPath()
      ctx.moveTo(x, y)
    }
    function onPointerMove(e) {
      if (!drawingRef.current) return
      const [x, y] = pos(e)
      ctx.lineTo(x, y)
      ctx.stroke()
      if (!hasDrawnRef.current) {
        hasDrawnRef.current = true
        setHasSignature(true)
      }
    }
    function onPointerUp() {
      drawingRef.current = false
    }

    canvas.addEventListener('pointerdown', onPointerDown)
    canvas.addEventListener('pointermove', onPointerMove)
    canvas.addEventListener('pointerup', onPointerUp)
    canvas.addEventListener('pointercancel', onPointerUp)

    return () => {
      canvas.removeEventListener('pointerdown', onPointerDown)
      canvas.removeEventListener('pointermove', onPointerMove)
      canvas.removeEventListener('pointerup', onPointerUp)
      canvas.removeEventListener('pointercancel', onPointerUp)
    }
  }, [status])

  function clearSignature() {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr)
    hasDrawnRef.current = false
    setHasSignature(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!nom.trim() || !hasSignature) {
      setError(!nom.trim() ? 'Indique ton nom.' : 'Trace ta signature avant de valider.')
      return
    }

    setError('')
    setLoading(true)
    try {
      const image = canvasRef.current.toDataURL('image/png')
      await signAttendance(sessionToken, nom.trim(), image)
      setStatus('done')
    } catch (err) {
      setError(err.message || 'La signature a échoué, réessaie.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-paper text-ink font-body flex flex-col">
      <div className="px-5 py-5">
        <Logo size={22} />
      </div>

      <div className="flex-1 flex flex-col px-5 pb-10 max-w-[480px] w-full mx-auto animate-slam">
        {status === 'loading' && (
          <div className="flex-1 flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-ink border-t-accent animate-spin" />
          </div>
        )}

        {status === 'notfound' && (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
            <p className="font-mono text-sm font-bold uppercase tracking-[1px]">Session introuvable</p>
            <p className="font-mono text-[13px] text-muted">Ce lien n&apos;est plus valide.</p>
          </div>
        )}

        {status === 'closed' && (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
            <p className="font-mono text-sm font-bold uppercase tracking-[1px]">Session clôturée</p>
            <p className="font-mono text-[13px] text-muted">
              L&apos;enregistrement a déjà démarré, la présence n&apos;est plus modifiable.
            </p>
          </div>
        )}

        {status === 'ready' && session && (
          <form onSubmit={handleSubmit} className="flex flex-col flex-1 pt-4">
            <h1 className="font-display text-[30px] uppercase tracking-[-2px] m-0 mb-1 leading-none">
              Confirme ta présence
            </h1>
            <p className="font-mono text-[13px] text-muted mb-6">
              {session.confirmed_count} / {session.headcount} déjà signées
            </p>

            <label className="font-mono text-xs uppercase tracking-[1px] font-bold text-ink">Nom</label>
            <input
              value={nom}
              onChange={e => { setNom(e.target.value); setError('') }}
              placeholder="Prénom Nom"
              className="block w-full my-2 p-3.5 font-mono text-[15px] bg-paper border-4 border-ink"
            />

            <label className="font-mono text-xs uppercase tracking-[1px] font-bold text-ink mt-4">Signature</label>
            <canvas
              ref={canvasRef}
              className="w-full h-[180px] my-2 border-4 border-ink bg-paper"
              style={{ touchAction: 'none' }}
            />
            <button
              type="button"
              onClick={clearSignature}
              className="cursor-pointer self-start font-mono text-[12px] uppercase tracking-[1px] underline mb-4"
            >
              Effacer
            </button>

            {error && (
              <div className="mb-3.5 px-3.5 py-2.5 border-[3px] border-accent bg-accent/10 font-mono text-[12px] text-accent">
                {error}
              </div>
            )}

            <p className="font-mono text-[11px] text-muted mt-auto mb-3">
              En validant, tu acceptes notre{' '}
              <Link to="/confidentialite" target="_blank" className="underline">
                politique de confidentialité
              </Link>.
            </p>

            <button
              type="submit"
              disabled={loading}
              className="cursor-pointer w-full py-4 text-center bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:enabled:bg-accent hover:enabled:text-ink transition-none disabled:opacity-50 disabled:cursor-wait"
            >
              {loading ? 'Un instant…' : 'Valider ma présence →'}
            </button>
          </form>
        )}

        {status === 'done' && (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
            <span className="w-14 h-14 border-4 border-ink flex items-center justify-center font-display text-2xl bg-accent text-white">
              ✕
            </span>
            <p className="font-mono text-sm font-bold uppercase tracking-[1px]">Présence enregistrée</p>
            <p className="font-mono text-[13px] text-muted">Tu peux fermer cette page.</p>
          </div>
        )}
      </div>
    </div>
  )
}
