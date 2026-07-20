import { createContext, useContext, useState } from 'react'

const RecapContext = createContext(null)

export function RecapProvider({ children }) {
  const [recap, setRecap] = useState(null)
  return (
    <RecapContext.Provider value={{ recap, setRecap }}>
      {children}
    </RecapContext.Provider>
  )
}

export function useRecap() {
  return useContext(RecapContext)
}
