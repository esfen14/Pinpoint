// Both provider choices require encrypted STARTTLS submission.
export type SmtpPreset = {
  provider: 'gmail' | 'custom'
  host: string
  port: number
  tls: 'starttls'
}

// The saved settings. The password is write-only: the server only says whether one is saved.
export type SmtpSettings = SmtpPreset & {
  username: string
  sender: string
  passwordSet: boolean
  configured: boolean
  version: number
  updatedAt: string | null
}

export type SmtpSettingsResponse = {
  settings: SmtpSettings
  presets: { gmail: SmtpPreset; custom: SmtpPreset }
  lastMailFailure: MailFailure | null
}

export type MailFailure = { time: string; reason: string }

export type SmtpSaveValues = {
  provider?: 'gmail' | 'custom'
  host?: string
  port?: number
  tls?: 'starttls'
  username: string
  sender: string
  // Sent exactly as typed. Left out to keep the saved one.
  password?: string
}

export type SmtpTestResult =
  | { ok: true; recipient: string }
  | {
      ok: false
      // auth_failed (rejected login), connect_failed (blocked port), host_not_found, tls_failed, rejected, send_failed.
      code: string
      message: string
      // Technically what happened and what to check, in plain English.
      explanation: string
      // Gmail's diagnostic text, with credentials redacted; empty for custom relays.
      details: string
    }
