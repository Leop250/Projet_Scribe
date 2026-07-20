import AppShell from '../components/AppShell'
import { useRecap } from '../context/RecapContext'

function SkeletonLine({ className = '' }) {
  return <div className={`h-3 bg-[rgba(255,255,255,0.07)] rounded animate-pulse ${className}`} />
}

function SummaryIcon() {
  return (
    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="8" y1="13" x2="16" y2="13" />
      <line x1="8" y1="17" x2="16" y2="17" />
    </svg>
  )
}

function initials(name) {
  return (name ?? '').trim().split(/\s+/).filter(Boolean).map(w => w[0]).slice(0, 2).join('').toUpperCase()
}

function SummaryCard({ summary, themes }) {
  return (
    <div className="relative bg-surface rounded-[18px] border border-[rgba(255,255,255,0.10)] shadow-[0_20px_50px_rgba(0,0,0,0.3)] p-[18px] overflow-hidden">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(70% 60% at 100% 0%, rgba(239,68,68,.08), transparent 60%)' }}
      />
      <div className="relative flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-[8px] bg-[rgba(239,68,68,0.14)] flex items-center justify-center text-accent shrink-0">
          <SummaryIcon />
        </div>
        <h3 className="text-[13px] font-bold text-ink">Résumé</h3>
      </div>
      <p className="relative text-[13px] text-white/70 leading-[1.6] whitespace-pre-line">
        {summary || 'Aucun résumé disponible pour cette réunion.'}
      </p>
      {themes?.length > 0 && (
        <div className="relative flex flex-wrap gap-2 mt-4">
          {themes.map(theme => (
            <span key={theme} className="text-[11px] font-semibold text-white/60 bg-[rgba(255,255,255,0.06)] px-2.5 py-1 rounded-full">
              {theme}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function ParticipantsIcon() {
  return (
    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )
}

function ParticipantsSection({ speakerCount, speakers }) {
  if (!speakers?.length && !speakerCount) return null

  return (
    <div className="relative bg-surface rounded-[18px] border border-[rgba(255,255,255,0.10)] p-[18px]">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-[8px] bg-[rgba(239,68,68,0.14)] flex items-center justify-center text-accent shrink-0">
          <ParticipantsIcon />
        </div>
        <h3 className="text-[13px] font-bold text-ink">
          Participants{typeof speakerCount === 'number' ? ` (${speakerCount})` : ''}
        </h3>
      </div>
      {speakers?.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {speakers.map((name, i) => (
            <div key={`${name}-${i}`} className="flex items-center gap-2 bg-[rgba(255,255,255,0.06)] rounded-full pl-1 pr-3 py-1">
              <div className="w-6 h-6 rounded-full bg-[rgba(255,255,255,0.10)] flex items-center justify-center text-[10px] font-bold text-white/70 shrink-0">
                {initials(name) || '?'}
              </div>
              <span className="text-[12px] font-semibold text-white/70">{name}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[13px] text-muted">Aucun interlocuteur identifié.</p>
      )}
    </div>
  )
}

function ActionsSection({ actions }) {
  return (
    <div>
      <h3 className="text-[13px] font-bold text-ink mb-3">Actions</h3>
      {actions?.length > 0 ? (
        <div className="flex flex-col gap-2">
          {actions.map((action, i) => (
            <div key={action.id ?? i} className="flex items-center gap-3 bg-surface rounded-[13px] px-4 py-3 border border-[rgba(255,255,255,0.06)]">
              <div className="w-[30px] h-[30px] rounded-full bg-[rgba(255,255,255,0.07)] flex items-center justify-center text-[11px] font-bold text-white/70 shrink-0">
                {initials(action.assignee) || '?'}
              </div>
              <p className="flex-1 text-[13px] text-white/80">{action.label}</p>
              {action.assignee && (
                <span className="text-[11px] font-semibold text-muted bg-[rgba(255,255,255,0.06)] px-2.5 py-1 rounded-full shrink-0">
                  {action.assignee}
                </span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[13px] text-muted">Aucune action détectée.</p>
      )}
    </div>
  )
}

function TranscriptSection({ transcript }) {
  return (
    <div>
      <h3 className="text-[13px] font-bold text-ink mb-3">Transcription</h3>
      {transcript?.length > 0 ? (
        <div className="flex flex-col gap-4">
          {transcript.map((turn, i) => (
            <div key={i} className="flex gap-3">
              <div className="w-[34px] h-[34px] rounded-full bg-[rgba(255,255,255,0.07)] flex items-center justify-center text-[12px] font-bold text-white/70 shrink-0">
                {initials(turn.speaker) || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-[13px] font-bold text-ink">{turn.speaker || 'Inconnu'}</span>
                  {turn.time && <span className="text-[11px] text-muted">{turn.time}</span>}
                </div>
                <p className="text-[13px] text-white/70 leading-[1.5]">{turn.text}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[13px] text-muted">Aucune transcription disponible.</p>
      )}
    </div>
  )
}

function RecapContent({ recap }) {
  return (
    <div className="flex flex-col gap-5">
      <SummaryCard summary={recap.summary} themes={recap.themes} />
      <ParticipantsSection speakerCount={recap.speaker_count} speakers={recap.speakers} />
      <ActionsSection actions={recap.actions} />
      <TranscriptSection transcript={recap.transcript} />
    </div>
  )
}

function RecapSkeleton() {
  return (
    <div className="flex flex-col gap-5">

      {/* Summary skeleton */}
      <div className="relative bg-surface rounded-[18px] border border-[rgba(255,255,255,0.10)] shadow-[0_20px_50px_rgba(0,0,0,0.3)] p-[18px] overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(70% 60% at 100% 0%, rgba(239,68,68,.08), transparent 60%)' }}
        />
        <div className="relative flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-[8px] bg-[rgba(255,255,255,0.07)] animate-pulse" />
          <SkeletonLine className="w-20" />
        </div>
        <div className="relative flex flex-col gap-2">
          <SkeletonLine />
          <SkeletonLine className="w-5/6" />
          <SkeletonLine className="w-4/5" />
          <SkeletonLine className="w-3/5" />
        </div>
      </div>

      {/* Participants skeleton */}
      <div className="bg-surface rounded-[18px] border border-[rgba(255,255,255,0.10)] p-[18px]">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-[8px] bg-[rgba(255,255,255,0.07)] animate-pulse" />
          <SkeletonLine className="w-24" />
        </div>
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-7 w-20 bg-[rgba(255,255,255,0.06)] rounded-full animate-pulse" />
          ))}
        </div>
      </div>

      {/* Actions skeleton */}
      <div>
        <SkeletonLine className="w-1/3 mb-4" />
        <div className="flex flex-col gap-2">
          {[1, 2].map(i => (
            <div key={i} className="flex items-center gap-3 bg-surface rounded-[13px] px-4 py-3">
              <div className="w-[30px] h-[30px] rounded-full bg-[rgba(255,255,255,0.07)] animate-pulse shrink-0" />
              <div className="flex-1 h-3 bg-[rgba(255,255,255,0.07)] rounded animate-pulse" />
              <div className="w-10 h-5 bg-[rgba(255,255,255,0.07)] rounded-full animate-pulse" />
            </div>
          ))}
        </div>
      </div>

      {/* Transcript skeleton */}
      <div>
        <SkeletonLine className="w-2/5 mb-4" />
        <div className="flex flex-col gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-3">
              <div className="w-[34px] h-[34px] rounded-full bg-[rgba(255,255,255,0.07)] animate-pulse shrink-0" />
              <div className="flex-1 flex flex-col gap-1.5">
                <SkeletonLine className="w-1/3" />
                <SkeletonLine />
                <SkeletonLine className="w-3/4" />
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}

export default function Recap() {
  const { recap } = useRecap()

  return (
    <AppShell>
      <div className="px-4 md:px-10 py-6 md:py-8 max-w-[700px]">

        {/* Mobile page header */}
        <div className="md:hidden mb-4">
          <h1 className="font-display text-[18px] font-bold tracking-[-0.02em] text-ink">
            Compte-rendu
          </h1>
          <p className="text-[12px] text-muted mt-0.5">
            {recap ? 'Analyse terminée' : "En attente de l'analyse…"}
          </p>
        </div>

        {/* Desktop subtitle */}
        <p className="hidden md:block text-[13px] text-muted mb-6">
          {recap ? 'Analyse terminée' : "En attente de l'analyse…"}
        </p>

        {recap ? <RecapContent recap={recap} /> : <RecapSkeleton />}

      </div>
    </AppShell>
  )
}
