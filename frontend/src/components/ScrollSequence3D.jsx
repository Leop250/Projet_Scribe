import { useEffect, useRef, useState } from 'react'

const DOC_WIDTHS = [92, 78, 96, 64, 88, 71, 54]
const DOC_DOTS = ['#ff2e00', '#1a56ff', '#8a8a00', '#0a0a0a', '#ff2e00', '#1a56ff', '#0a0a0a']

function lerp(a, b, t) {
  return a + (b - a) * t
}

function easeInOutQuad(t) {
  return t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2
}

export default function ScrollSequence3D() {
  const sectionRef = useRef(null)
  const rafRef = useRef(null)

  const [p, setP] = useState(0)
  const [reducedMotion, setReducedMotion] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )

  useEffect(() => {
    const mql = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = () => setReducedMotion(mql.matches)
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [])

  useEffect(() => {
    if (reducedMotion) return

    function onScroll() {
      if (rafRef.current) return
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = null
        const el = sectionRef.current
        if (!el) return
        const rect = el.getBoundingClientRect()
        const viewportHeight = document.documentElement.clientHeight || window.innerHeight
        const span = rect.height - viewportHeight
        const next = span > 0 ? Math.min(1, Math.max(0, -rect.top / span)) : 0
        setP(prev => (Math.abs(next - prev) > 0.002 ? next : prev))
      })
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    document.addEventListener('scroll', onScroll, { passive: true, capture: true })
    window.addEventListener('resize', onScroll)
    onScroll()

    return () => {
      window.removeEventListener('scroll', onScroll)
      document.removeEventListener('scroll', onScroll, true)
      window.removeEventListener('resize', onScroll)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
  }, [reducedMotion])

  const effectiveP = reducedMotion ? 1 : p
  const e = easeInOutQuad(effectiveP)

  const rx = lerp(64, 4, e)
  const ry = lerp(-34, 0, e)
  const rz = lerp(-8, 0, e)
  const sc = lerp(0.86, 1, e)

  const morph = Math.min(1, Math.max(0, (effectiveP - 0.42) / 0.34))
  const waveOpacity = 1 - Math.min(1, morph * 1.6)
  const docOpacity = Math.max(0, (morph - 0.35) / 0.65)

  const bars = Array.from({ length: 22 }, (_, i) => {
    const base = Math.abs(Math.sin(i * 1.7 + 0.6)) * 0.78 + 0.12
    const live = base * (0.45 + 0.55 * Math.abs(Math.sin(i * 0.9 + effectiveP * 9)))
    return live * 100
  })

  const slabTitle = morph > 0.5 ? 'Compte-rendu' : 'Captation'
  const slabTag = morph > 0.5 ? 'Prêt' : 'REC'
  const stepAudioActive = effectiveP < 0.4
  const stepTransActive = effectiveP >= 0.4 && effectiveP < 0.76
  const stepRecapActive = effectiveP >= 0.76
  const scrollHint = effectiveP > 0.95 ? 'Livré' : '↓ Continue de scroller'

  return (
    <section ref={sectionRef} className="relative h-[340vh]">
      <div className="sticky top-16 h-[calc(100vh-64px)] overflow-hidden flex items-center justify-center">

        <div className="absolute top-7 inset-x-0 flex justify-center px-5">
          <div className="flex items-center border-4 border-ink">
            <span className={`font-mono font-bold text-xs uppercase tracking-[2px] px-3.5 py-2 ${stepAudioActive ? 'bg-ink text-white' : 'bg-paper text-ink'}`}>
              Audio
            </span>
            <span className={`font-mono font-bold text-xs uppercase tracking-[2px] px-3.5 py-2 border-l-4 border-ink ${stepTransActive ? 'bg-ink text-white' : 'bg-paper text-ink'}`}>
              Transcription
            </span>
            <span className={`font-mono font-bold text-xs uppercase tracking-[2px] px-3.5 py-2 border-l-4 border-ink ${stepRecapActive ? 'bg-accent text-white' : 'bg-paper text-ink'}`}>
              Compte-rendu
            </span>
          </div>
        </div>

        <div className="w-full flex justify-center" style={{ perspective: '1400px', perspectiveOrigin: '50% 45%' }}>
          <div
            className="relative w-[min(560px,84vw)] h-[min(700px,62vh)]"
            style={{
              transformStyle: 'preserve-3d',
              transform: `rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) rotateZ(${rz.toFixed(2)}deg) scale(${sc.toFixed(3)})`,
            }}
          >
            <div className="absolute inset-0 bg-accent border-[6px] border-ink" style={{ transform: 'translateZ(-34px)' }} />
            <div className="absolute left-0 top-0 w-[34px] h-full bg-ink" style={{ transformOrigin: 'left center', transform: 'rotateY(-90deg)' }} />
            <div className="absolute right-0 top-0 w-[34px] h-full bg-ink" style={{ transformOrigin: 'right center', transform: 'rotateY(90deg)' }} />
            <div className="absolute left-0 bottom-0 w-full h-[34px] bg-ink" style={{ transformOrigin: 'center bottom', transform: 'rotateX(-90deg)' }} />

            <div className="absolute inset-0 bg-paper border-[6px] border-ink p-7 flex flex-col overflow-hidden">
              <div className="flex items-center justify-between gap-3 pb-4 border-b-4 border-ink">
                <span className="font-display text-xl uppercase tracking-[-1px]">{slabTitle}</span>
                <span className="font-mono text-[11px] uppercase tracking-[1px] px-2 py-1 bg-accent text-white">{slabTag}</span>
              </div>

              <div className="relative flex-1 mt-5">
                <div className="absolute inset-0 flex items-center gap-1.5" style={{ opacity: waveOpacity }}>
                  {bars.map((h, i) => (
                    <span key={i} className="flex-1 bg-ink" style={{ height: `${h}%` }} />
                  ))}
                </div>

                <div className="absolute inset-0 flex flex-col gap-3.5" style={{ opacity: docOpacity }}>
                  {DOC_WIDTHS.map((w, i) => (
                    <span key={i} className="flex items-center gap-2.5">
                      <span className="w-3.5 h-3.5 flex-shrink-0" style={{ background: DOC_DOTS[i] }} />
                      <span className="h-3 bg-ink" style={{ width: `${w}%` }} />
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="absolute bottom-6 inset-x-0 flex justify-center px-5">
          <span className="font-mono text-xs uppercase tracking-[2px] text-muted">{scrollHint}</span>
        </div>

      </div>
    </section>
  )
}
