import { useEffect, useState } from 'react'
import { AlertTriangle, ExternalLink, Loader2, Send } from 'lucide-react'

import { SettingsCard } from './SettingsCard'
import { SettingsActions } from './SettingsActions'
import { errorMessage } from '../../lib/api'
import { getSmtpSettings, saveSmtpSettings, sendTestEmail } from '../../lib/smtpSettingsApi'
import { useDisplayTime } from '../../hooks/useDisplayTime'
import type { MailFailure, SmtpPreset, SmtpSettings, SmtpTestResult } from '../../types/smtpSettings'

const HOST_PATTERN = /^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$/
const MAIL_POLL_MS = 30000

const APP_PASSWORDS_URL = 'https://myaccount.google.com/apppasswords'

const inputClass =
  'h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-sm text-[var(--text)] outline-none transition duration-200 focus:border-[#ffb100] disabled:cursor-not-allowed disabled:opacity-60'

interface FormState {
  provider: 'gmail' | 'custom'
  host: string
  port: string
  tls: 'starttls'
  username: string
  sender: string
  // Only what was typed this session; the saved password is never loaded.
  password: string
}

function toForm(settings: SmtpSettings): FormState {
  return { provider: settings.provider, host: settings.host, port: String(settings.port), tls: settings.tls, username: settings.username, sender: settings.sender, password: '' }
}

export function EmailSettings() {
  const [saved, setSaved] = useState<SmtpSettings | null>(null)
  const [preset, setPreset] = useState<SmtpPreset | null>(null)
  const [form, setForm] = useState<FormState>({ provider: 'gmail', host: '', port: '587', tls: 'starttls', username: '', sender: '', password: '' })
  // The sender follows the username until the admin types a different one.
  const [senderEdited, setSenderEdited] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<SmtpTestResult | null>(null)
  const [testError, setTestError] = useState<string | null>(null)

  const [lastMailFailure, setLastMailFailure] = useState<MailFailure | null>(null)
  const [refreshError, setRefreshError] = useState<string | null>(null)
  const { formatDateTime } = useDisplayTime()

  useEffect(() => {
    let cancelled = false
    let initialized = false
    let timer: ReturnType<typeof setTimeout>
    const refresh = () => {
      getSmtpSettings()
        .then((data) => {
          if (cancelled) return
          setLastMailFailure(data.lastMailFailure ?? null)
          setRefreshError(null)
          if (!initialized) {
            initialized = true
            setSaved(data.settings)
            setPreset(data.presets.gmail)
            setForm(toForm(data.settings))
            setSenderEdited(data.settings.sender !== '' && data.settings.sender !== data.settings.username)
          }
        })
        .catch((err) => {
          if (cancelled) return
          if (initialized) setRefreshError(errorMessage(err, 'Unable to refresh mail delivery status.'))
          else setLoadError(errorMessage(err, 'Unable to load email settings.'))
        })
        .finally(() => { if (!cancelled && initialized) timer = setTimeout(refresh, MAIL_POLL_MS) })
    }
    refresh()
    return () => { cancelled = true; clearTimeout(timer) }
  }, [])

  if (loadError) {
    return (
      <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-500">{loadError}</div>
    )
  }
  if (!saved || !preset) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
        <Loader2 size={15} className="animate-spin" /> Loading email settings...
      </div>
    )
  }

  const isGmail = form.provider === 'gmail'
  const senderDiffers = form.sender.trim() !== '' && form.sender.trim() !== form.username.trim()
  const hasChanges =
    form.provider !== saved.provider || form.host !== saved.host || form.port !== String(saved.port) ||
    form.username !== saved.username || form.sender !== saved.sender || form.password !== ''
  const canSave = form.username.trim() !== '' && (saved.passwordSet || form.password !== '')

  const setUsername = (username: string) =>
    setForm((current) => ({ ...current, username, sender: senderEdited ? current.sender : username }))

  const discard = () => {
    setForm(toForm(saved))
    setSenderEdited(saved.sender !== '' && saved.sender !== saved.username)
    setSaveError(null)
  }

  const save = async () => {
    if (!canSave) {
      setSaveError(isGmail ? (saved.passwordSet ? 'Enter the Gmail address.' : 'Enter the Gmail address and the app password.') : 'Enter the relay username and password.')
      return
    }
    if (!isGmail) {
      if (!HOST_PATTERN.test(form.host)) {
        setSaveError('The host must be a host name or IPv4 address, at most 253 characters.')
        return
      }
      if (!/^\d+$/.test(form.port) || Number(form.port) < 1 || Number(form.port) > 65535) {
        setSaveError('The port must be a whole number from 1 to 65535.')
        return
      }
      if (form.tls !== 'starttls') {
        setSaveError('Only STARTTLS is supported.')
        return
      }
    }
    setIsSaving(true)
    setSaveError(null)
    try {
      const updated = await saveSmtpSettings(
        {
          ...(!isGmail ? { provider: 'custom' as const, host: form.host, port: Number(form.port), tls: form.tls } : {}),
          username: form.username.trim(),
          sender: form.sender.trim() || form.username.trim(),
          // As typed or pasted, spaces included. Left out when blank so the saved one is kept.
          ...(form.password !== '' ? { password: form.password } : {}),
        },
        saved.version,
      )
      setSaved(updated)
      setForm(toForm(updated))
      setTestResult(null)
    } catch (err) {
      setSaveError(errorMessage(err, 'Unable to save email settings.'))
    } finally {
      setIsSaving(false)
    }
  }

  const runTest = async () => {
    setIsTesting(true)
    setTestResult(null)
    setTestError(null)
    try {
      setTestResult(await sendTestEmail())
    } catch (err) {
      setTestError(errorMessage(err, 'Unable to send the test email.'))
    } finally {
      setIsTesting(false)
    }
  }

  return (
    <div className="space-y-6">
      {lastMailFailure && (
        <div role="alert" className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-[var(--text)]">
          <p className="font-medium">Last notification failure: {formatDateTime(lastMailFailure.time)}</p>
          <p>{lastMailFailure.reason}</p>
          <p className="mt-1 text-xs">This records a past failure; a successful test does not clear it. Save any changes before testing.</p>
          <a href="#smtp-test-email" className="mt-2 inline-block text-[#ffb100] hover:underline">Test email settings</a>
        </div>
      )}
      {refreshError && <p role="alert" className="text-sm text-red-500">{refreshError}</p>}
      <SettingsCard
        title="Email (SMTP)"
        description={isGmail
          ? 'The Gmail account PinPoint sends notification email through. These settings are shared by the whole system: every alert email is sent from this one account, whoever is signed in.'
          : 'The SMTP relay PinPoint sends notification email through. These settings are shared by the whole system.'}
      >
        <div className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block text-sm text-[var(--text)]">
              Provider
              <select aria-label="Provider" value={form.provider} disabled={isSaving}
                className={`${inputClass} mt-1`}
                onChange={(e) => {
                  const provider = e.target.value as FormState['provider']
                  setForm({ ...form, provider, host: provider === 'gmail' ? preset.host : '', port: '587', tls: 'starttls' })
                  setSaveError(null)
                }}>
                <option value="gmail">Gmail</option>
                <option value="custom">Other SMTP relay</option>
              </select>
            </label>
            <label className="block text-sm text-[var(--text)]">
              Host
              <input aria-label="Host" value={form.host} disabled={isGmail || isSaving} onChange={(e) => setForm({ ...form, host: e.target.value })} className={`${inputClass} mt-1`} />
            </label>
            <div className="grid grid-cols-2 gap-4">
              <label className="block text-sm text-[var(--text)]">
                Port
                <input aria-label="Port" value={form.port} disabled={isGmail || isSaving} inputMode="numeric" onChange={(e) => setForm({ ...form, port: e.target.value })} className={`${inputClass} mt-1`} />
              </label>
              <label className="block text-sm text-[var(--text)]">
                Security
                <input aria-label="Security" value="STARTTLS" readOnly disabled className={`${inputClass} mt-1`} />
              </label>
            </div>
          </div>

          <label className="block text-sm text-[var(--text)]">
            {isGmail ? 'Username (full Gmail address)' : 'Username'}
            <input
              aria-label="Username"
              type={isGmail ? "email" : "text"}
              value={form.username}
              placeholder={isGmail ? 'you@gmail.com' : 'Relay username'}
              autoComplete="off"
              onChange={(e) => setUsername(e.target.value)}
              className={`${inputClass} mt-1`}
            />
            <span className="mt-1.5 block text-xs text-[var(--text-muted)]">
              {isGmail ? 'The Gmail account PinPoint signs in to, together with the app password.' : 'The account PinPoint signs in to on the SMTP relay.'}
            </span>
          </label>

          <div>
            <label className="block text-sm text-[var(--text)]">
              Sender
              <input
                id="smtp-sender"
                aria-label="Sender"
                type="email"
                value={form.sender}
                placeholder={isGmail ? 'you@gmail.com' : 'alerts@example.org'}
                autoComplete="off"
                onChange={(e) => {
                  setSenderEdited(true)
                  setForm({ ...form, sender: e.target.value })
                }}
                className={inputClass}
              />
              <span className="mt-1.5 block text-xs text-[var(--text-muted)]">
                {isGmail ? 'The "From" address shown on alert emails. Gmail always uses the account above, so leave it as is.'
                  : 'The From email address your relay permits this account to use.'}
              </span>
            </label>
            {isGmail && senderDiffers && (
              <p role="alert" className="mt-1.5 flex items-start gap-1.5 text-xs text-amber-600 dark:text-amber-300">
                <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                Gmail rewrites the From address to the account you sign in with, so this sender will not be kept.
              </p>
            )}
          </div>

          <div>
            {isGmail ? <div className="rounded-xl border border-[var(--border)] bg-[var(--hover)] p-3 text-xs text-[var(--text-muted)]">
              <p>
                Gmail does not accept your normal password here. Use a 16-character app password. You need 2-Step
                Verification turned on for the Google account to create one: Google Account → Security → App passwords.
              </p>
              <a
                href={APP_PASSWORDS_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1.5 inline-flex items-center gap-1 text-[#ffb100] hover:underline"
              >
                Create an app password <ExternalLink size={12} />
              </a>
            </div> : <p className="text-xs text-[var(--text-muted)]">
              Use your provider's SMTP submission host, port and password or app token. Only STARTTLS is supported.
              Implicit TLS (usually port 465), unencrypted SMTP and OAuth are unavailable. The server certificate must be trusted by this appliance.
            </p>}
            <label className="mt-3 block text-sm text-[var(--text)]">
              {isGmail ? 'App password' : 'Password'}
              <input
                aria-label={isGmail ? 'App password' : 'Password'}
                type="password"
                value={form.password}
                placeholder={isGmail ? 'xxxx xxxx xxxx xxxx' : 'Relay password or app token'}
                autoComplete="new-password"
                spellCheck={false}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className={`${inputClass} mt-1`}
              />
            </label>
            <p className="mt-1.5 text-xs text-[var(--text-muted)]">
              {saved.passwordSet
                ? (isGmail ? 'An app password is saved. Leave this blank to keep it. ' : 'A password is saved. Leave this blank to keep it. ')
                : ''}
              Paste it with or without spaces; it is used exactly as entered.
            </p>
          </div>

          {isGmail && <p className="text-xs text-[var(--text-muted)]">
            Gmail limits personal accounts to about 500 messages a day, and the appliance needs outbound access to
            smtp.gmail.com on port 587.
          </p>}
        </div>

        <SettingsActions
          hasChanges={hasChanges}
          onSave={save}
          onDiscard={discard}
          isSaving={isSaving}
          saveError={saveError}
        />
      </SettingsCard>

      <div id="smtp-test-email" />
      <SettingsCard
        title="Test email"
        description="Sends a message to your own address with the saved settings. Save any changes first."
      >
        <button
          type="button"
          onClick={runTest}
          disabled={!saved.configured || hasChanges || isTesting}
          className="flex items-center gap-2 rounded-xl border border-[var(--border)] px-4 py-2.5 text-sm text-[var(--text)] transition hover:bg-[var(--hover)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isTesting ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
          Send test email
        </button>

        {testError && <p role="alert" className="mt-3 text-sm text-red-500">{testError}</p>}

        {testResult?.ok && (
          <p role="status" className="mt-3 text-sm text-emerald-500">
            Test email sent to {testResult.recipient}. Did it arrive? Check that inbox (and spam). That is what
            confirms the address is yours; the app password only proves the login works.
          </p>
        )}

        {testResult && !testResult.ok && (
          <div role="alert" className="mt-3 text-sm text-red-500">
            <p>{testResult.message}</p>
            {(testResult.explanation || testResult.details) && (
              <details className="mt-1.5 text-xs text-[var(--text-muted)]">
                <summary className="cursor-pointer">Details</summary>
                {testResult.explanation && <p className="mt-1">{testResult.explanation}</p>}
                {testResult.details && (
                  <>
                    <p className="mt-2 font-medium">Server response</p>
                    <pre className="mt-0.5 whitespace-pre-wrap break-words">{testResult.details}</pre>
                  </>
                )}
              </details>
            )}
          </div>
        )}
      </SettingsCard>
    </div>
  )
}
