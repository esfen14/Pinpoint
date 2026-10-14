import { useEffect, useState } from 'react'

import { ApiError, apiPost, errorMessage } from '../../lib/api'
import { useCurrentUser } from '../../contexts/CurrentUserContext'

type Props = {
  hostname: string
  // Omit for a host.
  service?: string
  // Called after Nagios accepted the request, so the view can reload later.
  onRequested?: () => void
}

function recheckPath(hostname: string, service?: string) {
  const host = encodeURIComponent(hostname)
  if (!service) return `/api/system/network-health/hosts/${host}/recheck`
  return `/api/system/network-health/services/${host}/${service.split('/').map(encodeURIComponent).join('/')}/recheck`
}

// Asks Nagios to re-check a host or service now. Hidden without system.recheck; the server
// enforces the permission and a 10 second limit per target.
export function CheckNowButton({ hostname, service, onRequested }: Props) {
  const { hasPermission } = useCurrentUser()
  const [isSending, setIsSending] = useState(false)
  const [cooldown, setCooldown] = useState(0)
  const [message, setMessage] = useState<{ text: string; isError: boolean } | null>(null)

  useEffect(() => {
    setCooldown(0)
    setMessage(null)
  }, [hostname, service])

  useEffect(() => {
    if (cooldown <= 0) return
    const id = window.setTimeout(() => setCooldown((s) => s - 1), 1000)
    return () => window.clearTimeout(id)
  }, [cooldown])

  if (!hasPermission('system.recheck')) return null

  async function checkNow() {
    setIsSending(true)
    setMessage(null)
    try {
      await apiPost(recheckPath(hostname, service))
      setCooldown(10)
      setMessage({ text: 'Check requested. The result appears after the next refresh.', isError: false })
      onRequested?.()
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        const wait = (err.data as { retry_after?: number } | undefined)?.retry_after
        setCooldown(typeof wait === 'number' ? wait : 10)
      }
      setMessage({ text: errorMessage(err, 'Unable to request a check.'), isError: true })
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="space-y-1">
      <button
        type="button"
        disabled={isSending || cooldown > 0}
        onClick={checkNow}
        className="rounded-lg bg-[#ffb100] px-3 py-1.5 text-xs font-semibold text-black disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSending ? 'Requesting…' : cooldown > 0 ? `Check now (wait ${cooldown}s)` : 'Check now'}
      </button>
      {message && (
        <p className={`text-xs ${message.isError ? 'text-red-600 dark:text-red-400' : 'text-[var(--text-muted)]'}`}>
          {message.text}
        </p>
      )}
    </div>
  )
}
