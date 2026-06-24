import AppShell from '../components/AppShell'
import { useRecap } from '../context/RecapContext'

function SkeletonLine({ className = '' }) {
  return <div className={`h-3 bg-[rgba(255,255,255,0.07)] rounded animate-pulse ${className}`} />
}

function RecapContent({ recap }) {
  // TODO: render real recap data once API shape is confirmed
  // recap shape TBD — will be wired when backend routes are ready
  return (
    <div className="flex flex-col gap-5">
      <pre className="text-[12px] text-muted bg-surface rounded-[14px] p-4 overflow-x-auto">
        {JSON.stringify(recap, null, 2)}
      </pre>
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
