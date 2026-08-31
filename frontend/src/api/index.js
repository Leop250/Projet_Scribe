function normalizeBaseUrl(url) {
  if (!url) return 'http://localhost:8000'
  return /^https?:\/\//i.test(url) ? url : `https://${url}`
}

const BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_URL)

function extractErrorMessage(data, fallback) {
  if (typeof data?.detail === 'string') return data.detail
  if (Array.isArray(data?.detail)) {
    return data.detail.map(e => e.msg || JSON.stringify(e)).join(' ')
  }
  return fallback
}

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

export async function uploadRecording(blob, token, emails, name) {
  const body = new FormData()
  body.append('audio', blob, 'recording.webm')
  body.append('emails', emails)
  body.append('name', name)

  const data = await requestJson(
    `${BASE_URL}/recordings`,
    { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body },
    'Envoi échoué',
  )
  return data['Compte-rendu']
}

export async function getRecap(id, token) {
  return requestJson(
    `${BASE_URL}/recaps/${id}`,
    { headers: { Authorization: `Bearer ${token}` } },
    'Compte-rendu introuvable',
  )
}

export async function getMyRecaps(token) {
  return requestJson(
    `${BASE_URL}/recaps/mine`,
    { headers: { Authorization: `Bearer ${token}` } },
    'Impossible de charger les récaps',
  )
}

export async function login(email, password) {
  const body = new URLSearchParams()
  body.append('username', email)
  body.append('password', password)

  const data = await requestJson(
    `${BASE_URL}/token`,
    { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body },
    'Connexion refusée',
  )
  return data
}

export async function getSession(token) {
  return requestJson(`${BASE_URL}/auth/session`, { headers: { Authorization: `Bearer ${token}` } }, 'Non authentifié')
}

export async function checkEmailExists(email) {
  const data = await requestJson(`${BASE_URL}/users/exists?email=${encodeURIComponent(email)}`, {}, 'Vérification impossible')
  return data.exists
}

export async function registerUser({ username, email, password, acceptedGuidelines }) {
  return requestJson(
    `${BASE_URL}/users/createUsers`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, accepted_guidelines: acceptedGuidelines }),
    },
    'Inscription refusée',
  )
}

export async function verifyCode(email, code) {
  const data = await requestJson(
    `${BASE_URL}/auth/verify-code`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, code }) },
    'Vérification refusée',
  )
  return data
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
  return data
}

export async function getGoogleIntegrationStatus(token) {
  return requestJson(
    `${BASE_URL}/calendar/status`,
    { headers: { Authorization: `Bearer ${token}` } },
    'Statut Google Calendar indisponible',
  )
}

export async function getGoogleAuthorizeUrl(token) {
  const data = await requestJson(
    `${BASE_URL}/calendar/oauth/authorize`,
    { headers: { Authorization: `Bearer ${token}` } },
    'Autorisation Google indisponible',
  )
  return data.authorize_url
}

export async function disconnectGoogleIntegration(token) {
  return requestJson(
    `${BASE_URL}/calendar`,
    { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } },
    'Déconnexion refusée',
  )
}
