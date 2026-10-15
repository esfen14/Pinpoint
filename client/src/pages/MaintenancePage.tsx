import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { PageHeader } from '../components/shared/PageHeader'
import { NagiosSyncNotice } from '../components/shared/NagiosSyncNotice'
import { MaintenanceWindowForm } from '../components/maintenance/MaintenanceWindowForm'
import { MaintenanceWindowsTable } from '../components/maintenance/MaintenanceWindowsTable'
import { useDisplayTime } from '../hooks/useDisplayTime'
import { errorMessage } from '../lib/api'
import { cancelMaintenanceWindow, createMaintenanceWindow, listMaintenanceWindows, updateMaintenanceWindow } from '../lib/maintenanceApi'
import type { MaintenanceDevice, MaintenanceInput, MaintenanceWindow } from '../types/maintenance'

// null: the form is closed. 'new': creating. A window: editing it.
type Editing = null | 'new' | MaintenanceWindow

export function MaintenancePage() {
  const { timeZone } = useDisplayTime()
  const [windows, setWindows] = useState<MaintenanceWindow[]>([])
  const [devices, setDevices] = useState<MaintenanceDevice[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Editing>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await listMaintenanceWindows()
      setWindows(data.windows)
      setDevices(data.devices)
      setLoadError(null)
    } catch (err) {
      setLoadError(errorMessage(err, 'Unable to load maintenance windows.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  // First load. (Reloads after a change call load() from the handlers.)
  useEffect(() => {
    let cancelled = false
    listMaintenanceWindows()
      .then((data) => {
        if (cancelled) return
        setWindows(data.windows)
        setDevices(data.devices)
      })
      .catch((err) => {
        if (!cancelled) setLoadError(errorMessage(err, 'Unable to load maintenance windows.'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function save(input: MaintenanceInput) {
    setIsSaving(true)
    setSaveError(null)
    setNotice(null)
    try {
      if (editing && editing !== 'new') {
        const result = await updateMaintenanceWindow(editing.id, input)
        setNotice(result.nagios_synced ? null : result.nagios_message)
        setSuccess('Maintenance window updated.')
      } else {
        await createMaintenanceWindow(input)
        setSuccess('Maintenance window created.')
      }
      setEditing(null)
      await load()
    } catch (err) {
      setSaveError(errorMessage(err, 'Unable to save the maintenance window.'))
    } finally {
      setIsSaving(false)
    }
  }

  async function cancel(window: MaintenanceWindow) {
    setBusyId(window.id)
    setNotice(null)
    setSuccess(null)
    try {
      const result = await cancelMaintenanceWindow(window.id)
      setNotice(result.nagios_synced ? null : result.nagios_message)
      setSuccess('Maintenance window cancelled.')
      setConfirmingId(null)
      await load()
    } catch (err) {
      setLoadError(errorMessage(err, 'Unable to cancel the maintenance window.'))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <main className="ml-55 flex-1 space-y-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageHeader
          title="Maintenance"
          highlight="Windows"
          description="Schedule planned work. Alerts and notifications for the devices stop while the window is open."
        />
        <button
          type="button"
          onClick={() => {
            setEditing('new')
            setSaveError(null)
            setSuccess(null)
          }}
          className="flex items-center gap-2 rounded-lg bg-[#ffb100] px-4 py-2 text-sm font-semibold text-gray-900 hover:bg-[#f0a500]"
        >
          <Plus className="h-4 w-4" />
          New window
        </button>
      </div>

      <p className="rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm text-[var(--text-muted)]">
        A maintenance window <strong className="text-[var(--text)]">silences alerts</strong> by scheduling Nagios downtime.
        It is not the Maintenance Mode switch in{' '}
        <Link to="/settings#system" className="underline">Settings → System</Link>, which only pauses PinPoint&apos;s own
        background jobs (scans and checks) and does not silence any alert.
      </p>

      <NagiosSyncNotice message={notice} onDismiss={() => setNotice(null)} />
      {success && <p role="status" className="text-sm text-emerald-600 dark:text-emerald-400">{success}</p>}

      {editing && (
        <MaintenanceWindowForm
          // A different window gets a fresh form.
          key={editing === 'new' ? 'new' : editing.id}
          devices={devices}
          window={editing === 'new' ? null : editing}
          timeZone={timeZone}
          isSaving={isSaving}
          serverError={saveError}
          onSubmit={save}
          onClose={() => setEditing(null)}
        />
      )}

      {isLoading ? (
        <p className="text-sm text-[var(--text-muted)]">Loading maintenance windows…</p>
      ) : loadError ? (
        <div role="alert" className="flex items-center gap-3 text-sm text-red-600 dark:text-red-400">
          <span>{loadError}</span>
          <button type="button" onClick={() => void load()} className="underline">Try again</button>
        </div>
      ) : windows.length === 0 ? (
        <p className="rounded-3xl border border-dashed border-[var(--border)] px-6 py-10 text-center text-sm text-[var(--text-muted)]">
          No maintenance windows yet. Create one before planned work to stop alerts for it.
        </p>
      ) : (
        <MaintenanceWindowsTable
          windows={windows}
          confirmingId={confirmingId}
          busyId={busyId}
          onEdit={(window) => {
            setEditing(window)
            setSaveError(null)
            setSuccess(null)
          }}
          onAskCancel={(window) => setConfirmingId(window.id)}
          onConfirmCancel={(window) => void cancel(window)}
          onDismissCancel={() => setConfirmingId(null)}
        />
      )}
    </main>
  )
}
