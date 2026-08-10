import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router'
import Waveform from '../components/Waveform'
import { useRecap } from '../context/RecapContext'
import { useAuth } from '../context/AuthContext'
import { uploadRecording } from '../api'

function fmt(secs) {
  return `${String(Math.floor(secs / 60)).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}`
}

export default function Record() {
  const [seconds, setSeconds]       = useState(0)
  const [processing, setProcessing] = useState(false)
  const [error, setError]           = useState(null)
  const [analyser, setAnalyser]     = useState(null)

  const timerRef      = useRef(null)
  const recorderRef   = useRef(null)
  const streamRef     = useRef(null)
  const audioCtxRef   = useRef(null)
  const handleStopRef = useRef(() => {})

  const { setRecap } = useRecap()
  const { token }    = useAuth()
  const navigate     = useNavigate()

  // L'effet ci-dessous ne doit tourner qu'une fois (il ouvre le micro et le
  // MediaRecorder pour toute la durée de l'enregistrement — le relancer à
  // chaque changement de token couperait l'enregistrement en cours). Le
  // upload en fin d'enregistrement doit pourtant utiliser le token le plus
  // récent, pas celui capturé au montage : on le lit via une ref tenue à
  // jour, sur le même principe que handleStopRef juste au-dessus.
  const tokenRef = useRef(token)
  useEffect(() => {
    tokenRef.current = token
  }, [token])

  useEffect(() => {
    // Guards against the async getUserMedia() race: a React StrictMode
    // double-invoke (or a fast unmount) can leave a stale start() resolving
    // after this effect instance was already cleaned up.
    let cancelled = false
    let stopRequested = false

    async function start() {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      if (cancelled) {
        stream.getTracks().forEach(t => t.stop())
        return
      }
      streamRef.current = stream

      // Wire up Web Audio analyser for real-time waveform
      const audioCtx    = new AudioContext()
      audioCtxRef.current = audioCtx
      const source      = audioCtx.createMediaStreamSource(stream)
      const analyserNode = audioCtx.createAnalyser()
      analyserNode.fftSize = 2048
      source.connect(analyserNode)
      setAnalyser(analyserNode)

      const recorder = new MediaRecorder(stream)
      recorderRef.current = recorder

      const chunks = []
      recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data) }

      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        if (audioCtxRef.current?.state !== 'closed') audioCtxRef.current?.close()
        clearInterval(timerRef.current)
        if (cancelled) return
        setProcessing(true)

        try {
          const blob = new Blob(chunks, { type: recorder.mimeType })
          const data = await uploadRecording(blob, tokenRef.current)
          if (cancelled) return
          setRecap(data)
          navigate('/recap')
        } catch (err) {
          if (cancelled) return
          setError(err.message)
          setProcessing(false)
        }
      }

      recorder.start()
      timerRef.current = setInterval(() => setSeconds(s => s + 1), 1000)

      // The user hit "Arrêter" before the recorder finished initializing —
      // honor it now instead of leaving an unreachable recorder running.
      if (stopRequested) recorder.stop()
    }

    handleStopRef.current = () => {
      if (recorderRef.current) {
        if (recorderRef.current.state !== 'inactive') recorderRef.current.stop()
      } else {
        stopRequested = true
      }
    }

    start().catch(err => { if (!cancelled) setError(err.message) })

    return () => {
      cancelled = true
      if (recorderRef.current?.state !== 'inactive') recorderRef.current?.stop()
      streamRef.current?.getTracks().forEach(t => t.stop())
      if (audioCtxRef.current?.state !== 'closed') audioCtxRef.current?.close()
      clearInterval(timerRef.current)
    }
    // navigate (react-router) et setRecap (setter useState) sont stables à
    // vie — token n'a plus besoin d'être ici puisqu'il est lu via tokenRef.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleStop() {
    handleStopRef.current()
  }

  if (error) {
    return (
      <div className="h-[100dvh] flex flex-col items-center justify-center bg-paper text-ink gap-4 px-8 text-center font-body">
        <p className="font-mono text-sm font-bold uppercase tracking-[1px]">Une erreur est survenue</p>
        <p className="font-mono text-[13px] text-muted">{error}</p>
        <button
          onClick={() => navigate('/home')}
          className="mt-2 h-11 px-6 bg-ink text-white font-mono text-[13px] font-bold uppercase tracking-[1px] border-4 border-ink cursor-pointer hover:bg-accent transition-none"
        >
          Retour
        </button>
      </div>
    )
  }

  if (processing) {
    return (
      <div className="h-[100dvh] flex flex-col items-center justify-center bg-paper text-ink gap-5 font-body">
        <div className="w-12 h-12 border-4 border-ink border-t-accent animate-spin" />
        <div className="text-center">
          <p className="font-mono text-sm font-bold uppercase tracking-[1px] mb-1">Envoi de l'enregistrement…</p>
          <p className="font-mono text-[13px] text-muted">En attente de la réponse du serveur</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[100dvh] flex flex-col bg-paper text-ink font-body">
      <div className="w-full max-w-[700px] mx-auto flex flex-col flex-1 animate-slam">

        {/* Top bar */}
        <div className="flex items-center justify-between px-5 md:px-8 pt-10 pb-6 shrink-0 flex-wrap gap-3">
          <h2 className="font-display text-[32px] uppercase tracking-[-2px] m-0">En direct</h2>
          <div className="font-mono font-bold text-white bg-accent border-4 border-ink px-4 py-2 uppercase animate-blink">
            ● REC {fmt(seconds)}
          </div>
        </div>

        {/* Studio panel */}
        <div className="mx-5 md:mx-8 border-4 border-ink p-5 shrink-0">
          <Waveform active={true} analyser={analyser} />
        </div>

        <div className="flex-1" />

        {/* Stop button */}
        <div className="px-5 md:px-8 pb-10 pt-6 shrink-0">
          <button
            onClick={handleStop}
            className="w-full py-4 flex items-center justify-center gap-2 bg-ink text-white font-mono font-bold text-[15px] uppercase tracking-[1px] cursor-pointer border-4 border-ink hover:bg-accent transition-none"
          >
            <span>■</span>
            Arrêter &amp; générer le compte-rendu
          </button>
        </div>

      </div>
    </div>
  )
}
