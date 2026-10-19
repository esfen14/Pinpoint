import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { ApiError, apiGet } from '../../lib/api'
import { firstAccessiblePage } from '../../lib/pageAccess'
import { LoginPage } from '../../pages/LoginPage'

type SessionState =
  | { kind: 'checking' | 'signed-out' | 'error' }
  | { kind: 'signed-in'; landing: string }

// Check the server session before offering credentials, including on direct URLs.
export function LoginRoute() {
  const [session, setSession] = useState<SessionState>({ kind: 'checking' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    apiGet<{ permissions: string[] }>('/api/user/me')
      .then((user) => {
        if (!Array.isArray(user.permissions)) throw new Error('Invalid session response')
        if (!cancelled) {
          setSession({ kind: 'signed-in', landing: firstAccessiblePage(user.permissions) })
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setSession({ kind: error instanceof ApiError && error.status === 401 ? 'signed-out' : 'error' })
        }
      })
    return () => { cancelled = true }
  }, [attempt])

  if (session.kind === 'signed-in') return <Navigate to={session.landing} replace />
  if (session.kind === 'signed-out') return <LoginPage />

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      {session.kind === 'checking' ? (
        <p role="status">Checking your session...</p>
      ) : (
        <>
          <p role="alert">Unable to check your session. Please try again.</p>
          <button type="button" onClick={() => {
            setSession({ kind: 'checking' })
            setAttempt((current) => current + 1)
          }}>Try again</button>
        </>
      )}
    </main>
  )
}
