import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import AppShell from '../components/AppShell'
import { RecapContent, RecapSkeleton } from '../components/RecapView'
import { useRecap } from '../context/RecapContext'
import { useAuth } from '../context/AuthContext'
import { getRecap } from '../api'

const SOURCE_LABEL = { dictaphone: 'Dictaphone', visio: 'Visio' }

// La visio programmée automatiquement par le bot calendrier (source "calendar")
// reste de la visio du point de vue de l'utilisateur — une seule catégorie affichée.
function displaySource(source) {
  return source === 'calendar' ? 'visio' : source
}

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
  const [error, setError] = useState(null)

  useEffect(() => {
    if (lastRecap?.id === Number(id)) {
      setRecapState(lastRecap)
      return
    }
    setRecapState(null)
    setError(null)
    getRecap(id, token)
      .then(setRecapState)
      .catch(err => setError(err.message))
    // lastRecap ne doit déclencher cet effet que via id/token — le réévaluer
    // à chaque changement de lastRecap relancerait un fetch inutile dès
    // qu'un autre enregistrement est uploadé pendant la consultation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, token])

  return (
    <AppShell>
      <div className="p-6 md:p-10 max-w-[820px]">
        <div
          className="font-mono text-xs uppercase tracking-[2px] mb-3.5 cursor-pointer inline-block"
          onClick={() => navigate('/recap')}
        >
          ← Retour aux récaps
        </div>

        <h2 className="font-display text-[34px] uppercase tracking-[-1px] m-0 mb-1.5 leading-none">
          {recap?.name || 'Compte-rendu'}
        </h2>
        <div className="font-mono text-[13px] text-muted mb-6">
          {error
            ? 'Impossible de charger ce compte-rendu.'
            : recap
              ? `${SOURCE_LABEL[displaySource(recap.source)] || recap.source} · ${formatDate(recap.created_at)}`
              : "En attente de l'analyse…"}
        </div>

        {error ? (
          <div className="border-4 border-ink px-6 py-10 text-center font-mono text-sm">{error}</div>
        ) : recap ? (
          <RecapContent recap={recap} />
        ) : (
          <RecapSkeleton />
        )}
      </div>
    </AppShell>
  )
}
