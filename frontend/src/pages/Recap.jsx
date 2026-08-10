import AppShell from '../components/AppShell'
import { useRecap } from '../context/RecapContext'

const DOT_PALETTE = ['#ff2e00', '#0a0a0a', '#1a56ff', '#8a8a00']

function dotFor(i) {
  return DOT_PALETTE[i % DOT_PALETTE.length]
}

function ParticipantChips({ speakers }) {
  if (!speakers?.length) return null
  return (
    <div className="flex flex-wrap gap-2 mb-6">
      {speakers.map((name, i) => (
        <div key={`${name}-${i}`} className="flex items-center gap-2 border-[3px] border-ink px-3 py-1.5">
          <span className="w-3 h-3 border-2 border-ink shrink-0" style={{ background: dotFor(i) }} />
          <span className="font-mono text-[13px]">{name}</span>
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
  const colorFor = name => {
    const i = speakers.indexOf(name)
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

function RecapContent({ recap }) {
  return (
    <>
      <ParticipantChips speakers={recap.speakers} />
      <SummaryPanel summary={recap.summary} />
      <ActionsPanel actions={recap.actions} />
      <TranscriptPanel transcript={recap.transcript} speakers={recap.speakers} />
    </>
  )
}

function EmptyRecap() {
  return (
    <div className="border-4 border-ink px-6 py-10 text-center font-mono text-sm text-muted">
      Aucun compte-rendu pour le moment.
    </div>
  )
}

export default function Recap() {
  const { recap } = useRecap()

  return (
    <AppShell>
      <div className="p-6 md:p-10 max-w-[820px] mx-auto">
        <h2 className="font-display text-[34px] uppercase tracking-[-1px] m-0 mb-1.5 leading-none">
          Comptes-rendus
        </h2>
        <div className="font-mono text-[13px] text-muted mb-6">
          {recap ? 'Analyse terminée' : '0 compte-rendu'}
        </div>

        {recap ? <RecapContent recap={recap} /> : <EmptyRecap />}
      </div>
    </AppShell>
  )
}
