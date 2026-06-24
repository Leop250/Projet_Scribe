import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router'
import Waveform from '../components/Waveform'
import { useRecap } from '../context/RecapContext'
import { uploadRecording } from '../api'

function fmt(secs) {
  return `${String(Math.floor(secs / 60)).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}`
}

export default function Record() {
  const [seconds, setSeconds]       = useState(0)
  const [processing, setProcessing] = useState(false)
  const [error, setError]           = useState(null)
  const [analyser, setAnalyser]     = useState(null)

  const timerRef    = useRef(null)
  const recorderRef = useRef(null)
  const streamRef   = useRef(null)
  const audioCtxRef = useRef(null)

  const { setRecap } = useRecap()
  const navigate     = useNavigate()

  useEffect(() => {
    async function start() {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
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
        audioCtxRef.current?.close()
        clearInterval(timerRef.current)
        setProcessing(true)

        try {
          const blob = new Blob(chunks, { type: recorder.mimeType })
          const data = await uploadRecording(blob)
          setRecap(data)
          navigate('/recap')
        } catch (err) {
          setError(err.message)
          setProcessing(false)
        }
      }

      recorder.start()
      timerRef.current = setInterval(() => setSeconds(s => s + 1), 1000)
    }

    start().catch(err => setError(err.message))

    return () => {
      recorderRef.current?.stop()
      streamRef.current?.getTracks().forEach(t => t.stop())
      audioCtxRef.current?.close()
      clearInterval(timerRef.current)
    }
  }, [])

  function handleStop() {
    recorderRef.current?.stop()
  }

  if (error) {
    return (
      <div className="h-[100dvh] flex flex-col items-center justify-center bg-[#0c0d12] gap-4 px-8 text-center">
        <p className="text-[15px] font-semibold text-white/80">Une erreur est survenue</p>
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

  if (processing) {
    return (
      <div className="h-[100dvh] flex flex-col items-center justify-center bg-[#0c0d12] gap-5">
        <div className="w-12 h-12 rounded-full border-2 border-white/10 border-t-accent animate-spin" />
        <div className="text-center">
          <p className="text-[15px] font-semibold text-white/80 mb-1">Envoi de l'enregistrement…</p>
          <p className="text-[13px] text-white/40">En attente de la réponse du serveur</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[100dvh] flex flex-col bg-[#0c0d12]">
      <div className="w-full max-w-[700px] mx-auto flex flex-col flex-1">

        {/* Top bar */}
        <div className="flex items-center justify-between px-5 md:px-8 pt-12 pb-4 shrink-0">
          <div className="flex items-center gap-2 bg-[rgba(239,68,68,0.14)] px-3 py-1.5 rounded-full">
            <span className="text-[#ef4444] text-xs font-bold animate-blink">●</span>
            <span className="text-[#ef4444] text-xs font-bold">REC · {fmt(seconds)}</span>
          </div>
          <span className="text-[13px] font-medium text-white/55">Enregistrement en cours</span>
        </div>

        {/* Studio panel */}
        <div className="mx-5 md:mx-8 rounded-[22px] p-6 shrink-0 shadow-[0_24px_50px_rgba(0,0,0,0.4)] bg-[#141418]">
          <p className="text-center text-[13px] text-white/55 mb-1">Enregistrement présentiel</p>
          <p className="text-center font-display font-bold tracking-[-0.02em] text-white text-[34px] leading-none mb-5">
            {fmt(seconds)}
          </p>
          <Waveform active={true} analyser={analyser} />
        </div>

        <div className="flex-1" />

        {/* Stop button */}
        <div className="px-5 md:px-8 pb-10 pt-3 shrink-0">
          <button
            onClick={handleStop}
            className="w-full h-12 flex items-center justify-center gap-2 bg-accent rounded-[13px] text-white text-[15px] font-bold cursor-pointer border-none hover:opacity-90 transition-opacity"
          >
            <span>■</span>
            Arrêter &amp; générer le compte-rendu
          </button>
        </div>

      </div>
    </div>
  )
}
