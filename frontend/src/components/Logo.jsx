export default function Logo({ size = 26 }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className="text-ink uppercase"
        style={{ fontFamily: "'Playfair Display', serif", fontWeight: 900, fontSize: size, letterSpacing: '-1px' }}
      >
        Scribe
      </span>
      <span className="w-3 h-3 bg-accent border-2 border-ink shrink-0" />
    </span>
  )
}
