// Pure rules of the "Check options" form of a monitored HTTP, HTTPS, POP3, IMAP, POP3S or IMAPS port:
// which fields each service has, how saved variables become form values, what is checked before
// sending and what is sent. The server applies the same rules (plugin_registry.validate_variable_value)
// and is the authority; this only stops a request that cannot succeed and names the field.
import type { DeviceVariablesResponse } from '../../types/devicePluginVariables'

export type CheckOptionName = 'expected_text' | 'expected_status' | 'virtual_host' | 'method'
export type CheckOptionValues = Record<CheckOptionName, string>

export type CheckOptionField = {
  name: CheckOptionName
  label: string
  help: string
  placeholder?: string
}

// The services whose check has options, and the title shown for each.
export const CHECK_OPTION_SERVICES: Record<string, string> = {
  http: 'HTTP',
  https: 'HTTPS',
  pop3: 'POP3',
  pop3s: 'POP3 over TLS',
  imap: 'IMAP',
  imaps: 'IMAP over TLS',
}

export const HTTP_METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']

const WEB_FIELDS: CheckOptionField[] = [
  {
    name: 'expected_text',
    label: 'Expected text',
    help: 'The page must contain this text, otherwise the check is CRITICAL.',
  },
  {
    name: 'expected_status',
    label: 'Expected status codes',
    help: 'HTTP status codes that count as healthy, separated by commas (200 or 200,301). Any other status is CRITICAL.',
    placeholder: '200,301',
  },
  {
    name: 'virtual_host',
    label: 'Virtual host',
    help: 'The host name sent to the web server. The check still connects to the device address.',
    placeholder: 'www.example.com',
  },
  {
    name: 'method',
    label: 'Request method',
    help: 'The HTTP method of the request. Leave on Default to use the standard request.',
  },
]

const GREETING_DEFAULTS: Record<string, string> = { pop3: '+OK', pop3s: '+OK', imap: '* OK', imaps: '* OK' }

// A check can have options when its service is one of CHECK_OPTION_SERVICES.
export function hasCheckOptions(plugin: string | null | undefined): plugin is string {
  return !!plugin && plugin in CHECK_OPTION_SERVICES
}

export function fieldsFor(plugin: string): CheckOptionField[] {
  if (plugin === 'http' || plugin === 'https') return WEB_FIELDS
  return [
    {
      name: 'expected_text',
      label: 'Expected greeting',
      help: 'The text the server must start its reply with. Another reply is CRITICAL.',
      placeholder: GREETING_DEFAULTS[plugin],
    },
  ]
}

export const EMPTY_VALUES: CheckOptionValues = { expected_text: '', expected_status: '', virtual_host: '', method: '' }

export function valuesFromSaved(saved: DeviceVariablesResponse, plugin: string): CheckOptionValues {
  const values = { ...EMPTY_VALUES }
  for (const { name } of fieldsFor(plugin)) {
    const value = saved.variables[name]
    if (value != null) values[name] = String(value)
  }
  return values
}

const MAX_LENGTH = 128
const FORBIDDEN_CHARACTERS = "'\"`!$;\\"
// The server refuses these and every control character (line breaks, NUL).
const isForbidden = (text: string) => [...text].some((character) => FORBIDDEN_CHARACTERS.includes(character) || character.charCodeAt(0) < 32)
const STATUS_PATTERN = /^[1-5][0-9]{2}(,[1-5][0-9]{2}){0,9}$/
const HOST_PATTERN = /^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$/

// The first problem that would make the server refuse the form, as { field, message }, or null.
export function formProblem(plugin: string, values: CheckOptionValues): { field: CheckOptionName; message: string } | null {
  for (const { name, label } of fieldsFor(plugin)) {
    const value = values[name].trim()
    if (!value) continue
    if (value.length > MAX_LENGTH) return { field: name, message: `${label} is too long (at most ${MAX_LENGTH} characters).` }
    if (isForbidden(value)) return { field: name, message: `${label} cannot contain quotes, ! $ ; \` or a backslash.` }
    if (name === 'expected_status' && !STATUS_PATTERN.test(value)) {
      return { field: name, message: 'Expected status codes must be HTTP status codes from 100 to 599, separated by commas.' }
    }
    if (name === 'virtual_host' && !HOST_PATTERN.test(value)) {
      return { field: name, message: 'Virtual host must be a host name: letters, digits, "." and "-".' }
    }
    if (name === 'method' && !HTTP_METHODS.includes(value)) {
      return { field: name, message: `Request method must be one of ${HTTP_METHODS.join(', ')}.` }
    }
  }
  return null
}

// The variables to send: the form's non-empty fields plus the saved values the form does not own,
// because the server replaces the whole override.
export function variablesFromForm(plugin: string, values: CheckOptionValues, saved: DeviceVariablesResponse | null): Record<string, string | number> {
  const owned = new Set<string>(fieldsFor(plugin).map((field) => field.name))
  const result: Record<string, string | number> = {}
  for (const [key, value] of Object.entries(saved?.variables ?? {})) {
    if (!owned.has(key)) result[key] = value
  }
  for (const { name } of fieldsFor(plugin)) {
    const value = values[name].trim()
    if (value) result[name] = value
  }
  return result
}

// The default a blank field falls back to, for the hint under the field; null when there is none.
export function defaultHint(plugin: string, name: CheckOptionName): string | null {
  if (name === 'expected_text' && plugin in GREETING_DEFAULTS) return GREETING_DEFAULTS[plugin]
  return null
}
