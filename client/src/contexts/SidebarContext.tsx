import { createContext, useContext, useState, type ReactNode } from 'react'

// Whether the sidebar is shown. Shared by the header's toggle button, the
// sidebar and the layout that leaves room for it. Starts shown on each load.

type SidebarContextValue = {
  isSidebarOpen: boolean
  toggleSidebar: () => void
}

const SidebarContext = createContext<SidebarContextValue | undefined>(undefined)

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const toggleSidebar = () => setIsSidebarOpen((open) => !open)

  return (
    <SidebarContext.Provider value={{ isSidebarOpen, toggleSidebar }}>
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebar() {
  const context = useContext(SidebarContext)
  if (!context) {
    throw new Error('useSidebar must be used inside SidebarProvider')
  }
  return context
}
