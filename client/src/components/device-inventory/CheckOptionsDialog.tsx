import { useCallback, useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'

import { errorMessage } from '../../lib/api'
import {
  getDevicePluginVariables,
  resetDevicePluginVariables,
  saveDevicePluginVariables,
} from '../../lib/devicePluginVariablesApi'
import type { DeviceVariablesResponse } from '../../types/devicePluginVariables'
import { DropdownSelect } from '../shared/DropdownSelect'
import {
  CHECK_OPTION_SERVICES,
  EMPTY_VALUES,
  HTTP_METHODS,
  type CheckOptionName,
  type CheckOptionValues,
  defaultHint,
  fieldsFor,
  formProblem,
  valuesFromSaved,
  variablesFromForm,
} from './checkOptionsForm'

type Props = {
  deviceId: number
  hostname: string
  // The registry service of the port ("http", "pop3", ...); settings are kept per device and service.
  plugin: string
  // False for a user without system.hosts.edit or an ended device: the options are shown, not changed.
  canEdit: boolean
  onClose: () => void
}

const INPUT = 'h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-[15px] text-[var(--text)] disabled:cursor-not-allowed disabled:opacity-50'
const BUTTON = 'flex items-center gap-1 rounded-lg border border-[var(--border)] px-3 py-1.5 text-[13px] font-medium hover:bg-[var(--hover)] disabled:opacity-50'

const METHOD_OPTIONS = [{ value: '', label: 'Default' }, ...HTTP_METHODS.map((method) => ({ value: method, label: method }))]

// "Check options" of a monitored HTTP, HTTPS, POP3 or IMAP port (spec files/Device_Inventory_Requirements.md):
// what the check expects back (text, status codes, greeting), the virtual host and the request method.
// The options are saved per device and service through the plugin variables API, so they apply to every
// port of that service on the device. The values are checked here as the server checks them, the server's
// own 400 and 422 messages are shown as they are, and Reset to defaults removes the override. Without
// system.hosts.edit the saved options are shown and nothing can be changed.
export function CheckOptionsDialog({ deviceId, hostname, plugin, canEdit, onClose }: Props) {
  const title = CHECK_OPTION_SERVICES[plugin] ?? plugin
  const fields = fieldsFor(plugin)

  const [saved, setSaved] = useState<DeviceVariablesResponse | null>(null)
  const [values, setValues] = useState<CheckOptionValues>(EMPTY_VALUES)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [busy, setBusy] = useState<'save' | 'reset' | null>(null)
  const [problem, setProblem] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const load = useCallback((response: DeviceVariablesResponse) => {
    setSaved(response)
    setValues(valuesFromSaved(response, plugin))
  }, [plugin])

  useEffect(() => {
    let cancelled = false
    getDevicePluginVariables(deviceId, plugin)
      .then((response) => {
        if (cancelled) return
        load(response)
        setLoadError(null)
      })
      .catch((err) => {
        if (!cancelled) setLoadError(errorMessage(err, 'Unable to load the check options.'))
      })
    return () => {
      cancelled = true
    }
  }, [deviceId, plugin, reloadKey, load])

  function change(name: CheckOptionName, value: string) {
    setValues((current) => ({ ...current, [name]: value }))
    setProblem(null)
    setNotice(null)
  }

  async function run(kind: 'save' | 'reset', action: () => Promise<void>, failure: string) {
    setBusy(kind)
    setProblem(null)
    setNotice(null)
    try {
      await action()
    } catch (err) {
      setProblem(errorMessage(err, failure))
    } finally {
      setBusy(null)
    }
  }

  async function save() {
    const invalid = formProblem(plugin, values)
    if (invalid) {
      setProblem(invalid.message)
      return
    }
    await run('save', async () => {
      load(await saveDevicePluginVariables(deviceId, variablesFromForm(plugin, values, saved), [], plugin))
      setNotice('Check options saved.')
    }, 'Unable to save the check options.')
  }

  async function reset() {
    await run('reset', async () => {
      load(await resetDevicePluginVariables(deviceId, plugin))
      setNotice('Check options reset to the defaults.')
    }, 'Unable to reset the check options.')
  }

  const disabled = !canEdit || busy !== null
  const hasSaved = !!saved && Object.keys(saved.variables).length > 0

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Check options for ${title} on ${hostname}`}
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4"
    >
      <div className="max-h-full w-full max-w-md space-y-3 overflow-y-auto rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 shadow-xl">
        <h3 className="text-[17px] font-semibold text-[var(--text)]">
          Check options: {title} on {hostname}
        </h3>
        <p className="text-[13px] text-[var(--text-muted)]">
          These options apply to every {title} service monitored on this device. Leave a field empty to use the default check.
          {!canEdit && ' You can view the options but not change them.'}
        </p>

        {loadError && (
          <div className="space-y-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-red-600 dark:text-red-400">
            <p>{loadError}</p>
            <button
              type="button"
              onClick={() => {
                setLoadError(null)
                setReloadKey((key) => key + 1)
              }}
              className="rounded-lg border border-red-500/40 px-3 py-1 text-[13px] font-medium hover:bg-red-500/10"
            >
              Retry
            </button>
          </div>
        )}

        {!saved && !loadError && (
          <p className="flex items-center text-[var(--text-muted)]">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading check options…
          </p>
        )}

        {saved && (
          <div className="space-y-3">
            {fields.map((field) => {
              const id = `check-option-${field.name}`
              const hint = defaultHint(plugin, field.name)
              return (
                <div key={field.name}>
                  {field.name === 'method' ? (
                    <>
                      <p className="mb-1 text-[13px] font-medium">{field.label}</p>
                      <DropdownSelect<string>
                        label={field.label}
                        block
                        value={values.method}
                        disabled={disabled}
                        options={METHOD_OPTIONS}
                        onChange={(method) => change('method', method)}
                      />
                    </>
                  ) : (
                    <>
                      <label className="mb-1 block text-[13px] font-medium" htmlFor={id}>{field.label}</label>
                      <input
                        id={id}
                        type="text"
                        autoComplete="off"
                        value={values[field.name]}
                        placeholder={field.placeholder}
                        disabled={disabled}
                        onChange={(event) => change(field.name, event.target.value)}
                        className={INPUT}
                      />
                    </>
                  )}
                  <p className="mt-1 text-[13px] text-[var(--text-muted)]">
                    {field.help}
                    {hint && ` Default: ${hint}`}
                  </p>
                </div>
              )
            })}
          </div>
        )}

        {notice && (
          <p role="status" className="rounded-lg bg-emerald-500/10 px-3 py-2 text-[13px] text-emerald-700 dark:text-emerald-300">
            {notice}
          </p>
        )}
        {problem && (
          <p role="alert" className="rounded-lg bg-red-500/10 px-3 py-2 text-[13px] text-red-600 dark:text-red-400">
            {problem}
          </p>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            {canEdit && saved && (
              <button type="button" onClick={() => void reset()} disabled={disabled || !hasSaved} className={BUTTON}>
                {busy === 'reset' && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Reset to defaults
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={onClose} disabled={busy !== null} className={BUTTON}>
              {canEdit ? 'Cancel' : 'Close'}
            </button>
            {canEdit && saved && (
              <button
                type="button"
                onClick={() => void save()}
                disabled={disabled}
                className="flex items-center gap-2 rounded-lg bg-[#ffb100] px-4 py-1.5 text-[13px] font-semibold text-black disabled:cursor-not-allowed disabled:opacity-50"
              >
                {busy === 'save' && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Save
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
