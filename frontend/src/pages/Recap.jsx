import { useState } from 'react'
import AppShell from '../components/AppShell'
import { useRecap } from '../context/RecapContext'

// ─── Icons ────────────────────────────────────────────────────────────────────

function IconSummary() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 4h12M2 7h9M2 10h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

function IconTranscript() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 6h6M5 9h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

function IconActions() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function IconTasks() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M3 4.5h10M3 8h7M3 11.5h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function SkeletonLine({ className = '' }) {
  return <div className={`h-3 bg-[rgba(255,255,255,0.07)] rounded animate-pulse ${className}`} />
}

function RecapSkeleton() {
  return (
    <div className="flex flex-col gap-5">
      <div className="relative bg-surface rounded-[18px] border border-[rgba(255,255,255,0.10)] shadow-[0_20px_50px_rgba(0,0,0,0.3)] p-[18px] overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(70% 60% at 100% 0%, rgba(239,68,68,.08), transparent 60%)' }} />
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

      <div>
        <SkeletonLine className="w-1/3 mb-4" />
        <div className="flex flex-col gap-2">
          {[1, 2].map(i => (
            <div key={i} className="flex items-center gap-3 bg-surface rounded-[13px] px-4 py-3">
              <div className="w-[30px] h-[30px] rounded-full bg-[rgba(255,255,255,0.07)] animate-pulse shrink-0" />
              <div className="flex-1 h-3 bg-[rgba(255,255,255,0.07)] rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>

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

// ─── Section card ─────────────────────────────────────────────────────────────

function Section({ icon, title, accent = false, children }) {
  return (
    <div className="relative bg-surface rounded-[18px] border border-[rgba(255,255,255,0.08)] p-[18px] overflow-hidden">
      {accent && (
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(70% 60% at 100% 0%, rgba(239,68,68,.08), transparent 60%)' }} />
      )}
      <div className="relative flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-[8px] bg-[rgba(239,68,68,0.12)] text-accent flex items-center justify-center">
          {icon}
        </div>
        <span className="text-[13px] font-semibold text-ink">{title}</span>
      </div>
      <div className="relative">{children}</div>
    </div>
  )
}

// ─── Combo selector ───────────────────────────────────────────────────────────

const STT_LABELS = {
  'groq/whisper-large-v3':       'Groq Whisper Large v3',
  'groq/whisper-large-v3-turbo': 'Groq Whisper Turbo',
  'deepgram/nova-2':             'Deepgram Nova-2',
  'assemblyai/best':             'AssemblyAI',
  'speechmatics/enhanced':       'Speechmatics',
  'openai/whisper-1':            'OpenAI Whisper-1',
  'vexa/google_meet':            'Vexa (Google Meet)',
}

const CLASSIFIER_LABELS = {
  'llama-3.3-70b-versatile': 'Llama 3.3 70B',
  'llama-3.1-8b-instant': 'Llama 3.1 8B',
  'mixtral-8x7b-32768': 'Mixtral 8×7B',
  'gemma2-9b-it': 'Gemma2 9B',
}

function Chip({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-[8px] text-[12px] font-medium transition-colors whitespace-nowrap
        ${active
          ? 'bg-accent text-white'
          : 'bg-[rgba(255,255,255,0.06)] text-muted hover:text-ink hover:bg-[rgba(255,255,255,0.10)]'
        }`}
    >
      {children}
    </button>
  )
}

function ComboSelector({ combos, selectedSTT, setSelectedSTT, selectedClassifier, setSelectedClassifier }) {
  const sttModels = [...new Set(combos.map(c => c.stt_model))]
  const classifierModels = [...new Set(combos.map(c => c.classifier_model))]

  return (
    <div className="flex flex-col gap-3 bg-surface rounded-[18px] border border-[rgba(255,255,255,0.08)] p-4">
      <div>
        <p className="text-[11px] text-muted uppercase tracking-wider mb-2">Transcription STT</p>
        <div className="flex flex-wrap gap-2">
          {sttModels.map(m => (
            <Chip key={m} active={selectedSTT === m} onClick={() => setSelectedSTT(m)}>
              {STT_LABELS[m] ?? m}
            </Chip>
          ))}
        </div>
      </div>
      <div>
        <p className="text-[11px] text-muted uppercase tracking-wider mb-2">Classifier LLM</p>
        <div className="flex flex-wrap gap-2">
          {classifierModels.map(m => (
            <Chip key={m} active={selectedClassifier === m} onClick={() => setSelectedClassifier(m)}>
              {CLASSIFIER_LABELS[m] ?? m}
            </Chip>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Main recap content ───────────────────────────────────────────────────────

function RecapContent({ recap }) {
  const sttModels = [...new Set(recap.combos.map(c => c.stt_model))]
  const classifierModels = [...new Set(recap.combos.map(c => c.classifier_model))]

  const [selectedSTT, setSelectedSTT] = useState(sttModels[0])
  const [selectedClassifier, setSelectedClassifier] = useState(classifierModels[0])

  const combo = recap.combos.find(
    c => c.stt_model === selectedSTT && c.classifier_model === selectedClassifier
  )

  return (
    <div className="flex flex-col gap-4">
      <ComboSelector
        combos={recap.combos}
        selectedSTT={selectedSTT}
        setSelectedSTT={setSelectedSTT}
        selectedClassifier={selectedClassifier}
        setSelectedClassifier={setSelectedClassifier}
      />

      {combo ? (
        <>
          {/* Résumé */}
          <Section icon={<IconSummary />} title="Résumé" accent>
            <p className="text-[13px] text-muted leading-relaxed">{combo.resume || '—'}</p>
          </Section>

          {/* Contenu total */}
          <Section icon={<IconTranscript />} title="Contenu total">
            <p className="text-[13px] text-muted leading-relaxed whitespace-pre-wrap">{combo.transcript || '—'}</p>
            <p className="text-[11px] text-muted mt-3 opacity-50">
              STT : {combo.stt_duration_ms} ms · Classifier : {combo.classifier_duration_ms} ms
            </p>
          </Section>

          {/* Actions & décisions */}
          <Section icon={<IconActions />} title="Actions & décisions">
            {combo.actions_decisions.length === 0 ? (
              <p className="text-[13px] text-muted">Aucune action ou décision détectée.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {combo.actions_decisions.map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 shrink-0" />
                    <span className="text-[13px] text-muted">{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          {/* Tâches assignées */}
          <Section icon={<IconTasks />} title="Tâches assignées">
            {combo.taches_assignees.length === 0 ? (
              <p className="text-[13px] text-muted">Aucune tâche assignée détectée.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {combo.taches_assignees.map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <div className="w-5 h-5 rounded-[5px] border border-[rgba(255,255,255,0.15)] shrink-0 mt-0.5" />
                    <span className="text-[13px] text-muted">{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </Section>
        </>
      ) : (
        <p className="text-[13px] text-muted px-1">
          Ce combo n'est pas disponible.
        </p>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Recap() {
  const { recap } = useRecap()

  return (
    <AppShell>
      <div className="px-4 md:px-10 py-6 md:py-8 max-w-[700px]">

        <div className="md:hidden mb-4">
          <h1 className="font-display text-[18px] font-bold tracking-[-0.02em] text-ink">
            Compte-rendu
          </h1>
          <p className="text-[12px] text-muted mt-0.5">
            {recap ? 'Analyse terminée' : "En attente de l'analyse…"}
          </p>
        </div>

        <p className="hidden md:block text-[13px] text-muted mb-6">
          {recap ? 'Analyse terminée' : "En attente de l'analyse…"}
        </p>

        {recap ? <RecapContent recap={recap} /> : <RecapSkeleton />}

      </div>
    </AppShell>
  )
}
