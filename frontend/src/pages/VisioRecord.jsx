import { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router'
import { useRecap } from '../context/RecapContext'

const WS_BASE = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000')
  .replace(/^http/, 'ws')

function StatusDot({ color = 'bg-accent' }) {
  return <span className={`inline-block w-2 h-2 rounded-full ${color} animate-pulse`} />
}

export default function VisioRecord() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const { setRecap } = useRecap()

  const [status, setStatus]           = useState('connecting')   // connecting | live | classifying | done | error
  const [statusMsg, setStatusMsg]     = useState('Connexion au bot…')
  const [segments, setSegments]       = useState([])             // { uid, speaker, text }[]
  const [warning, setWarning]         = useState(null)
  const [error, setError]             = useState(null)
  const wsRef                         = useRef(null)
  const bottomRef                     = useRef(null)

  const nativeId = state?.native_meeting_id
  const platform = state?.platform ?? 'google_meet'
  const provider = state?.provider ?? 'vexa'

  useEffect(() => {
    if (!nativeId) {
      navigate('/home')
      return
    }

    // `active` prevents stale callbacks (React StrictMode mounts twice in dev)
    let active = true

    const ws = new WebSocket(`${WS_BASE}/ws/visio/${nativeId}?provider=${provider}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      if (!active) return
      const msg = JSON.parse(event.data)

      if (msg.type === 'status') {
        setStatusMsg(msg.message)
        setStatus('connecting')
      } else if (msg.type === 'bot_status') {
        const labels = {
          requested: 'Bot envoyé…',
          joining:   'Bot en train de rejoindre…',
          in_meeting: 'Bot dans la réunion',
          done:      'Réunion terminée',
        }
        setStatusMsg(labels[msg.status] ?? msg.status)
      } else if (msg.type === 'warning') {
        setWarning(msg.message)
      } else if (msg.type === 'transcript') {
        setStatus('live')
        setStatusMsg('Réunion en cours')
        setWarning(null)
        setSegments(prev => {
          const uid = msg.uid
          if (!uid) return [...prev, { uid: null, speaker: msg.speaker, text: msg.text }]
          const idx = prev.findIndex(s => s.uid === uid)
          if (idx === -1) return [...prev, { uid, speaker: msg.speaker, text: msg.text }]
          const next = [...prev]
          next[idx] = { uid, speaker: msg.speaker, text: msg.text }
          return next
        })
      } else if (msg.type === 'classifying') {
        setStatus('classifying')
        setStatusMsg('Analyse en cours…')
      } else if (msg.type === 'recap') {
        setStatus('done')
        setRecap(msg.data)
        navigate('/recap')
      } else if (msg.type === 'cancelled') {
        navigate('/home')
      } else if (msg.type === 'session_expired') {
        setStatus('error')
        setError('La session du bot a expiré. Cliquez sur "Retour" et relancez le bot.')
      } else if (msg.type === 'error') {
        setStatus('error')
        setError(msg.message)
      }
    }

    ws.onerror = () => {
      if (!active) return
      setStatus('error')
      setError('Impossible de se connecter au serveur.')
    }

    return () => {
      active = false
      ws.close()
    }
  }, [nativeId])

  // Auto-scroll to latest line
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [segments])

  function handleStop() {
    wsRef.current?.send('stop')
    setStatus('classifying')
    setStatusMsg('Analyse en cours…')
  }

  if (error) {
    return (
      <div className="h-[100dvh] flex flex-col items-center justify-center bg-[#0c0d12] gap-4 px-8 text-center">
        <p className="text-[15px] font-semibold text-white/80">Erreur</p>
        <p className="text-[13px] text-white/40">{error}</p>
        <button
          onClick={() => navigate('/home')}
          className="mt-2 h-10 px-6 rounded-[11px] bg-surface text-ink text-[13px] font-bold border-none cursor-pointer hover:opacity-80 transition-opacity"
        >
          Retour
        </button>
      </div>
    )
  }

  if (status === 'classifying') {
    return (
      <div className="h-[100dvh] flex flex-col items-center justify-center bg-[#0c0d12] gap-5">
        <div className="w-12 h-12 rounded-full border-2 border-white/10 border-t-accent animate-spin" />
        <p className="text-[15px] font-semibold text-white/80">Analyse en cours…</p>
        <p className="text-[13px] text-white/40">Classification par tous les LLMs</p>
      </div>
    )
  }

  return (
    <div className="h-[100dvh] flex flex-col bg-[#0c0d12]">
      <div className="w-full max-w-[700px] mx-auto flex flex-col h-full">

        {/* Top bar */}
        <div className="flex items-center justify-between px-5 md:px-8 pt-10 pb-4 shrink-0">
          <div className="flex items-center gap-2 bg-[rgba(239,68,68,0.14)] px-3 py-1.5 rounded-full">
            <StatusDot color={status === 'live' ? 'bg-accent' : 'bg-white/40'} />
            <span className="text-[#ef4444] text-xs font-bold">
              {status === 'live' ? 'LIVE' : 'BOT'}
            </span>
          </div>
          <span className="text-[13px] font-medium text-white/55">{statusMsg}</span>
        </div>

        {/* Transcript scroll area */}
        <div className="flex-1 overflow-y-auto px-5 md:px-8 flex flex-col gap-3 pb-4">
          {warning && (
            <div className="bg-[rgba(239,68,68,0.12)] border border-[rgba(239,68,68,0.25)] rounded-[12px] px-4 py-3 mb-2">
              <p className="text-[13px] text-accent/90 leading-relaxed">⚠ {warning}</p>
            </div>
          )}

          {segments.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-[13px] text-white/30 text-center">
                {status === 'connecting'
                  ? 'Le bot rejoint la réunion, le transcript apparaîtra ici…'
                  : 'En attente de parole…'}
              </p>
            </div>
          ) : (
            segments.map((seg, i) => (
              <div key={seg.uid ?? i} className="flex flex-col gap-0.5">
                {seg.speaker && (
                  <span className="text-[11px] font-semibold text-accent/70 uppercase tracking-wider">
                    {seg.speaker}
                  </span>
                )}
                <p className="text-[14px] text-white/80 leading-relaxed">{seg.text}</p>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>

        {/* Stop button */}
        <div className="px-5 md:px-8 pb-10 pt-3 shrink-0">
          <button
            onClick={handleStop}
            disabled={status === 'connecting' || status === 'classifying'}
            className="w-full h-12 flex items-center justify-center gap-2 bg-accent rounded-[13px] text-white text-[15px] font-bold cursor-pointer border-none hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span>■</span>
            Arrêter &amp; générer le compte-rendu
          </button>
        </div>

      </div>
    </div>
  )
}
