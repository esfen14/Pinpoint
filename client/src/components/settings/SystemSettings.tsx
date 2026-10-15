import { useState } from 'react'
import {
  Database,
  HardDrive,
  History,
  Wrench,
} from 'lucide-react'

import { SettingsCard } from './SettingsCard'
import { NotificationPolicySettings } from './NotificationPolicySettings'
import { SettingsSelect } from './SettingsSelect'
import { SettingsToggle } from './SettingsToggle'
import { SettingsActions } from './SettingsActions'

import {
  useSystemSettings,
} from '../../contexts/SystemSettingsContext'

const updateFrequencyOptions = [
  {
    value: 'weekly',
    label: 'Weekly',
  },
  {
    value: 'monthly',
    label: 'Monthly',
  },
  {
    value: 'quarterly',
    label: 'Quarterly',
  },
  {
    value: 'manual',
    label: 'Manual',
  },
]

// Same bounds as the server (PUT /api/system): retry 1 to 10 minutes, attempts 1 to 10.
const RETRY_INTERVAL_MINUTES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
const CHECK_ATTEMPT_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// Nagios's own flap thresholds (nagios.cfg), shown as help text. Used when a field is left empty.
const NAGIOS_DEFAULT_LOW_FLAP = 5
const NAGIOS_DEFAULT_HIGH_FLAP = 20

// Same rules as the server (PUT /api/system): 0 to 100, low below high, empty is allowed.
function flapThresholdError(low: number | null, high: number | null): string | null {
  for (const value of [low, high]) {
    if (value !== null && (!Number.isFinite(value) || value < 0 || value > 100)) {
      return 'Flap thresholds must be a percentage from 0 to 100.'
    }
  }
  if (low !== null && high !== null && low >= high) {
    return 'The low flap threshold must be lower than the high flap threshold.'
  }
  return null
}

interface FlapThresholdInputProps {
  label: string
  description: string
  value: number | null
  disabled: boolean
  onChange: (value: number | null) => void
}

// Keeps what the user typed, so "1." or "abc" is not rewritten while editing;
// an unparseable entry is stored as NaN so the card can report it.
function FlapThresholdInput({ label, description, value, disabled, onChange }: FlapThresholdInputProps) {
  const [draft, setDraft] = useState<string | null>(null)
  const shown = draft ?? (value === null ? '' : String(value))
  const id = label.toLowerCase().replace(/\s+/g, '-')

  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-medium text-[var(--text)]">{label}</label>
      <input
        id={id}
        type="text"
        inputMode="decimal"
        value={shown}
        disabled={disabled}
        placeholder="Nagios default"
        onChange={(e) => {
          const text = e.target.value
          setDraft(text)
          onChange(text.trim() === '' ? null : Number(text))
        }}
        onBlur={() => setDraft(null)}
        className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-sm text-[var(--text)] outline-none transition duration-200 focus:border-[#ffb100] disabled:cursor-not-allowed disabled:opacity-50"
      />
      <p className="mt-1.5 text-xs text-[var(--text-muted)]">{description}</p>
    </div>
  )
}

const retentionOptions = [
  {
    value: '7',
    label: '7 days',
  },
  {
    value: '30',
    label: '30 days',
  },
  {
    value: '60',
    label: '60 days',
  },
  {
    value: '90',
    label: '90 days',
  },
  {
    value: '180',
    label: '180 days',
  },
  {
    value: '365',
    label: '1 year',
  },
]

export function SystemSettings() {
  const {
    settings,
    updateSettings,
    saveSettings,
    discardChanges,
    hasUnsavedChanges,
    isSaving,
    saveError,
  } = useSystemSettings()

  // Invalid thresholds are explained next to the inputs and never sent to the server.
  const flapError = flapThresholdError(settings.flapLowThreshold, settings.flapHighThreshold)
  const saveUnlessInvalid = () => (flapError ? undefined : saveSettings())

  return (
    <div className="space-y-6">

      <SettingsCard
        title="System Configuration"
        description="Manage system-wide maintenance, updates, and storage behavior."
      >
        <div className="grid gap-x-8 gap-y-7 lg:grid-cols-3">

          <SettingsSelect
            label="System Update Frequency"
            description="How often to re-scan installed plugins for newer versions"
            value={
              settings.systemUpdateFrequency
            }
            options={
              updateFrequencyOptions
            }
            onChange={(value) =>
              updateSettings({
                systemUpdateFrequency:
                  value as
                    | 'weekly'
                    | 'monthly'
                    | 'quarterly'
                    | 'manual',
              })
            }
          />

          <SettingsSelect
            label="Check interval"
            description="How often Nagios checks generated hosts and services; separate from network discovery and browser refresh."
            value={String(settings.checkInterval)}
            options={[1, 2, 5, 10, 15].map((minutes) => ({ value: String(minutes), label: `${minutes} minutes` }))}
            onChange={(value) => {
              const checkInterval = Number(value)
              // A retry never waits longer than a normal check, so keep the two consistent.
              updateSettings({
                checkInterval,
                retryInterval: Math.min(settings.retryInterval, checkInterval),
              })
            }}
          />

          <SettingsSelect
            label="Data polling interval"
            description="How often Pinpoint reads results from Nagios. Separate from Nagios checks, network discovery and browser refresh."
            value={String(settings.dataPollingInterval)}
            options={[30, 60, 120, 300].map((seconds) => ({ value: String(seconds), label: `${seconds} seconds` }))}
            onChange={(value) => updateSettings({ dataPollingInterval: Number(value) })}
          />

          <SettingsSelect
            label="Retry interval"
            description="How soon Nagios re-checks something that just failed. Cannot be longer than the check interval."
            value={String(settings.retryInterval)}
            options={RETRY_INTERVAL_MINUTES
              .filter((minutes) => minutes <= settings.checkInterval)
              .map((minutes) => ({ value: String(minutes), label: `${minutes} ${minutes === 1 ? 'minute' : 'minutes'}` }))}
            onChange={(value) => updateSettings({ retryInterval: Number(value) })}
          />

          <SettingsSelect
            label="Maximum check attempts"
            description="Failed checks in a row before a problem is confirmed and alerts are sent. More attempts means slower alerts and fewer false alarms."
            value={String(settings.maxCheckAttempts)}
            options={CHECK_ATTEMPT_OPTIONS.map((attempts) => ({ value: String(attempts), label: `${attempts} ${attempts === 1 ? 'attempt' : 'attempts'}` }))}
            onChange={(value) => updateSettings({ maxCheckAttempts: Number(value) })}
          />

          <SettingsToggle
            label="Maintenance Mode"
            description="Pause scheduled scans and checks, and show a notice to all users"
            enabled={
              settings.maintenanceMode
            }
            onChange={(enabled) =>
              updateSettings({
                maintenanceMode:
                  enabled,
              })
            }
          />

          <SettingsToggle
            label="Automatic Backups"
            description="Back up the system databases once a day (keeps the last 7)"
            enabled={
              settings.automaticBackups
            }
            onChange={(enabled) =>
              updateSettings({
                automaticBackups:
                  enabled,
              })
            }
          />

          <SettingsSelect
            label="System Log Retention"
            value={String(
              settings.logRetentionDays
            )}
            options={retentionOptions}
            onChange={(value) =>
              updateSettings({
                logRetentionDays:
                  Number(value),
              })
            }
          />

          <SettingsSelect
            label="Diagnostic History Retention"
            value={String(
              settings.diagnosticHistoryRetentionDays
            )}
            options={retentionOptions}
            onChange={(value) =>
              updateSettings({
                diagnosticHistoryRetentionDays:
                  Number(value),
              })
            }
          />

        </div>

        <SettingsActions
          hasChanges={hasUnsavedChanges}
          onSave={saveUnlessInvalid}
          onDiscard={discardChanges}
          isSaving={isSaving}
          saveError={saveError}
        />
        
      </SettingsCard>

      <NotificationPolicySettings />

      <SettingsCard
        title="Flap detection"
        description="Nagios marks a host or service as flapping when it keeps switching between states, and holds back its alerts until it settles."
      >
        <div className="grid gap-x-8 gap-y-7 lg:grid-cols-3">

          <SettingsToggle
            label="Flap detection"
            description="Turn off to stop Nagios flagging noisy devices as flapping. Flapping alerts then behave like normal ones."
            enabled={settings.flapDetectionEnabled}
            onChange={(enabled) => updateSettings({ flapDetectionEnabled: enabled })}
          />

          <FlapThresholdInput
            label="Low flap threshold"
            description={`Percent of state change below which flapping stops. Leave empty to use Nagios's own value (${NAGIOS_DEFAULT_LOW_FLAP}% by default).`}
            value={settings.flapLowThreshold}
            disabled={!settings.flapDetectionEnabled}
            onChange={(flapLowThreshold) => updateSettings({ flapLowThreshold })}
          />

          <FlapThresholdInput
            label="High flap threshold"
            description={`Percent of state change above which flapping starts. Leave empty to use Nagios's own value (${NAGIOS_DEFAULT_HIGH_FLAP}% by default).`}
            value={settings.flapHighThreshold}
            disabled={!settings.flapDetectionEnabled}
            onChange={(flapHighThreshold) => updateSettings({ flapHighThreshold })}
          />

        </div>

        {flapError && (
          <p role="alert" data-testid="flap-error" className="mt-4 text-sm text-red-500">{flapError}</p>
        )}

        <p className="mt-4 text-xs text-[var(--text-muted)]">Saved with the other system settings above.</p>
      </SettingsCard>

      <SettingsCard
        title="System Status"
        description="Overview of configuration states."
      >
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">

          <StatusCard
            icon={Wrench}
            title="Maintenance"
            status={
              settings.maintenanceMode
                ? 'Active'
                : 'Normal'
            }
            active={
              settings.maintenanceMode
            }
          />

          <StatusCard
            icon={Database}
            title="Automatic Backups"
            status={
              settings.automaticBackups
                ? 'Enabled'
                : 'Disabled'
            }
            active={
              settings.automaticBackups
            }
          />

          <StatusCard
            icon={HardDrive}
            title="Log Retention"
            status={`${settings.logRetentionDays} days`}
            active
          />

          <StatusCard
            icon={History}
            title="Diagnostic History"
            status={`${settings.diagnosticHistoryRetentionDays} days`}
            active
          />

        </div>
      </SettingsCard>

    </div>
  )
}

function StatusCard({ icon: Icon, title, status, active }: { icon: typeof Wrench; title: string; status: string; active: boolean }) {
  return (
    <div className="rounded-2xl bg-[var(--card-alt)] border border-[var(--border)] p-5">
      <Icon size={20} className="text-[#ffb100]" />
      <p className="mt-4 text-sm font-medium text-[var(--text)]">{title}</p>
      <div className="mt-2 flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${active ? 'bg-emerald-500' : 'bg-gray-400'}`} />
        <span className="text-xs text-[var(--text-muted)]">{status}</span>
      </div>
    </div>
  )
}