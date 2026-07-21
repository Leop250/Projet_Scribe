import { useNavigate } from 'react-router'
import AppShell from '../components/AppShell'

export default function Dashboard() {
  const navigate = useNavigate()

  return (
    <AppShell />
  )
}
