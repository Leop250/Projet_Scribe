const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/**
 * POST /recordings
 * Upload an audio blob recorded via MediaRecorder.
 * Returns the recap object created by the backend.
 */
export async function uploadRecording(blob) {
  const body = new FormData()
  body.append('audio', blob, 'recording.webm')

  const res = await fetch(`${BASE_URL}/recordings`, {
    method: 'POST',
    body,
  })

  if (!res.ok) throw new Error(`Upload failed (${res.status})`)
  return res.json()
}

/**
 * GET /recaps/:id
 * Fetch a single recap by ID.
 */
export async function getRecap(id) {
  const res = await fetch(`${BASE_URL}/recaps/${id}`)

  if (!res.ok) throw new Error(`Fetch recap failed (${res.status})`)
  return res.json()
}
