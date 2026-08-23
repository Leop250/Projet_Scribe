import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import AppShell from '../components/AppShell'
import { RecapContent, RecapSkeleton } from '../components/RecapView'
import { useRecap } from '../context/RecapContext'
import { useAuth } from '../context/AuthContext'
import { getRecap } from '../api'
import { SOURCE_LABEL, displaySource } from '../utils/recapSource'

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function RecapDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { recap: lastRecap } = useRecap()
  const { token } = useAuth()

  const [recap, setRecapState] = useState(lastRecap?.id === Number(id) ? lastRecap : null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    if (lastRecap?.id === Number(id)) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setRecapState(lastRecap)
      return
    }
    setRecapState(null)
    setError(false)
    getRecap(id, token)
      .then(data => { if (!cancelled) setRecapState(data) })
      .catch(() => { if (!cancelled) setError(true) })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, token])

  return (
    <AppShell>
      <div className="p-6 md:p-10 max-w-[820px]">
        <button
          type="button"
          onClick={() => navigate('/recap')}
          className="cursor-pointer bg-transparent border-none p-0 font-mono text-xs uppercase tracking-[2px] mb-3.5 inline-block"
        >
          ← Retour aux récaps
        </button>

        <h2 className="font-display text-[34px] uppercase tracking-[-1px] m-0 mb-1.5 leading-none">
          {recap?.name || 'Compte-rendu'}
        </h2>
        {!error && (
          <div className="font-mono text-[13px] text-muted mb-6">
            {recap
              ? `${SOURCE_LABEL[displaySource(recap.source)] || recap.source} · ${formatDate(recap.created_at)}`
              : "En attente de l'analyse…"}
          </div>
        )}

        {error ? (
          <div className="border-4 border-ink px-6 py-10 text-center font-mono text-sm text-muted mt-6">
            Impossible de charger ce compte-rendu.
          </div>
        ) : recap ? (
          <RecapContent recap={recap} />
        ) : (
          <RecapSkeleton />
        )}
      </div>
    </AppShell>
  )
}
