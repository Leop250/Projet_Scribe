import { createContext, useContext, useEffect, useState } from 'react'
import { getSession } from '../api'

const AuthContext = createContext(null)
const STORAGE_KEY = 'scribe_token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState(null)
  const [sessionError, setSessionError] = useState(false)

  useEffect(() => {
    if (token) localStorage.setItem(STORAGE_KEY, token)
    else localStorage.removeItem(STORAGE_KEY)
  }, [token])

  useEffect(() => {
    if (!token) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSessionError(false)
    getSession(token)
      .then(setUser)
      .catch(err => {
        if (err.status === 401) { setToken(null); setUser(null) }
        else setSessionError(true)
      })
  }, [token])

  function logout() {
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, setToken, user, logout, isAuthenticated: !!token, sessionError }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
