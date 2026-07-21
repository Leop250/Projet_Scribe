import { useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router'
import TopNav from '../components/TopNav'

export default function Token() {
  const [cells, setCells] = useState(['', '', '', '', '', ''])
  const inputsRef = useRef([])
  const navigate = useNavigate()
  const { state } = useLocation()
  const email = state?.email || 'votre adresse'

  function onInput(i, raw) {
    const v = raw.replace(/\D/g, '').slice(0, 1)
    setCells(cs => {
      const next = [...cs]
      next[i] = v
      return next
    })
    if (v && i < 5) inputsRef.current[i + 1]?.focus()
  }

  function resend() {
    setCells(['', '', '', '', '', ''])
    inputsRef.current[0]?.focus()
  }

  return (
    <div className="min-h-screen bg-paper text-ink font-body">
      <TopNav />
      <div className="max-w-[560px] mx-auto px-5 py-14 animate-slam">
        <div
          className="font-mono text-xs uppercase tracking-[2px] mb-3.5 cursor-pointer inline-block"
          onClick={() => navigate('/login')}
        >
          ← Retour
        </div>
        <div className="inline-block font-mono text-xs uppercase tracking-[1px] font-bold bg-accent text-white border-[3px] border-ink px-3 py-1.5 mb-5">
          ● Code envoyé
        </div>
        <h1 className="font-display text-[44px] uppercase tracking-[-2px] m-0 mb-1.5 leading-none">
          Vérification
        </h1>
        <p className="font-mono text-sm m-0 mb-7">Code à 6 chiffres envoyé à {email}</p>

        <div className="flex gap-2.5">
          {cells.map((v, i) => (
            <input
              key={i}
              ref={el => { inputsRef.current[i] = el }}
              value={v}
              onChange={e => onInput(i, e.target.value)}
              maxLength={1}
              inputMode="numeric"
              className="w-full aspect-square text-center border-4 border-ink font-display text-[28px] bg-paper focus:bg-accent"
            />
          ))}
        </div>

        <button
          onClick={() => navigate('/consent')}
          className="cursor-pointer w-full mt-[26px] text-center py-4 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink shadow-[8px_8px_0_#ff2e00] hover:shadow-[2px_2px_0_#ff2e00] hover:translate-x-1.5 hover:translate-y-1.5 transition-none"
        >
          Valider →
        </button>
        <div
          onClick={resend}
          className="cursor-pointer mt-[18px] font-mono text-[13px] text-center underline"
        >
          Réessayer / renvoyer le code
        </div>
      </div>
    </div>
  )
}
