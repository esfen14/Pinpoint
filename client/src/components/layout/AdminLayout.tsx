import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { SessionTimeoutWatcher } from './SessionTimeoutWatcher'
import { MaintenanceBanner } from './MaintenanceBanner'
import { PageAccessGuard } from './PageAccessGuard'
import { SystemSettingsProvider } from '../../contexts/SystemSettingsContext'
import { CurrentUserProvider, useCurrentUser } from '../../contexts/CurrentUserContext'
import { SidebarProvider, useSidebar } from '../../contexts/SidebarContext'
import { ForcePasswordChange } from './ForcePasswordChange'
import { FirstRunSetup } from './FirstRunSetup'

function LayoutBody() {
  const { user } = useCurrentUser()
  const { isSidebarOpen } = useSidebar()

  if (user?.needsSetup) {
    return (
      <>
        <SessionTimeoutWatcher />
        <FirstRunSetup />
      </>
    )
  }

  if (user?.mustChangePassword) {
    return (
      <>
        <SessionTimeoutWatcher />
        <ForcePasswordChange />
      </>
    )
  }

  return (
    <>
      <SessionTimeoutWatcher />
      <div className="admin-bg flex min-h-screen">
        {isSidebarOpen && <Sidebar />}

        {/* The sidebar is fixed, so this column alone leaves room for it. */}
        <main className={`admin-bg flex min-h-screen flex-1 flex-col min-w-0 ${isSidebarOpen ? 'ml-55' : ''}`}>
          <Header />

          <div className="flex-1 overflow-x-auto overflow-y-auto px-4 pb-8 min-w-0">
            <MaintenanceBanner />
            <PageAccessGuard>
              <Outlet />
            </PageAccessGuard>
          </div>
        </main>
      </div>
    </>
  )
}

export function AdminLayout() {
  return (
    <CurrentUserProvider>
      <SystemSettingsProvider>
        <SidebarProvider>
          <LayoutBody />
        </SidebarProvider>
      </SystemSettingsProvider>
    </CurrentUserProvider>
  )
}
