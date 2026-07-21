import { Routes, Route } from "react-router"
import Auth from "./pages/Auth"
import Consent from "./pages/Consent"
import Home from "./pages/Home"
import Record from "./pages/Record"
import Recap from "./pages/Recap"
import Settings from "./pages/Settings"
import Dashboard from "./pages/Dashboard"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Auth />} />
      <Route path="/consent" element={<Consent />} />
      <Route path="/home" element={<Home />} />
      <Route path="/record" element={<Record />} />
      <Route path="/recap" element={<Recap />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/ dashboard" element={<Dashboard />} />
    </Routes>
  )
}
