import { Navigate } from 'react-router'
import { useAuth } from '../context/AuthContext'

export default function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/" replace />
}
