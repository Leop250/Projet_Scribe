const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function uploadRecording(blob) {
  const body = new FormData()
  body.append('audio', blob, 'recording.flac')

  const res = await fetch(`${BASE_URL}/recordings`, {
    method: 'POST',
    body,
  })

  if (!res.ok) throw new Error(`Upload failed (${res.status})`)
  const data = await res.json()
  return data['Compte-rendu']
}

export async function getRecap(id) {
  const res = await fetch(`${BASE_URL}/recaps/${id}`)

  if (!res.ok) throw new Error(`Fetch recap failed (${res.status})`)
  return res.json()
}
