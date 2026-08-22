const DOT_PALETTE = ['#ff2e00', '#0a0a0a', '#1a56ff', '#8a8a00']

function dotFor(i) {
  return DOT_PALETTE[i % DOT_PALETTE.length]
}

// speakers vient soit de l'agent (liste de chaînes), soit de la diarisation
// visio (liste d'objets { id, names, user_id } via build_speakers_list) : on
// normalise vers une chaîne d'affichage dans les deux cas.
function speakerName(speaker) {
  return typeof speaker === 'string' ? speaker : speaker?.names || 'Inconnu'
}

function SkeletonLine({ className = '' }) {
  return <div className={`h-3 bg-black/10 animate-pulse ${className}`} />
}

function ParticipantChips({ speakers }) {
  if (!speakers?.length) return null
  return (
    <div className="flex flex-wrap gap-2 mb-6">
      {speakers.map((speaker, i) => (
        <div key={`${speakerName(speaker)}-${i}`} className="flex items-center gap-2 border-[3px] border-ink px-3 py-1.5">
          <span className="w-3 h-3 border-2 border-ink shrink-0" style={{ background: dotFor(i) }} />
          <span className="font-mono text-[13px]">{speakerName(speaker)}</span>
        </div>
      ))}
    </div>
  )
}

function SummaryPanel({ summary }) {
  return (
    <div className="border-4 border-ink mb-5">
      <div className="bg-ink text-white px-4 py-2.5 font-mono text-xs uppercase tracking-[1px]">Résumé</div>
      <div className="px-4 py-4.5 font-mono text-sm leading-[1.7] whitespace-pre-line">
        {summary || 'Aucun résumé disponible pour cette réunion.'}
      </div>
    </div>
  )
}

function ActionsPanel({ actions }) {
  return (
    <div className="border-4 border-ink mb-5">
      <div className="bg-accent text-white px-4 py-2.5 font-mono text-xs font-bold uppercase tracking-[1px]">Actions</div>
      {actions?.length > 0 ? (
        actions.map((action, i) => (
          <div key={action.id ?? i} className="flex gap-3 px-4 py-3.5 border-t-[3px] border-ink font-mono text-sm">
            <span className="font-display shrink-0">□</span>
            <span>
              <b>{action.assignee || 'Non assigné'}</b> — {action.label}
            </span>
          </div>
        ))
      ) : (
        <div className="px-4 py-4 font-mono text-sm text-muted">Aucune action détectée.</div>
      )}
    </div>
  )
}

function TranscriptPanel({ transcript, speakers = [] }) {
  const names = speakers.map(speakerName)
  const colorFor = name => {
    const i = names.indexOf(name)
    return dotFor(i >= 0 ? i : 0)
  }
  return (
    <div className="border-4 border-ink">
      <div className="bg-ink text-white px-4 py-2.5 font-mono text-xs uppercase tracking-[1px]">Transcription</div>
      {transcript?.length > 0 ? (
        transcript.map((turn, i) => (
          <div key={i} className="px-4 py-3 border-t-[3px] border-ink font-mono text-[13px] leading-[1.6]">
            <span className="font-bold" style={{ color: colorFor(turn.speaker) }}>{turn.speaker || 'Inconnu'}</span>{' '}
            {turn.time && <span className="text-[#999]">{turn.time}</span>}
            <br />
            {turn.text}
          </div>
        ))
      ) : (
        <div className="px-4 py-4 font-mono text-sm text-muted">Aucune transcription disponible.</div>
      )}
    </div>
  )
}

export function RecapContent({ recap }) {
  return (
    <>
      <ParticipantChips speakers={recap.speakers} />
      <SummaryPanel summary={recap.summary} />
      <ActionsPanel actions={recap.actions} />
      <TranscriptPanel transcript={recap.transcript} speakers={recap.speakers} />
    </>
  )
}

export function RecapSkeleton() {
  return (
    <>
      <div className="border-4 border-ink mb-5">
        <div className="bg-ink text-white px-4 py-2.5 font-mono text-xs uppercase tracking-[1px]">Résumé</div>
        <div className="px-4 py-4.5 flex flex-col gap-2">
          <SkeletonLine />
          <SkeletonLine className="w-5/6" />
          <SkeletonLine className="w-4/5" />
        </div>
      </div>
      <div className="border-4 border-ink mb-5">
        <div className="bg-accent text-white px-4 py-2.5 font-mono text-xs font-bold uppercase tracking-[1px]">Actions</div>
        <div className="px-4 py-4 flex flex-col gap-3">
          <SkeletonLine className="w-2/3" />
          <SkeletonLine className="w-1/2" />
        </div>
      </div>
      <div className="border-4 border-ink">
        <div className="bg-ink text-white px-4 py-2.5 font-mono text-xs uppercase tracking-[1px]">Transcription</div>
        <div className="px-4 py-4 flex flex-col gap-3">
          <SkeletonLine className="w-1/3" />
          <SkeletonLine />
          <SkeletonLine className="w-3/4" />
        </div>
      </div>
    </>
  )
}
