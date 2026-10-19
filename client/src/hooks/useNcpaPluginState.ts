import { useEffect, useState } from 'react'
import { getPluginInventory } from '../lib/pluginApi'

export type NcpaPluginState = 'unknown' | 'enabled' | 'not-enabled'

// Whether check_ncpa is on in Plugin Manager. NCPA checks are only monitored while it is
// enabled, so the deployment page warns when it is not. Any failure (including a user
// without plugin.view) leaves the state "unknown", which shows no warning.
// Refresh on mount and when returning to the window/tab; only the latest request wins.
export function useNcpaPluginState(): NcpaPluginState {
  const [state, setState] = useState<NcpaPluginState>('unknown')

  useEffect(() => {
    let active = true
    let latestRequest = 0

    const refresh = () => {
      const request = ++latestRequest
      getPluginInventory({ search: 'check_ncpa', per_page: 10, sort_by: 'name', order: 'asc' })
        .then((data) => {
          if (!active || request !== latestRequest) return
          // Match the backend registry's supported filename normalization.
          const enabled = data.items.some((item) =>
            /^check_ncpa(?:\.(?:py|pl|sh))?$/.test(item.name.trim().toLowerCase())
            && (item.status === 'Enabled' || item.status === 'Active'),
          )
          setState(enabled ? 'enabled' : 'not-enabled')
        })
        .catch(() => {
          if (active && request === latestRequest) setState('unknown')
        })
    }
    const refreshWhenVisible = () => {
      if (document.visibilityState === 'visible') refresh()
    }

    refresh()
    window.addEventListener('focus', refresh)
    document.addEventListener('visibilitychange', refreshWhenVisible)
    return () => {
      active = false
      window.removeEventListener('focus', refresh)
      document.removeEventListener('visibilitychange', refreshWhenVisible)
    }
  }, [])

  return state
}
