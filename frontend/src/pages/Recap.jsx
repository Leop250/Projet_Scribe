import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import AppShell from '../components/AppShell'
import { useAuth } from '../context/AuthContext'
import { getCalendarEvents, getMyRecaps } from '../api'
import { SOURCE_LABEL, SOURCE_COLOR, displaySource } from '../utils/recapSource'

const SOURCES = [
  { value: 'all', label: 'Tous', color: '#0a0a0a' },
  { value: 'dictaphone', label: 'Dictaphone', icon: '●', color: '#ff2e00' },
  { value: 'visio', label: 'Visio', icon: '◆', color: '#1a56ff' },
]

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatDateTime(iso) {
  if (!iso) return ''
  if (iso.length === 10) {
    return new Date(iso).toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short' })
  }
  const d = new Date(iso)
  const day = d.toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short' })
  const time = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  return `${day} · ${time}`
}

function Chip({ active, color = '#0a0a0a', children, onClick }) {
  return (
    <button
      onClick={onClick}
      className="cursor-pointer border-4 border-ink px-4 py-2 font-mono text-xs font-bold uppercase tracking-[1px] -ml-1 first:ml-0 active:scale-[0.96]"
      style={{ background: active ? color : '#ffffff', borderColor: active ? color : '#0a0a0a', color: active ? '#ffffff' : '#0a0a0a' }}
    >
      {children}
    </button>
  )
}

function StatTile({ label, value, color }) {
  return (
    <div className="border-4 border-ink border-l-[10px] px-4 py-3 bg-paper" style={{ borderLeftColor: color }}>
      <div className="font-mono text-[10px] uppercase tracking-[1px] text-muted">{label}</div>
      <div className="font-display text-[32px] leading-none mt-1" style={{ color }}>{value}</div>
    </div>
  )
}

const WEEKDAYS = ['L', 'M', 'M', 'J', 'V', 'S', 'D']
const MIXED_SOURCE_COLOR = '#7c3aed'
const DOT_MIN_SIZE = 6
const DOT_GROWTH_PER_RECAP = 3
const DOT_MAX_SIZE = 16

function dateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function buildMonthCells(viewDate) {
  const year = viewDate.getFullYear()
  const month = viewDate.getMonth()
  const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const cells = Array(firstWeekday).fill(null)
  for (let day = 1; day <= daysInMonth; day++) cells.push(new Date(year, month, day))
  return cells
}

function dayDotColor(sources) {
  if (sources.size > 1) return MIXED_SOURCE_COLOR
  return SOURCE_COLOR[[...sources][0]] || '#0a0a0a'
}

function dayDotSize(count) {
  return Math.min(DOT_MIN_SIZE + (count - 1) * DOT_GROWTH_PER_RECAP, DOT_MAX_SIZE)
}

function Calendar({ dayStats, selected, onSelect }) {
  const [viewDate, setViewDate] = useState(() => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth(), 1)
  })

  const cells = useMemo(() => buildMonthCells(viewDate), [viewDate])
  const monthLabel = viewDate.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
  const today = dateKey(new Date())

  return (
    <div className="border-4 border-ink p-4 w-full max-w-[320px]">
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={() => setViewDate(d => new Date(d.getFullYear(), d.getMonth() - 1, 1))}
          className="cursor-pointer font-mono text-sm w-7 h-7 border-2 border-ink bg-paper hover:bg-ink hover:text-white transition-none active:scale-[0.97]"
        >
          ←
        </button>
        <div className="font-mono text-xs uppercase tracking-[1px] font-bold">{monthLabel}</div>
        <button
          onClick={() => setViewDate(d => new Date(d.getFullYear(), d.getMonth() + 1, 1))}
          className="cursor-pointer font-mono text-sm w-7 h-7 border-2 border-ink bg-paper hover:bg-ink hover:text-white transition-none active:scale-[0.97]"
        >
          →
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 mb-1">
        {WEEKDAYS.map((w, i) => (
          <div key={i} className="font-mono text-[9px] uppercase text-muted text-center">{w}</div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {cells.map((d, i) => {
          if (!d) return <div key={i} />
          const key = dateKey(d)
          const stats = dayStats.get(key)
          const isSelected = selected === key
          const isToday = key === today
          const dotSize = stats ? dayDotSize(stats.count) : 0
          const dotColor = stats ? (isSelected ? '#ffffff' : dayDotColor(stats.sources)) : 'transparent'
          return (
            <button
              key={i}
              onClick={() => onSelect(isSelected ? null : key)}
              className="cursor-pointer aspect-square flex flex-col items-center justify-center gap-0.5 font-mono text-[11px] border-2 active:scale-[0.9]"
              style={{
                borderColor: isSelected ? '#0a0a0a' : isToday ? '#ff2e00' : 'transparent',
                background: isSelected ? '#0a0a0a' : '#ffffff',
                color: isSelected ? '#ffffff' : '#0a0a0a',
              }}
            >
              {d.getDate()}
              <span style={{ width: dotSize, height: dotSize, background: dotColor, flexShrink: 0 }} />
            </button>
          )
        })}
      </div>
    </div>
  )
}

function RecapCard({ recap, onOpen }) {
  const color = SOURCE_COLOR[displaySource(recap.source)] || '#0a0a0a'
  return (
    <button
      type="button"
      onClick={onOpen}
      className="cursor-pointer w-full text-left bg-transparent border-none flex items-center justify-between gap-4 px-5 py-4 border-t-[3px] border-ink first:border-t-0 hover:bg-accent hover:text-white transition-none active:scale-[0.99]"
    >
      <div className="flex items-center gap-4 min-w-0">
        <span className="shrink-0 w-3.5 h-3.5 border-[3px] border-ink" style={{ background: color }} />
        <div className="min-w-0">
          <div className="font-body font-extrabold text-[17px] truncate">{recap.name}</div>
          <div className="font-mono text-xs text-muted">
            {SOURCE_LABEL[displaySource(recap.source)] || recap.source} · {formatDate(recap.created_at)}
            {recap.speaker_count ? ` · ${recap.speaker_count} participant${recap.speaker_count > 1 ? 's' : ''}` : ''}
          </div>
          {recap.summary && (
            <div className="font-mono text-xs mt-1.5 line-clamp-1 opacity-80">{recap.summary}</div>
          )}
        </div>
      </div>
      <div className="font-mono text-xs uppercase border-[3px] border-ink px-2.5 py-1 shrink-0">Ouvrir →</div>
    </button>
  )
}

function RecapListSkeleton() {
  return (
    <div className="border-4 border-ink">
      {[0, 1, 2].map(i => (
        <div key={i} className="px-5 py-4 border-t-[3px] border-ink first:border-t-0 flex flex-col gap-2">
          <div className="h-3 w-2/5 bg-black/10 animate-pulse" />
          <div className="h-3 w-1/4 bg-black/10 animate-pulse" />
        </div>
      ))}
    </div>
  )
}

function UpcomingCard({ event }) {
  const color = event.will_record ? '#1a56ff' : '#0a0a0a'
  const attendeeCount = event.attendees?.length || 0
  const inner = (
    <>
      <div className="flex items-center gap-4 min-w-0">
        <span
          className="shrink-0 w-3.5 h-3.5 border-[3px] border-ink rounded-full"
          style={{ background: event.will_record ? color : '#ffffff' }}
        />
        <div className="min-w-0">
          <div className="font-body font-extrabold text-[17px] truncate">{event.title}</div>
          <div className="font-mono text-xs text-muted">
            {formatDateTime(event.start)}
            {attendeeCount ? ` · ${attendeeCount} participant${attendeeCount > 1 ? 's' : ''}` : ''}
          </div>
          {event.will_record && (
            <div
              className="font-mono text-[10px] uppercase tracking-[1px] border-2 px-1.5 py-0.5 mt-1.5 inline-block"
              style={{ borderColor: color, color }}
            >
              Sera enregistrée
            </div>
          )}
        </div>
      </div>
      {event.meeting_url && (
        <div className="font-mono text-xs uppercase border-[3px] border-ink px-2.5 py-1 shrink-0">Rejoindre →</div>
      )}
    </>
  )
  const cls =
    'w-full text-left flex items-center justify-between gap-4 px-5 py-4 border-t-[3px] border-ink first:border-t-0'
  return event.meeting_url ? (
    <a href={event.meeting_url} target="_blank" rel="noreferrer" className={`${cls} hover:bg-accent hover:text-white transition-none`}>
      {inner}
    </a>
  ) : (
    <div className={cls}>{inner}</div>
  )
}

function UpcomingSection({ events, connected, search }) {
  if (events === null) return <RecapListSkeleton />

  if (!connected) {
    return (
      <div className="border-4 border-dashed border-ink px-5 py-6 font-mono text-xs text-muted">
        Connecte ton agenda Google dans les réglages pour voir les réunions à venir.
      </div>
    )
  }

  const query = search.trim().toLowerCase()
  const list = query ? events.filter(e => (e.title || '').toLowerCase().includes(query)) : events

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="font-mono text-[11px] uppercase tracking-[1px] text-muted">À venir</div>
        <div className="font-mono text-[11px] text-muted">{list.length}</div>
      </div>
      {list.length > 0 ? (
        <div className="border-4 border-ink">
          {list.map(e => (
            <UpcomingCard key={e.id} event={e} />
          ))}
        </div>
      ) : (
        <div className="border-4 border-ink px-5 py-6 text-center font-mono text-xs text-muted">
          Aucune réunion planifiée.
        </div>
      )}
    </div>
  )
}

export default function Recap() {
  const { token, user } = useAuth()
  const navigate = useNavigate()

  const [recaps, setRecaps] = useState(null)
  const [events, setEvents] = useState(null)
  const [eventsConnected, setEventsConnected] = useState(false)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [selectedDay, setSelectedDay] = useState(null)

  useEffect(() => {
    let cancelled = false

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setRecaps(null)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setEvents(null)
    setError(null)
    getMyRecaps(token)
      .then(data => { if (!cancelled) setRecaps(data) })
      .catch(err => { if (!cancelled) setError(err.message) })

    getCalendarEvents(token)
      .then(data => {
        if (cancelled) return
        setEvents(data.events || [])
        setEventsConnected(Boolean(data.connected))
      })
      .catch(() => {
        if (cancelled) return
        setEvents([])
        setEventsConnected(false)
      })

    return () => {
      cancelled = true
    }
  }, [token])

  const dayStats = useMemo(() => {
    const map = new Map()
    for (const r of recaps ?? []) {
      if (!r.created_at) continue
      const key = r.created_at.slice(0, 10)
      const entry = map.get(key) ?? { count: 0, sources: new Set() }
      entry.count += 1
      entry.sources.add(displaySource(r.source))
      map.set(key, entry)
    }
    return map
  }, [recaps])

  const { monthCount, yearCount } = useMemo(() => {
    const now = new Date()
    let month = 0
    let year = 0
    for (const r of recaps ?? []) {
      if (!r.created_at) continue
      const d = new Date(r.created_at)
      if (d.getFullYear() === now.getFullYear()) {
        year += 1
        if (d.getMonth() === now.getMonth()) month += 1
      }
    }
    return { monthCount: month, yearCount: year }
  }, [recaps])

  const filtered = (recaps ?? []).filter(r => {
    if (sourceFilter !== 'all' && displaySource(r.source) !== sourceFilter) return false
    if (selectedDay) {
      if (r.created_at?.slice(0, 10) !== selectedDay) return false
    }
    if (search.trim()) {
      const haystack = [r.name, r.summary].filter(Boolean).join(' ').toLowerCase()
      if (!haystack.includes(search.trim().toLowerCase())) return false
    }
    return true
  })

  return (
    <AppShell>
      <div className="p-6 md:p-10 max-w-[1240px]">
        <h2 className="font-display text-[40px] uppercase tracking-[-2px] m-0 mb-1.5 leading-none">
          Récaps
        </h2>
        <p className="font-mono text-[13px] text-muted mb-6">
          {user?.username ? `Bonjour ${user.username}, voici` : 'Voici'} les récaps de vos réunions.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-8 items-start">
          <div className="flex flex-col gap-7">
            <div className="flex gap-4 flex-wrap">
              <StatTile label="Ce mois-ci" value={monthCount} color="#ff2e00" />
              <StatTile label="Cette année" value={yearCount} color="#1a56ff" />
            </div>

            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 font-display text-xl pointer-events-none text-muted">⌕</span>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Rechercher un mot-clé…"
                className="block w-full pl-12 pr-4 py-4 font-mono text-base bg-paper border-4 border-ink shadow-[6px_6px_0_#ff2e00] focus:shadow-[2px_2px_0_#ff2e00] focus:translate-x-1 focus:translate-y-1 transition-none"
              />
            </div>

            <div className="border-4 border-ink p-5 flex flex-col gap-4">
              <div className="flex gap-2 flex-wrap">
                {SOURCES.map(s => (
                  <Chip key={s.value} active={sourceFilter === s.value} color={s.color} onClick={() => setSourceFilter(s.value)}>
                    {s.icon ? `${s.icon} ` : ''}{s.label}
                  </Chip>
                ))}
              </div>

              <Calendar dayStats={dayStats} selected={selectedDay} onSelect={setSelectedDay} />

              {selectedDay && (
                <div className="flex items-center gap-2 font-mono text-xs flex-wrap">
                  <span className="border-4 border-ink px-2.5 py-1.5">
                    {new Date(selectedDay).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })}
                  </span>
                  <button
                    onClick={() => setSelectedDay(null)}
                    className="cursor-pointer font-mono text-[11px] uppercase underline bg-transparent border-none p-0"
                  >
                    Réinitialiser
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-8">
            <UpcomingSection events={events} connected={eventsConnected} search={search} />

            <div>
              <div className="font-mono text-[11px] uppercase tracking-[1px] text-muted mb-2">Passées</div>
              {error ? (
                <div className="border-4 border-ink px-6 py-10 text-center font-mono text-sm">
                  Impossible de charger les récaps.
                </div>
              ) : recaps === null ? (
                <RecapListSkeleton />
              ) : filtered.length > 0 ? (
                <div className="border-4 border-ink">
                  {filtered.map(r => (
                    <RecapCard key={r.id} recap={r} onOpen={() => navigate(`/recap/${r.id}`)} />
                  ))}
                </div>
              ) : (
                <div className="border-4 border-ink px-6 py-10 text-center font-mono text-sm text-muted">
                  Aucun compte-rendu pour le moment.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
