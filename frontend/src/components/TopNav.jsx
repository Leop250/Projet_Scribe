import { useNavigate } from 'react-router'
import Logo from './Logo'

export default function TopNav() {
  const navigate = useNavigate()

  return (
    <div className="sticky top-0 z-50 flex items-center justify-between px-5 h-16 bg-paper border-b-4 border-ink">
      <button
        onClick={() => navigate('/')}
        className="cursor-pointer bg-transparent border-none p-0"
      >
        <Logo size={26} />
      </button>
      <button
        onClick={() => navigate('/login')}
        className="cursor-pointer flex items-center px-[22px] h-10 bg-ink text-white font-mono font-bold text-[13px] uppercase tracking-[1px] border-4 border-ink shadow-[6px_6px_0_#ff2e00] hover:shadow-[2px_2px_0_#ff2e00] hover:translate-x-1 hover:translate-y-1 transition-none"
      >
        Se connecter →
      </button>
    </div>
  )
}
