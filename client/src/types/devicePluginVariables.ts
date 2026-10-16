// Mirrors the per-device plugin variable routes in server/app/api/system/device_plugin_variables.py.
// Secret values are never part of a response: secrets_set only says whether each one is saved.

export type SnmpSecretName = 'auth_password' | 'priv_password'

export type DeviceVariablesResponse = {
  plugin: string
  // Plain values only, e.g. { protocol: '3', v3_user: 'monitor' }.
  variables: Record<string, string | number>
  secrets_set: Partial<Record<SnmpSecretName, boolean>>
  editable: string[]
  // SNMP only: whether the device has an SNMP port monitored (the form is shown only then).
  in_use: boolean | null
}

export type SnmpTestResult = {
  ok: boolean
  state: 'OK' | 'WARNING' | 'CRITICAL' | 'UNKNOWN'
  message: string
}

export type SnmpVersion = '' | '1' | '2c' | '3'
export type SnmpSecurityLevel = 'noAuthNoPriv' | 'authNoPriv' | 'authPriv'

// What the SNMP form edits. Passwords are typed values only: empty means "keep the saved one".
export type SnmpFormValues = {
  version: SnmpVersion
  community: string
  securityLevel: SnmpSecurityLevel | ''
  user: string
  authProtocol: string
  authPassword: string
  privProtocol: string
  privPassword: string
}
