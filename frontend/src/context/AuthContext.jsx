import { createContext, useContext, useEffect, useState } from 'react'
import { getSession } from '../api'

const AuthContext = createContext(null)
const STORAGE_KEY = 'scribe_token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY))

  useEffect(() => {
    if (token) localStorage.setItem(STORAGE_KEY, token)
    else localStorage.removeItem(STORAGE_KEY)
  }, [token])

  useEffect(() => {
    // Un token en localStorage peut avoir expiré pendant que l'app était
    // fermée — on le vérifie une fois au démarrage plutôt que de laisser
    // l'utilisateur découvrir ça au milieu d'une action (upload, etc.).
    // Seul un vrai 401 doit déconnecter : une panne réseau ou un backend
    // momentanément indisponible ne veut pas dire que le token est invalide.
    if (!token) return
    getSession(token).catch(err => { if (err.status === 401) setToken(null) })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function logout() {
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ token, setToken, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
