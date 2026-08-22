import { createContext, useContext, useEffect, useState } from 'react'
import { getSession } from '../api'

const AuthContext = createContext(null)
const STORAGE_KEY = 'scribe_token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState(null)

  useEffect(() => {
    if (token) localStorage.setItem(STORAGE_KEY, token)
    else localStorage.removeItem(STORAGE_KEY)
  }, [token])

  useEffect(() => {
    // Se déclenche à chaque changement de token (login, ou restauration
    // depuis localStorage au démarrage) : un token périmé pendant que l'app
    // était fermée déclenche un vrai 401 ici plutôt que de laisser
    // l'utilisateur le découvrir au milieu d'une action (upload, etc.), et
    // ça peuple `user` au passage. Seul un vrai 401 doit déconnecter : une
    // panne réseau ou un backend momentanément indisponible ne veut pas dire
    // que le token est invalide.
    if (!token) { setUser(null); return }
    getSession(token)
      .then(setUser)
      .catch(err => { if (err.status === 401) setToken(null) })
  }, [token])

  function logout() {
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ token, setToken, user, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
