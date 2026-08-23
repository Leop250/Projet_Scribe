import { Routes, Route } from "react-router"
import Landing from "./pages/Landing"
import Auth from "./pages/Auth"
import Consent from "./pages/Consent"
import Home from "./pages/Home"
import Attendance from "./pages/Attendance"
import Sign from "./pages/Sign"
import Confidentialite from "./pages/Confidentialite"
import Record from "./pages/Record"
import Recap from "./pages/Recap"
import RecapDetail from "./pages/RecapDetail"
import Settings from "./pages/Settings"
import NotFound from "./pages/NotFound"
import RequireAuth from "./components/RequireAuth"


export default function App() {
  return (
    <>
      <a
        href="#main-content"
        className="absolute left-2 -top-16 focus:top-2 z-[100] bg-ink text-white font-mono text-xs uppercase tracking-[1px] px-4 py-2.5 border-4 border-ink transition-none"
      >
        Aller au contenu
      </a>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Auth />} />
        <Route path="/consent" element={<RequireAuth><Consent /></RequireAuth>} />
        <Route path="/home" element={<RequireAuth><Home /></RequireAuth>} />
        <Route path="/attendance" element={<RequireAuth><Attendance /></RequireAuth>} />
        <Route path="/sign/:sessionToken" element={<Sign />} />
        <Route path="/confidentialite" element={<Confidentialite />} />
        <Route path="/record" element={<RequireAuth><Record /></RequireAuth>} />
        <Route path="/recap" element={<RequireAuth><Recap /></RequireAuth>} />
        <Route path="/recap/:id" element={<RequireAuth><RecapDetail /></RequireAuth>} />
        <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  )
}
