import Sidebar from './Sidebar'
import BottomNav from './BottomNav'

export default function AppShell({ children }) {
  return (
    <div className="flex min-h-[100dvh] bg-paper text-ink">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <main id="main-content" tabIndex={-1} className="flex-1 pb-16 md:pb-0">
          {children}
        </main>

        <div className="md:hidden fixed bottom-0 left-0 right-0">
          <BottomNav />
        </div>
      </div>
    </div>
  )
}
