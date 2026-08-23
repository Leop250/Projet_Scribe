import { useEffect, useRef } from 'react'

const BAR_COUNT = 34

export default function Waveform({ active, analyser }) {
  const barsRef = useRef([])
  const rafRef  = useRef(null)
  const t0Ref   = useRef(null)

  useEffect(() => {
    if (analyser) {
      const data = new Uint8Array(analyser.frequencyBinCount)
      const step = Math.floor(data.length / BAR_COUNT)

      const frame = () => {
        analyser.getByteTimeDomainData(data)
        barsRef.current.forEach((bar, i) => {
          if (!bar) return
          const sample    = data[i * step] ?? 128
          const amplitude = Math.abs(sample - 128) / 128
          bar.style.height  = `${3 + 45 * amplitude}px`
          bar.style.opacity = String(0.3 + 0.7 * amplitude)
        })
        rafRef.current = requestAnimationFrame(frame)
      }
      rafRef.current = requestAnimationFrame(frame)
      return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
    }

    const frame = (ts) => {
      if (!t0Ref.current) t0Ref.current = ts
      const t = (ts - t0Ref.current) / 1000
      barsRef.current.forEach((bar, i) => {
        if (!bar) return
        if (active) {
          bar.style.height  = `${8 + 34 * (0.5 + 0.5 * Math.sin(i * 0.9 + t * 3))}px`
          bar.style.opacity = String(0.4 + 0.6 * (0.5 + 0.5 * Math.sin(i * 0.7 + t * 2.5)))
        } else {
          bar.style.height  = `${3 + 5 * (0.5 + 0.5 * Math.sin(i * 0.9 + t * 0.6))}px`
          bar.style.opacity = '0.25'
        }
      })
      rafRef.current = requestAnimationFrame(frame)
    }
    rafRef.current = requestAnimationFrame(frame)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [analyser, active])

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      gap: '2.5px', height: '50px', width: '100%',
    }}>
      {Array.from({ length: BAR_COUNT }, (_, i) => (
        <div
          key={i}
          ref={el => { barsRef.current[i] = el }}
          style={{
            width: 4, backgroundColor: '#0a0a0a',
            height: 3, opacity: 0.25,
          }}
        />
      ))}
    </div>
  )
}
