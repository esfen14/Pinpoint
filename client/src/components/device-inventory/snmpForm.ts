// Pure rules of the SNMP form: how saved variables become form values, which fields a security level
// needs, and what is sent. The server applies the same rules and is the authority; this only stops a
// request that cannot succeed and names the missing field.
import type {
  DeviceVariablesResponse,
  SnmpFormValues,
  SnmpSecretName,
  SnmpSecurityLevel,
  SnmpVersion,
} from '../../types/devicePluginVariables'

export const SECURITY_LEVELS: { value: SnmpSecurityLevel; label: string }[] = [
  { value: 'noAuthNoPriv', label: 'No authentication, no privacy' },
  { value: 'authNoPriv', label: 'Authentication only' },
  { value: 'authPriv', label: 'Authentication and privacy' },
]
export const AUTH_PROTOCOLS = ['SHA', 'MD5']
export const PRIV_PROTOCOLS = ['AES', 'DES']

// Variables this form owns; anything else saved for the device (a port, a threshold) is sent back unchanged.
const FORM_KEYS = ['protocol', 'community', 'security_level', 'v3_user', 'auth_protocol', 'priv_protocol']

export const EMPTY_FORM: SnmpFormValues = {
  version: '', community: '', securityLevel: '', user: '',
  authProtocol: 'SHA', authPassword: '', privProtocol: 'AES', privPassword: '',
}

export function formFromSaved(saved: DeviceVariablesResponse): SnmpFormValues {
  const text = (key: string) => (saved.variables[key] == null ? '' : String(saved.variables[key]))
  return {
    version: (['1', '2c', '3'].includes(text('protocol')) ? text('protocol') : '') as SnmpVersion,
    community: text('community'),
    securityLevel: (text('security_level') as SnmpSecurityLevel) || '',
    user: text('v3_user'),
    authProtocol: text('auth_protocol') || EMPTY_FORM.authProtocol,
    authPassword: '',
    privProtocol: text('priv_protocol') || EMPTY_FORM.privProtocol,
    privPassword: '',
  }
}

export const needsAuth = (form: SnmpFormValues) => form.version === '3' && (form.securityLevel === 'authNoPriv' || form.securityLevel === 'authPriv')
export const needsPriv = (form: SnmpFormValues) => form.version === '3' && form.securityLevel === 'authPriv'

// The first problem that would make the server refuse the form, or null. A password field left empty is
// fine while a saved one is kept (secretsKept).
export function formProblem(form: SnmpFormValues, secretsKept: Partial<Record<SnmpSecretName, boolean>>): string | null {
  if (form.version !== '3') return null
  if (!form.securityLevel) return 'Choose a security level.'
  if (!form.user.trim()) return 'Enter the SNMP v3 user name.'
  if (needsAuth(form)) {
    if (!form.authProtocol) return 'Choose an authentication protocol.'
    if (!form.authPassword && !secretsKept.auth_password) return 'Enter the authentication password.'
  }
  if (needsPriv(form)) {
    if (!form.privProtocol) return 'Choose a privacy protocol.'
    if (!form.privPassword && !secretsKept.priv_password) return 'Enter the privacy password.'
  }
  return null
}

// The variables to send: the form's fields for the chosen version, plus saved values the form does not own.
export function variablesFromForm(form: SnmpFormValues, saved: DeviceVariablesResponse | null): Record<string, string | number> {
  const result: Record<string, string | number> = {}
  for (const [key, value] of Object.entries(saved?.variables ?? {})) {
    if (!FORM_KEYS.includes(key)) result[key] = value
  }
  if (form.version) result.protocol = form.version
  if (form.version !== '3') {
    if (form.community.trim()) result.community = form.community.trim()
    return result
  }
  result.security_level = form.securityLevel
  result.v3_user = form.user.trim()
  if (needsAuth(form)) {
    result.auth_protocol = form.authProtocol
    if (form.authPassword) result.auth_password = form.authPassword
  }
  if (needsPriv(form)) {
    result.priv_protocol = form.privProtocol
    if (form.privPassword) result.priv_password = form.privPassword
  }
  return result
}
