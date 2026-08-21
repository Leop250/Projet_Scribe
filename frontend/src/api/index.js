function normalizeBaseUrl(url) {
  if (!url) return 'http://localhost:8000'
  return /^https?:\/\//i.test(url) ? url : `https://${url}`
}

const BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_URL)

// FastAPI renvoie `detail` en string pour une erreur métier (HTTPException),
// mais en liste d'objets {msg, loc, ...} pour une erreur de validation
// Pydantic (422) — sans ça, un message d'erreur de validation s'affiche
// comme "[object Object]" dans l'UI.
function extractErrorMessage(data, fallback) {
  if (typeof data?.detail === 'string') return data.detail
  if (Array.isArray(data?.detail)) {
    return data.detail.map(e => e.msg || JSON.stringify(e)).join(' ')
  }
  return fallback
}

// Centralise fetch + parsing JSON + gestion d'erreur pour les routes auth :
// chaque appelant peut compter sur `err.status` pour distinguer les cas
// (403 non vérifié, 429 rate limit, 409 conflit...) plutôt que de parser
// le message d'erreur.
async function requestJson(url, options, fallbackMessage) {
  const res = await fetch(url, options)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(extractErrorMessage(data, `${fallbackMessage} (${res.status})`))
    err.status = res.status
    throw err
  }
  return data
}

export async function uploadRecording(blob, token, sessionToken, emails) {
  const body = new FormData()
  body.append('audio', blob, 'recording.webm')
  body.append('emails', emails)
  if (sessionToken) body.append('session_token', sessionToken)

  const res = await fetch(`${BASE_URL}/recordings`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
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

// -- Auth (OAuth2 Password Grant + Bearer JWT) --
// POST /token attend un formulaire OAuth2 classique (champ "username", pas "email").
export async function login(email, password) {
  const body = new URLSearchParams()
  body.append('username', email)
  body.append('password', password)

  const data = await requestJson(
    `${BASE_URL}/token`,
    { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body },
    'Connexion refusée',
  )
  return data // { access_token, token_type }
}

export async function getSession(token) {
  return requestJson(`${BASE_URL}/auth/session`, { headers: { Authorization: `Bearer ${token}` } }, 'Non authentifié')
  // { id, username, email, is_verified }
}

export async function checkEmailExists(email) {
  const data = await requestJson(`${BASE_URL}/users/exists?email=${encodeURIComponent(email)}`, {}, 'Vérification impossible')
  return data.exists
}

export async function registerUser({ username, email, password }) {
  return requestJson(
    `${BASE_URL}/users/createUsers`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, email, password }) },
    'Inscription refusée',
  )
}

export async function verifyCode(email, code) {
  const data = await requestJson(
    `${BASE_URL}/auth/verify-code`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, code }) },
    'Vérification refusée',
  )
  return data // { access_token, token_type }
}

export async function resendCode(email) {
  return requestJson(
    `${BASE_URL}/auth/resend-code`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) },
    'Renvoi refusé',
  )
}

export async function forgotPassword(email) {
  return requestJson(
    `${BASE_URL}/auth/forgot-password`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) },
    'Demande refusée',
  )
}

export async function resetPassword(email, code, newPassword) {
  const data = await requestJson(
    `${BASE_URL}/auth/reset-password`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, code, new_password: newPassword }) },
    'Réinitialisation refusée',
  )
  return data // { access_token, token_type }
}

// -- Présence par QR code --
export async function createAttendanceSession(headcount, token) {
  return requestJson(
    `${BASE_URL}/attendance/sessions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ headcount }),
    },
    'Création de la session impossible',
  )
  // { session_token, sign_url, headcount }
}

export async function getAttendanceSessionStatus(sessionToken, token) {
  return requestJson(
    `${BASE_URL}/attendance/sessions/${sessionToken}`,
    { headers: { Authorization: `Bearer ${token}` } },
    'Statut indisponible',
  )
  // { headcount, confirmed_count, ready }
}

export async function startAttendanceSession(sessionToken, token) {
  return requestJson(
    `${BASE_URL}/attendance/sessions/${sessionToken}/start`,
    { method: 'POST', headers: { Authorization: `Bearer ${token}` } },
    "Démarrage refusé",
  )
}

export async function getPublicAttendanceSession(sessionToken) {
  return requestJson(
    `${BASE_URL}/attendance/sessions/${sessionToken}/public`,
    {},
    'Session introuvable',
  )
  // { headcount, confirmed_count, status }
}

export async function signAttendance(sessionToken, nom, image) {
  return requestJson(
    `${BASE_URL}/attendance/sessions/${sessionToken}/sign`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nom, image }) },
    'Signature refusée',
  )
}
