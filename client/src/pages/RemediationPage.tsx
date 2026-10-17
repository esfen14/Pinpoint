import { useCallback, useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { PageHeader } from '../components/shared/PageHeader'
import { ActionsTable } from '../components/remediation/ActionsTable'
import { ActionFormDialog } from '../components/remediation/ActionFormDialog'
import { RunLog } from '../components/remediation/RunLog'
import { StatusPanel } from '../components/remediation/StatusPanel'
import { useCurrentUser } from '../contexts/CurrentUserContext'
import { ApiError, errorMessage } from '../lib/api'
import {
  deleteAction, getActionTypes, getHealth, getSettings, listActions, updateAction, updateSettings,
} from '../lib/remediationApi'
import type {
  ActionTypeInfo, RemediationAction, RemediationHealth, RemediationSettings,
} from '../types/remediation'

type Tab = 'actions' | 'runs'

// How often the health card refreshes; the consumer itself runs every 15 seconds.
const HEALTH_REFRESH_MS = 15000

const alertClass =
  'rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-300'

// Remediation: the actions that run when a service or host reaches a hard failure, and the log of
// what was decided. Changing actions needs remediation.manage; viewing needs remediation.view.
export function RemediationPage() {
  const { hasPermission } = useCurrentUser()
  const canManage = hasPermission('remediation.manage')

  const [tab, setTab] = useState<Tab>('actions')
  const [actions, setActions] = useState<RemediationAction[]>([])
  const [types, setTypes] = useState<ActionTypeInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [editing, setEditing] = useState<RemediationAction | 'new' | null>(null)
  const [health, setHealth] = useState<RemediationHealth | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [settings, setSettings] = useState<RemediationSettings | null>(null)
  const [settingsError, setSettingsError] = useState<string | null>(null)
  const [statusLoading, setStatusLoading] = useState(true)
  const [switchSaving, setSwitchSaving] = useState(false)

  const load = useCallback(async () => {
    setLoadError(null)
    try {
      const [loadedActions, loadedTypes] = await Promise.all([listActions(), getActionTypes()])
      setActions(loadedActions)
      setTypes(loadedTypes)
    } catch (err) {
      setLoadError(
        err instanceof ApiError && err.status === 403
          ? 'You do not have permission to view remediation.'
          : errorMessage(err, 'Unable to load remediation actions.'),
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const loadHealth = useCallback(async () => {
    try {
      setHealth(await getHealth())
      setHealthError(null)
    } catch (err) {
      setHealthError(
        err instanceof ApiError && err.status === 403
          ? 'You do not have permission to view the health of automatic recovery.'
          : 'Unable to load the health of automatic recovery.',
      )
    }
  }, [])

  const loadSettings = useCallback(async () => {
    try {
      setSettings(await getSettings())
      setSettingsError(null)
    } catch (err) {
      setSettingsError(
        err instanceof ApiError && err.status === 403
          ? 'You do not have permission to view the kill switch.'
          : 'Unable to load the kill switch.',
      )
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    Promise.all([loadHealth(), loadSettings()]).finally(() => {
      if (!cancelled) setStatusLoading(false)
    })
    const timer = window.setInterval(loadHealth, HEALTH_REFRESH_MS)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [loadHealth, loadSettings])

  const toggleKillSwitch = async () => {
    if (!settings) return
    const stopping = settings.enabled
    const question = stopping
      ? 'Stop automatic recovery? This stops for every action: nothing will run until you switch it back on. Failures are still logged as skipped.'
      : 'Resume automatic recovery? Enabled actions will run again on the next hard failure.'
    if (!window.confirm(question)) return
    setSwitchSaving(true)
    setSettingsError(null)
    try {
      setSettings(await updateSettings({ enabled: !stopping }))
    } catch (err) {
      setSettingsError(errorMessage(err, 'Unable to change the kill switch.'))
    } finally {
      setSwitchSaving(false)
    }
  }

  const saveRepeatLimits = async (repeatCount: number, repeatWindowHours: number) => {
    setSettings(await updateSettings({ repeatCount, repeatWindowHours }))
  }

  const typeLabels = Object.fromEntries(types.map((t) => [t.key, t.label]))

  const toggle = async (action: RemediationAction) => {
    setBusyId(action.id)
    setActionError(null)
    try {
      const saved = await updateAction(
        action.id,
        {
          name: action.name,
          actionType: action.actionType,
          scopeKind: action.scopeKind,
          hostPattern: action.hostPattern,
          servicePattern: action.servicePattern,
          parameters: action.parameters,
          enabled: !action.enabled,
          maxRunsPerHour: action.maxRunsPerHour,
          cooldownSeconds: action.cooldownSeconds,
          runWhenAcknowledged: action.runWhenAcknowledged,
          notifyOn: action.notifyOn,
        },
        action.version,
      )
      setActions((current) => current.map((a) => (a.id === saved.id ? saved : a)))
    } catch (err) {
      setActionError(errorMessage(err, 'Unable to change this action.'))
    } finally {
      setBusyId(null)
    }
  }

  const remove = async (action: RemediationAction) => {
    if (!window.confirm(`Delete the action ${action.name}? Its run history stays in the log.`)) return
    setBusyId(action.id)
    setActionError(null)
    try {
      await deleteAction(action.id)
      await load()
    } catch (err) {
      setActionError(errorMessage(err, 'Unable to delete this action.'))
    } finally {
      setBusyId(null)
    }
  }

  const tabClass = (active: boolean) =>
    `pb-3 text-sm transition ${
      active
        ? 'border-b-2 border-[var(--text)] font-medium text-[var(--text)]'
        : 'text-[var(--text-muted)] hover:text-[var(--text)]'
    }`

  return (
    <main className="ml-[220px] flex-1">
      <div className="space-y-6 p-6">
        <PageHeader
          title="Remediation"
          description="Actions that run when a service or host reaches a hard failure, and what was decided each time."
        />

        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200">
          Actions run automatically when a service reaches a hard failure.
        </div>

        <StatusPanel
          health={health}
          healthError={healthError}
          settings={settings}
          settingsError={settingsError}
          isLoading={statusLoading}
          canManage={canManage}
          isSaving={switchSaving}
          onToggleKillSwitch={toggleKillSwitch}
          onSaveRepeatLimits={saveRepeatLimits}
        />

        <div role="tablist" className="flex gap-6 border-b border-[var(--border)]">
          <button type="button" role="tab" aria-selected={tab === 'actions'} onClick={() => setTab('actions')} className={tabClass(tab === 'actions')}>
            Actions
          </button>
          <button type="button" role="tab" aria-selected={tab === 'runs'} onClick={() => setTab('runs')} className={tabClass(tab === 'runs')}>
            Run log
          </button>
        </div>

        {tab === 'actions' && (
          <section className="space-y-4">
            {canManage && (
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setEditing('new')}
                  disabled={types.length === 0}
                  className="flex items-center gap-2 rounded-xl bg-[#ffb100] px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
                >
                  <Plus className="h-4 w-4" />
                  Add action
                </button>
              </div>
            )}

            {loadError && <div role="alert" className={alertClass}>{loadError}</div>}
            {actionError && <div role="alert" className={alertClass}>{actionError}</div>}

            {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading actions…</p>}

            {!isLoading && !loadError && actions.length === 0 && (
              <p className="rounded-xl border border-dashed border-[var(--border)] p-6 text-center text-sm text-[var(--text-muted)]">
                No actions yet.{canManage ? ' Add one to start recording what happens on a hard failure.' : ''}
              </p>
            )}

            {actions.length > 0 && (
              <ActionsTable
                actions={actions}
                typeLabels={typeLabels}
                canManage={canManage}
                busyId={busyId}
                killSwitchOn={settings?.enabled === false}
                onToggle={toggle}
                onEdit={setEditing}
                onDelete={remove}
              />
            )}
          </section>
        )}

        {tab === 'runs' && <RunLog actions={actions} />}
      </div>

      {editing !== null && (
        <ActionFormDialog
          types={types}
          action={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            load()
          }}
          onReload={() => {
            setEditing(null)
            load()
          }}
        />
      )}
    </main>
  )
}
