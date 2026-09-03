import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter } from "react-router"
import { RecapProvider } from "./context/RecapContext"
import { AuthProvider } from "./context/AuthContext"
import App from "./App"
import "./index.css"

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <RecapProvider>
          <App />
        </RecapProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
)
