import { Routes, Route } from "react-router"
import Landing from "./pages/Landing"
import Auth from "./pages/Auth"
import Token from "./pages/Token"
import Consent from "./pages/Consent"
import Home from "./pages/Home"
import Record from "./pages/Record"
import Recap from "./pages/Recap"
import Settings from "./pages/Settings"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Auth />} />
      <Route path="/token" element={<Token />} />
      <Route path="/consent" element={<Consent />} />
      <Route path="/home" element={<Home />} />
      <Route path="/record" element={<Record />} />
      <Route path="/recap" element={<Recap />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  )
}
