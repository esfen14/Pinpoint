import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import { reportUnauthorized } from '../lib/api'

// The signed-in user and their role's permissions, from /api/user/me.
// Loaded once by AdminLayout, then checked every 10 seconds while the tab is
// visible and whenever it regains focus. So an admin's changes show without a
// refresh, and a session the back end ended goes to the login page on its own.

export type CurrentUser = {
  firstName: string
  lastName: string
  email: string
  role: string
  permissions: string[]
  mustChangePassword: boolean
  needsSetup: boolean
}

type CurrentUserContextValue = {
  user: CurrentUser | null
  isLoading: boolean
  hasPermission: (permission: string) => boolean
  reload: () => void
}

const SESSION_CHECK_INTERVAL_MS = 10_000

// Keeps the same object when nothing changed, so a check doesn't re-render
// pages or restart their effects.
function keepIfUnchanged(previous: CurrentUser | null, loaded: CurrentUser) {
  return JSON.stringify(previous) === JSON.stringify(loaded) ? previous : loaded
}

const CurrentUserContext = createContext<CurrentUserContextValue | undefined>(undefined)

async function fetchCurrentUser(): Promise<CurrentUser> {
  const res = await fetch('/api/user/me', { credentials: 'include' })
  if (res.status === 401) {
    reportUnauthorized()
  }
  if (!res.ok) {
    throw new Error(`Unable to load current user (${res.status})`)
  }

  const body = await res.json()
  const data = body.data ?? body

  return {
    firstName: data.first_name,
    lastName: data.last_name,
    email: data.email,
    role: data.role,
    permissions: Array.isArray(data.permissions) ? data.permissions : [],
    mustChangePassword: data.must_change_password === true,
    needsSetup: data.needs_setup === true,
  }
}

export function CurrentUserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    const loadUser = () => {
      fetchCurrentUser()
        .then((loaded) => {
          if (!cancelled) setUser((previous) => keepIfUnchanged(previous, loaded))
        })
        .catch((error) => {
          // A 401 is handled by SessionTimeoutWatcher, which sends the user to login.
          console.error('Unable to load current user:', error)
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false)
        })
    }

    const handleVisible = () => {
      if (document.visibilityState === 'visible') {
        loadUser()
      }
    }

    loadUser()
    document.addEventListener('visibilitychange', handleVisible)
    window.addEventListener('focus', handleVisible)

    return () => {
      cancelled = true
      document.removeEventListener('visibilitychange', handleVisible)
      window.removeEventListener('focus', handleVisible)
    }
  }, [])

  // First-run setup and the forced password change replace the session's sign-in
  // details. A check sent while that request is still running would carry the
  // old session and be refused, so checks wait until the account is unblocked.
  const isBlocked = Boolean(user?.needsSetup || user?.mustChangePassword)

  useEffect(() => {
    if (isBlocked) return

    const checkSession = () => {
      if (document.visibilityState !== 'visible') return

      fetchCurrentUser()
        .then((loaded) => setUser((previous) => keepIfUnchanged(previous, loaded)))
        .catch((error) => console.error('Unable to load current user:', error))
    }

    const intervalId = window.setInterval(checkSession, SESSION_CHECK_INTERVAL_MS)
    return () => window.clearInterval(intervalId)
  }, [isBlocked])

  const reload = useCallback(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch((error) => console.error('Unable to load current user:', error))
  }, [])

  const hasPermission = useCallback(
    (permission: string) => user?.permissions.includes(permission) ?? false,
    [user]
  )

  return (
    <CurrentUserContext.Provider value={{ user, isLoading, hasPermission, reload }}>
      {children}
    </CurrentUserContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCurrentUser() {
  const context = useContext(CurrentUserContext)
  if (!context) {
    throw new Error('useCurrentUser must be used inside CurrentUserProvider')
  }
  return context
}
