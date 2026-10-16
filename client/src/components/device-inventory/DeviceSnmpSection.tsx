import { useCallback, useEffect, useState } from 'react'
import { Loader2, Radio } from 'lucide-react'

import { errorMessage } from '../../lib/api'
import {
  getDevicePluginVariables,
  resetDevicePluginVariables,
  saveDevicePluginVariables,
  testDeviceSnmp,
} from '../../lib/devicePluginVariablesApi'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { DropdownSelect } from '../shared/DropdownSelect'
import type {
  DeviceVariablesResponse,
  SnmpFormValues,
  SnmpSecretName,
  SnmpSecurityLevel,
  SnmpTestResult,
  SnmpVersion,
} from '../../types/devicePluginVariables'
import {
  AUTH_PROTOCOLS,
  EMPTY_FORM,
  PRIV_PROTOCOLS,
  SECURITY_LEVELS,
  formFromSaved,
  formProblem,
  needsAuth,
  needsPriv,
  variablesFromForm,
} from './snmpForm'

type Props = {
  deviceId: number
  // The Nagios host name shown in messages.
  hostname: string
}

const VERSION_OPTIONS: { value: SnmpVersion; label: string }[] = [
  { value: '', label: 'Default' },
  { value: '1', label: 'Version 1' },
  { value: '2c', label: 'Version 2c' },
  { value: '3', label: 'Version 3 (user and passwords)' },
]
const LEVEL_OPTIONS: { value: SnmpSecurityLevel | ''; label: string }[] = [
  { value: '', label: 'Choose…' },
  ...SECURITY_LEVELS,
]

const INPUT = 'h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-sm text-[var(--text)] disabled:cursor-not-allowed disabled:opacity-50'
const BUTTON = 'flex items-center gap-1 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs font-medium hover:bg-[var(--hover)] disabled:opacity-50'

// The badge text: what this device is polled with now.
function modeLabel(saved: DeviceVariablesResponse): string {
  const version = String(saved.variables.protocol ?? '')
  if (version === '3') return `SNMP v3 · ${String(saved.variables.security_level ?? 'not set up')}`
  if (version === '1' || version === '2c') return `SNMP v${version}`
  return 'Default settings'
}

// The SNMP section of the device drawer: the version a device is polled with (default, v1, v2c or v3) and, for
// v3, the user and credentials. Saving applies the Nagios config; the server decides everything, rejects an
// incomplete v3 setup naming the field, and never returns a password: a saved password is shown only as
// "Saved", is kept when its box is left blank and can be removed. Test asks the device once with what is in the
// form (nothing is saved). Needs system.hosts to view and system.hosts.edit to change.
export function DeviceSnmpSection({ deviceId, hostname }: Props) {
  const { hasPermission } = useCurrentUser()
  const canEdit = hasPermission('system.hosts.edit')

  const [saved, setSaved] = useState<DeviceVariablesResponse | null>(null)
  const [form, setForm] = useState<SnmpFormValues>(EMPTY_FORM)
  const [removed, setRemoved] = useState<Partial<Record<SnmpSecretName, boolean>>>({})
  const [loadError, setLoadError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [busy, setBusy] = useState<'save' | 'test' | 'reset' | null>(null)
  const [problem, setProblem] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<SnmpTestResult | null>(null)

  const load = useCallback((response: DeviceVariablesResponse) => {
    setSaved(response)
    setForm(formFromSaved(response))
    setRemoved({})
  }, [])

  useEffect(() => {
    let cancelled = false
    getDevicePluginVariables(deviceId)
      .then((response) => {
        if (cancelled) return
        load(response)
        setLoadError(null)
      })
      .catch((err) => {
        if (!cancelled) setLoadError(errorMessage(err, 'Unable to load the SNMP settings.'))
      })
    return () => {
      cancelled = true
    }
  }, [deviceId, reloadKey, load])

  function change(values: Partial<SnmpFormValues>) {
    setForm((current) => ({ ...current, ...values }))
    setProblem(null)
    setNotice(null)
    setTestResult(null)
  }

  const kept: Partial<Record<SnmpSecretName, boolean>> = {
    auth_password: !!saved?.secrets_set.auth_password && !removed.auth_password,
    priv_password: !!saved?.secrets_set.priv_password && !removed.priv_password,
  }

  // A removed password the chosen level no longer uses is dropped by the server on its own.
  function secretsToClear(): SnmpSecretName[] {
    const result: SnmpSecretName[] = []
    if (removed.auth_password && needsAuth(form)) result.push('auth_password')
    if (removed.priv_password && needsPriv(form)) result.push('priv_password')
    return result
  }

  function check(): Record<string, string | number> | null {
    const message = formProblem(form, kept)
    if (message) {
      setProblem(message)
      return null
    }
    return variablesFromForm(form, saved)
  }

  async function run(kind: 'save' | 'test' | 'reset', action: () => Promise<void>, failure: string) {
    setBusy(kind)
    setProblem(null)
    setNotice(null)
    setTestResult(null)
    try {
      await action()
    } catch (err) {
      setProblem(errorMessage(err, failure))
    } finally {
      setBusy(null)
    }
  }

  async function save() {
    const variables = check()
    if (!variables) return
    await run('save', async () => {
      load(await saveDevicePluginVariables(deviceId, variables, secretsToClear()))
      setNotice('SNMP settings saved.')
    }, 'Unable to save the SNMP settings.')
  }

  async function test() {
    const variables = check()
    if (!variables) return
    await run('test', async () => {
      setTestResult(await testDeviceSnmp(deviceId, variables))
    }, 'Unable to test the SNMP settings.')
  }

  async function reset() {
    await run('reset', async () => {
      load(await resetDevicePluginVariables(deviceId))
      setNotice('SNMP settings reset to the defaults.')
    }, 'Unable to reset the SNMP settings.')
  }

  if (loadError) {
    return (
      <section>
        <h3 className="mb-2 font-semibold">SNMP</h3>
        <div className="space-y-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-red-600 dark:text-red-400">
          <p>{loadError}</p>
          <button
            type="button"
            onClick={() => {
              setLoadError(null)
              setReloadKey((key) => key + 1)
            }}
            className="rounded-lg border border-red-500/40 px-3 py-1 text-xs font-medium hover:bg-red-500/10"
          >
            Retry
          </button>
        </div>
      </section>
    )
  }

  if (!saved) {
    return (
      <p className="flex items-center text-[var(--text-muted)]">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading SNMP settings…
      </p>
    )
  }

  // Devices without an SNMP port have nothing to configure: leave the drawer as it was.
  if (saved.in_use !== true) return null

  const hasSaved = Object.keys(saved.variables).length > 0 || !!saved.secrets_set.auth_password || !!saved.secrets_set.priv_password
  const disabled = !canEdit || busy !== null

  function passwordField(name: SnmpSecretName, label: string, value: string, onChange: (value: string) => void) {
    const isSaved = kept[name]
    return (
      <div>
        <label className="mb-1 block text-xs font-medium" htmlFor={`snmp-${name}`}>{label}</label>
        <div className="flex gap-2">
          <input
            id={`snmp-${name}`}
            type="password"
            autoComplete="new-password"
            value={value}
            placeholder={isSaved ? 'Saved. Leave blank to keep it.' : ''}
            disabled={disabled}
            onChange={(event) => onChange(event.target.value)}
            className={INPUT}
          />
          {canEdit && saved?.secrets_set[name] && (
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => setRemoved((current) => ({ ...current, [name]: !current[name] }))}
              aria-label={`${removed[name] ? 'Keep' : 'Remove'} saved ${label.toLowerCase()}`}
              className={`${BUTTON} shrink-0`}
            >
              {removed[name] ? 'Keep saved' : 'Remove saved'}
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <section className="rounded-2xl border border-[#F4A90B]/40 bg-[#F4A90B]/5 p-4">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 font-semibold">
          <Radio className="h-4 w-4 text-[#F4A90B]" aria-hidden="true" />
          SNMP monitoring
        </h3>
        <span className="rounded-full bg-[#F4A90B]/15 px-2.5 py-0.5 text-xs font-medium text-[#F4A90B]">
          {modeLabel(saved)}
        </span>
      </div>
      <p className="mb-3 text-xs text-[var(--text-muted)]">
        This device answers SNMP. Choose how {hostname} is polled: version 1, 2c, or 3 with a user and passwords.
        Leave the version on Default to use the network-wide settings.
        {!canEdit && ' You can view SNMP settings but not change them.'}
      </p>

      <div className="space-y-3">
        <div>
          <p className="mb-1 text-xs font-medium">SNMP version</p>
          <DropdownSelect<SnmpVersion>
            label="SNMP version"
            block
            value={form.version}
            disabled={disabled}
            options={VERSION_OPTIONS}
            onChange={(version) => change({ version })}
          />
        </div>

        {form.version !== '3' && (
          <div>
            <label className="mb-1 block text-xs font-medium" htmlFor="snmp-community">Community</label>
            <input
              id="snmp-community"
              type="text"
              value={form.community}
              placeholder="Network-wide default"
              disabled={disabled}
              onChange={(event) => change({ community: event.target.value })}
              className={INPUT}
            />
          </div>
        )}

        {form.version === '3' && (
          <>
            <div>
              <p className="mb-1 text-xs font-medium">Security level</p>
              <DropdownSelect<SnmpSecurityLevel | ''>
                label="Security level"
                block
                value={form.securityLevel}
                disabled={disabled}
                options={LEVEL_OPTIONS}
                onChange={(securityLevel) => change({ securityLevel })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium" htmlFor="snmp-user">SNMP v3 user</label>
              <input
                id="snmp-user"
                type="text"
                autoComplete="off"
                value={form.user}
                disabled={disabled}
                onChange={(event) => change({ user: event.target.value })}
                className={INPUT}
              />
            </div>
            {needsAuth(form) && (
              <>
                <div>
                  <p className="mb-1 text-xs font-medium">Authentication protocol</p>
                  <DropdownSelect<string>
                    label="Authentication protocol"
                    block
                    value={form.authProtocol}
                    disabled={disabled}
                    options={AUTH_PROTOCOLS.map((name) => ({ value: name, label: name }))}
                    onChange={(authProtocol) => change({ authProtocol })}
                  />
                </div>
                {passwordField('auth_password', 'Authentication password', form.authPassword, (value) => change({ authPassword: value }))}
              </>
            )}
            {needsPriv(form) && (
              <>
                <div>
                  <p className="mb-1 text-xs font-medium">Privacy protocol</p>
                  <DropdownSelect<string>
                    label="Privacy protocol"
                    block
                    value={form.privProtocol}
                    disabled={disabled}
                    options={PRIV_PROTOCOLS.map((name) => ({ value: name, label: name }))}
                    onChange={(privProtocol) => change({ privProtocol })}
                  />
                </div>
                {passwordField('priv_password', 'Privacy password', form.privPassword, (value) => change({ privPassword: value }))}
              </>
            )}
            <p className="text-xs text-[var(--text-muted)]">
              Passwords are stored encrypted and are never shown again. They are not written to the Nagios host file.
            </p>
          </>
        )}
      </div>

      {notice && (
        <p role="status" className="mt-3 rounded-lg bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">
          {notice}
        </p>
      )}
      {problem && (
        <p role="alert" className="mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-600 dark:text-red-400">
          {problem}
        </p>
      )}
      {testResult && (
        <p
          role={testResult.ok ? 'status' : 'alert'}
          className={`mt-3 rounded-lg px-3 py-2 text-xs ${testResult.ok
            ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
            : 'bg-red-500/10 text-red-600 dark:text-red-400'}`}
        >
          {testResult.ok ? 'The device answered: ' : `The test failed (${testResult.state}): `}{testResult.message}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {canEdit && (
          <button type="button" onClick={() => void save()} disabled={disabled} className={BUTTON}>
            {busy === 'save' && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Save
          </button>
        )}
        {canEdit && (
          <button type="button" onClick={() => void test()} disabled={disabled} className={BUTTON}>
            {busy === 'test' && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Test
          </button>
        )}
        {canEdit && (
          <button type="button" onClick={() => void reset()} disabled={disabled || !hasSaved} className={BUTTON}>
            {busy === 'reset' && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Reset to defaults
          </button>
        )}
      </div>
    </section>
  )
}
