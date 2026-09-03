import { useNavigate } from 'react-router'
import AppShell from '../components/AppShell'
import GoogleCalendarIntegration from '../components/GoogleCalendarIntegration'
import { useAuth } from '../context/AuthContext'

function InfoRow({ label, value, badge }) {
  return (
    <div className="flex items-center justify-between gap-4 px-5 py-4 border-t-[3px] border-ink first:border-t-0">
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[1px] text-muted">{label}</div>
        <div className="font-body font-extrabold text-[15px] mt-0.5">{value}</div>
      </div>
      {badge}
    </div>
  )
}

function InfoRowSkeleton() {
  return (
    <div className="px-5 py-4 border-t-[3px] border-ink first:border-t-0 flex flex-col gap-2">
      <div className="h-2.5 w-1/4 bg-black/10 animate-pulse" />
      <div className="h-3.5 w-2/5 bg-black/10 animate-pulse" />
    </div>
  )
}

export default function Settings() {
  const navigate = useNavigate()
  const { user, logout, sessionError } = useAuth()

  return (
    <AppShell>
      <div className="p-6 md:p-10 max-w-[820px] mx-auto">
        <h2 className="font-display text-[40px] uppercase tracking-[-2px] m-0 mb-7 leading-none">
          Réglages
        </h2>

        <h3 className="font-display text-[22px] uppercase tracking-[-1px] mb-3.5">
          Compte
        </h3>
        <div className="border-4 border-ink mb-10">
          {user ? (
            <>
              <InfoRow label="Nom d'utilisateur" value={user.username} />
              <InfoRow
                label="E-mail"
                value={user.email}
                badge={
                  <span
                    className="font-mono text-[10px] uppercase tracking-[1px] border-2 px-2 py-1 shrink-0"
                    style={{
                      borderColor: user.is_verified ? '#0a0a0a' : '#ff2e00',
                      color: user.is_verified ? '#0a0a0a' : '#ff2e00',
                    }}
                  >
                    {user.is_verified ? 'Vérifié' : 'Non vérifié'}
                  </span>
                }
              />
            </>
          ) : sessionError ? (
            <div className="px-5 py-6 font-mono text-[13px] text-muted">
              Impossible de charger les informations du compte.
            </div>
          ) : (
            <>
              <InfoRowSkeleton />
              <InfoRowSkeleton />
            </>
          )}
        </div>

        <GoogleCalendarIntegration />

        <h3 className="font-display text-[22px] uppercase tracking-[-1px] mb-3.5">
          Confidentialité
        </h3>
        <div className="border-4 border-ink mb-10">
          <button
            type="button"
            onClick={() => navigate('/guidelines')}
            className="cursor-pointer w-full text-left bg-transparent border-none flex items-center justify-between px-5 py-4 hover:bg-accent hover:text-white transition-none active:scale-[0.99]"
          >
            <span className="font-body font-extrabold text-[15px]">Conditions d&apos;utilisation</span>
            <span className="font-mono text-xs uppercase border-[3px] border-ink px-2.5 py-1">Ouvrir →</span>
          </button>
        </div>

        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => navigate('/home')}
            className="cursor-pointer px-6 py-3.5 bg-ink text-white font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:bg-accent transition-none active:scale-[0.98]"
          >
            ← Retour à l&apos;accueil
          </button>
          <button
            onClick={() => { logout(); navigate('/') }}
            className="cursor-pointer px-6 py-3.5 bg-paper text-ink font-mono font-bold uppercase tracking-[1px] border-4 border-ink hover:bg-accent hover:text-white transition-none active:scale-[0.98]"
          >
            Se déconnecter
          </button>
        </div>
      </div>
    </AppShell>
  )
}
