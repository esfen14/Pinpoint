import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { ApiError, errorMessage } from '../../lib/api'
import { createAction, fieldErrors, updateAction } from '../../lib/remediationApi'
import type {
  ActionTypeInfo,
  FieldErrors,
  RemediationAction,
  RemediationActionInput,
  RemediationScope,
} from '../../types/remediation'

type Props = {
  types: ActionTypeInfo[]
  // The action being edited, or null to add a new one.
  action: RemediationAction | null
  onClose: () => void
  // Called after a successful save, so the list can reload.
  onSaved: () => void
  // Called when the action changed under the editor (409): reload the list and close.
  onReload: () => void
}

const inputClass =
  'h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-sm text-[var(--text)] outline-none transition focus:border-[#ffb100]'

type FieldProps = {
  id: string
  label: string
  error?: string
  children: ReactNode
}

function Field({ id, label, error, children }: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-[var(--text)]">
        {label}
      </label>
      {children}
      {error && (
        <p id={`${id}-error`} className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}

/** The form's values as the API wants them, with the service pattern dropped for a host action. */
function buildInput(form: {
  name: string
  actionType: string
  scopeKind: RemediationScope
  hostPattern: string
  servicePattern: string
  enabled: boolean
  maxRunsPerHour: number
  cooldownSeconds: number
  parameters: Record<string, unknown>
}): RemediationActionInput {
  return {
    name: form.name,
    actionType: form.actionType,
    scopeKind: form.scopeKind,
    hostPattern: form.hostPattern,
    servicePattern: form.scopeKind === 'service' ? form.servicePattern : null,
    parameters: form.parameters,
    enabled: form.enabled,
    maxRunsPerHour: form.maxRunsPerHour,
    cooldownSeconds: form.cooldownSeconds,
  }
}

// Add or edit one action. Server validation messages are shown against the field they belong to.
export function ActionFormDialog({ types, action, onClose, onSaved, onReload }: Props) {
  const [name, setName] = useState(action?.name ?? '')
  const [actionType, setActionType] = useState(action?.actionType ?? types[0]?.key ?? '')
  const [scopeKind, setScopeKind] = useState<RemediationScope>(action?.scopeKind ?? 'service')
  const [hostPattern, setHostPattern] = useState(action?.hostPattern ?? '')
  const [servicePattern, setServicePattern] = useState(action?.servicePattern ?? '')
  const [enabled, setEnabled] = useState(action?.enabled ?? false)
  const [maxRunsPerHour, setMaxRunsPerHour] = useState(action?.maxRunsPerHour ?? 2)
  const [cooldownSeconds, setCooldownSeconds] = useState(action?.cooldownSeconds ?? 600)
  const [parameters, setParameters] = useState<Record<string, unknown>>(action?.parameters ?? {})
  const [errors, setErrors] = useState<FieldErrors>({})
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [stale, setStale] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const selectedType = types.find((t) => t.key === actionType)
  const title = action ? 'Edit action' : 'Add action'
  const describe = (field: string) => (errors[field] ? `remediation-${field}-error` : undefined)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    setErrors({})
    setGeneralError(null)
    setStale(false)
    const input = buildInput({
      name, actionType, scopeKind, hostPattern, servicePattern, enabled, maxRunsPerHour, cooldownSeconds,
      parameters,
    })
    try {
      if (action) await updateAction(action.id, input, action.version)
      else await createAction(input)
      onSaved()
    } catch (err) {
      const fields = fieldErrors(err)
      if (Object.keys(fields).length > 0) {
        setErrors(fields)
        const known = new Set(['name', 'actionType', 'scopeKind', 'hostPattern', 'servicePattern', 'enabled', 'maxRunsPerHour', 'cooldownSeconds', ...(selectedType?.parameters.map((parameter) => `parameters.${parameter.name}`) ?? [])])
        const other = Object.entries(fields).filter(([key]) => !known.has(key))
        if (other.length > 0) setGeneralError(other.map(([key, message]) => `${key}: ${message}`).join(' '))
      } else {
        setGeneralError(errorMessage(err, 'Unable to save this action.'))
        setStale(err instanceof ApiError && err.status === 409)
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="remediation-form-title"
        onSubmit={submit}
        noValidate
        className="max-h-full w-full max-w-lg space-y-4 overflow-y-auto rounded-2xl bg-white p-6 shadow-xl dark:bg-[#171B20]"
      >
        <h2 id="remediation-form-title" className="text-lg font-semibold text-[var(--text)]">
          {title}
        </h2>

        {generalError && (
          <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-300">
            <span>{generalError}</span>
            {stale && (
              <button type="button" onClick={onReload} className="ml-3 font-medium underline">
                Reload
              </button>
            )}
          </div>
        )}

        <Field id="remediation-name" label="Name" error={errors.name}>
          <input
            id="remediation-name"
            className={inputClass}
            value={name}
            onChange={(e) => setName(e.target.value)}
            aria-describedby={describe('name')}
            aria-invalid={Boolean(errors.name)}
          />
        </Field>

        <Field id="remediation-actionType" label="Action type" error={errors.actionType}>
          <select
            id="remediation-actionType"
            className={inputClass}
            value={actionType}
            onChange={(e) => {
              setActionType(e.target.value)
              setParameters({})
              setErrors({})
            }}
            aria-describedby={describe('actionType')}
          >
            {types.map((t) => (
              <option key={t.key} value={t.key}>
                {t.label}
              </option>
            ))}
          </select>
          {selectedType && <p className="mt-1 text-sm text-[var(--text-muted)]">{selectedType.description}</p>}
        </Field>

        {selectedType?.parameters.map((parameter) => {
          const field = `parameters.${parameter.name}`
          const id = `remediation-${field}`
          const value = typeof parameters[parameter.name] === 'string' ? String(parameters[parameter.name]) : ''
          const shared = {
            id, className: inputClass, value,
            'aria-describedby': describe(field), 'aria-invalid': Boolean(errors[field]),
            required: parameter.required,
            onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
              setParameters((current) => ({ ...current, [parameter.name]: event.target.value })),
          }
          return (
            <Field key={field} id={id} label={parameter.label} error={errors[field]}>
              {parameter.type === 'choice' ? (
                <select {...shared}>
                  <option value="">Choose a service</option>
                  {parameter.choices?.map((choice) => <option key={choice} value={choice}>{choice}</option>)}
                </select>
              ) : <input {...shared} placeholder="apache2" />}
            </Field>
          )
        })}

        <Field id="remediation-scopeKind" label="Scope" error={errors.scopeKind}>
          <select
            id="remediation-scopeKind"
            className={inputClass}
            value={scopeKind}
            onChange={(e) => setScopeKind(e.target.value as RemediationScope)}
            aria-describedby={describe('scopeKind')}
          >
            <option value="service">Service</option>
            <option value="host">Host</option>
          </select>
        </Field>

        <Field id="remediation-hostPattern" label="Host pattern" error={errors.hostPattern}>
          <input
            id="remediation-hostPattern"
            className={inputClass}
            value={hostPattern}
            placeholder="web-01 or web-*"
            onChange={(e) => setHostPattern(e.target.value)}
            aria-describedby={describe('hostPattern')}
            aria-invalid={Boolean(errors.hostPattern)}
          />
        </Field>

        {scopeKind === 'service' && (
          <Field id="remediation-servicePattern" label="Service pattern" error={errors.servicePattern}>
            <input
              id="remediation-servicePattern"
              className={inputClass}
              value={servicePattern}
              placeholder="HTTP or HT*"
              onChange={(e) => setServicePattern(e.target.value)}
              aria-describedby={describe('servicePattern')}
              aria-invalid={Boolean(errors.servicePattern)}
            />
          </Field>
        )}

        <div className="grid grid-cols-2 gap-4">
          <Field id="remediation-maxRunsPerHour" label="Max runs per hour" error={errors.maxRunsPerHour}>
            <input
              id="remediation-maxRunsPerHour"
              type="number"
              className={inputClass}
              value={maxRunsPerHour}
              onChange={(e) => setMaxRunsPerHour(Number(e.target.value))}
              aria-describedby={describe('maxRunsPerHour')}
            />
          </Field>
          <Field id="remediation-cooldownSeconds" label="Cooldown (seconds)" error={errors.cooldownSeconds}>
            <input
              id="remediation-cooldownSeconds"
              type="number"
              className={inputClass}
              value={cooldownSeconds}
              onChange={(e) => setCooldownSeconds(Number(e.target.value))}
              aria-describedby={describe('cooldownSeconds')}
            />
          </Field>
        </div>

        <label className="flex items-center gap-2 text-sm text-[var(--text)]">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
          Enabled
        </label>
        {errors.enabled && <p className="text-sm text-red-600">{errors.enabled}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="rounded-xl border border-[var(--border)] px-4 py-2 text-sm text-[var(--text)] hover:bg-[var(--hover)]">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSaving}
            className="rounded-xl bg-[#ffb100] px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
          >
            Save action
          </button>
        </div>
      </form>
    </div>
  )
}
