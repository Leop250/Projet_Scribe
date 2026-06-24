export default function Logo({ size = 26 }) {
  return (
    <div style={{ position: 'relative', width: size + 18, height: size + 10 }}>
      <div style={{
        position: 'absolute', top: 0, left: 0,
        width: size, height: size, borderRadius: 8,
        backgroundColor: '#f87171',
      }} />
      <div style={{
        position: 'absolute', top: size * 0.38, left: size * 0.38,
        width: size, height: size, borderRadius: 8,
        backgroundColor: '#ef4444',
      }} />
    </div>
  )
}
