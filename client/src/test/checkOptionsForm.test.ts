import { describe, expect, it } from 'vitest'
import {
  CHECK_OPTION_SERVICES,
  EMPTY_VALUES,
  fieldsFor,
  formProblem,
  hasCheckOptions,
  valuesFromSaved,
  variablesFromForm,
} from '../components/device-inventory/checkOptionsForm'
import type { DeviceVariablesResponse } from '../types/devicePluginVariables'

const saved = (variables: DeviceVariablesResponse['variables'] = {}): DeviceVariablesResponse => ({
  plugin: 'http', variables, secrets_set: {}, editable: [], in_use: null,
})

describe('which services have check options', () => {
  it.each(Object.keys(CHECK_OPTION_SERVICES))('%s has options', (plugin) => {
    expect(hasCheckOptions(plugin)).toBe(true)
  })

  it.each(['ssh', 'tcp', 'snmp', 'ncpa', '', null, undefined])('%s has none', (plugin) => {
    expect(hasCheckOptions(plugin)).toBe(false)
  })

  it('offers four fields for web checks and the greeting for mail checks', () => {
    expect(fieldsFor('http').map((f) => f.name)).toEqual(['expected_text', 'expected_status', 'virtual_host', 'method'])
    expect(fieldsFor('https')).toEqual(fieldsFor('http'))
    for (const plugin of ['pop3', 'imap', 'pop3s', 'imaps']) expect(fieldsFor(plugin).map((f) => f.name)).toEqual(['expected_text'])
  })
})

describe('formProblem', () => {
  const check = (plugin: string, values: Partial<typeof EMPTY_VALUES>) => formProblem(plugin, { ...EMPTY_VALUES, ...values })

  it('accepts an empty form and valid values', () => {
    expect(check('http', {})).toBeNull()
    expect(check('http', { expected_text: 'Welcome (v2)', expected_status: '200,301', virtual_host: 'www.example.com', method: 'HEAD' })).toBeNull()
    expect(check('imap', { expected_text: '* OK Dovecot' })).toBeNull()
  })

  it.each(["it's", 'a;b', 'x$y', 'a!b', 'a\\b', 'a`b', 'a"b'])('refuses forbidden characters in %s', (text) => {
    expect(check('http', { expected_text: text })?.field).toBe('expected_text')
    expect(check('pop3', { expected_text: text })?.field).toBe('expected_text')
  })

  it.each(['98', '600', '20x', '200,', '200;404', 'ok', '200 301'])('refuses the status %s', (status) => {
    expect(check('http', { expected_status: status })?.field).toBe('expected_status')
  })

  it.each(['bad host', '-x', 'host/path', 'a_b'])('refuses the virtual host %s', (host) => {
    expect(check('https', { virtual_host: host })?.field).toBe('virtual_host')
  })

  it('refuses an unknown method and an over-long value', () => {
    expect(check('http', { method: 'FETCH' })?.field).toBe('method')
    expect(check('http', { expected_text: 'x'.repeat(129) })?.field).toBe('expected_text')
  })

  it('ignores fields the service does not have', () => {
    expect(check('imap', { expected_status: 'nonsense', virtual_host: 'bad host' })).toBeNull()
  })
})

describe('values and variables', () => {
  it('reads saved variables into the form', () => {
    const values = valuesFromSaved(saved({ expected_text: 'ok', method: 'HEAD', warning: '2' }), 'http')
    expect(values).toEqual({ expected_text: 'ok', expected_status: '', virtual_host: '', method: 'HEAD' })
  })

  it('sends only non-empty fields and keeps saved values it does not own', () => {
    const body = variablesFromForm(
      'http',
      { ...EMPTY_VALUES, expected_text: ' ok ', expected_status: '200' },
      saved({ expected_text: 'old', method: 'HEAD', warning: '2', port: 8080 }),
    )
    expect(body).toEqual({ warning: '2', port: 8080, expected_text: 'ok', expected_status: '200' })
  })

  it('sends an empty override when everything is cleared', () => {
    expect(variablesFromForm('pop3', EMPTY_VALUES, saved({ expected_text: '+OK' }))).toEqual({})
  })
})
