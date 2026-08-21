import { Routes, Route } from "react-router"
import Auth from "./pages/Auth"
import Consent from "./pages/Consent"
import Home from "./pages/Home"
import Attendance from "./pages/Attendance"
import Sign from "./pages/Sign"
import Confidentialite from "./pages/Confidentialite"
import Record from "./pages/Record"
import Recap from "./pages/Recap"
import Settings from "./pages/Settings"
import Dashboard from "./pages/Dashboard"
import RequireAuth from "./components/RequireAuth"


export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Auth />} />
      <Route path="/consent" element={<RequireAuth><Consent /></RequireAuth>} />
      <Route path="/home" element={<RequireAuth><Home /></RequireAuth>} />
      <Route path="/attendance" element={<RequireAuth><Attendance /></RequireAuth>} />
      <Route path="/sign/:sessionToken" element={<Sign />} />
      <Route path="/confidentialite" element={<Confidentialite />} />
      <Route path="/record" element={<RequireAuth><Record /></RequireAuth>} />
      <Route path="/recap" element={<RequireAuth><Recap /></RequireAuth>} />
      <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
      <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
    </Routes>
  )
}
