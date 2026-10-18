import { useEffect, useState } from 'react'
import { useCurrentUser } from '../contexts/CurrentUserContext'
import { apiGet } from '../lib/api'
import type { LastRun } from '../types/remediation'

// Runs only change when a failure happens, so a slow refresh is enough.
const REFRESH_MS = 60 * 1000

/**
 * The newest automatic-recovery run for each service, for the badge on a service row. Only asks
 * the server when the user may view remediation; returns null until loaded, without the permission,
 * or when a request fails (the badge is a hint, so it never shows an error on the page).
 */
export function useLastRecoveries(): LastRun[] | null {
  const { hasPermission } = useCurrentUser()
  const allowed = hasPermission('remediation.view')
  const [runs, setRuns] = useState<LastRun[] | null>(null)

  useEffect(() => {
    if (!allowed) return
    let active = true
    async function load() {
      try {
        const data = await apiGet<{ items: LastRun[] }>('/api/system/remediation/last-runs')
        if (active) setRuns(data.items)
      } catch {
        // Keep whatever was loaded before.
      }
    }
    load()
    const id = window.setInterval(load, REFRESH_MS)
    return () => {
      active = false
      window.clearInterval(id)
    }
  }, [allowed])

  return allowed ? runs : null
}
