import { describe, it, expect } from 'vitest'
import { pluginUsage } from '../lib/pluginUsage'
import type { PluginCustomSupport } from '../types/plugin'

const support = (overrides: Partial<PluginCustomSupport> = {}): PluginCustomSupport => ({
  class: 'custom', supported: true, target: 'device', note: null, fields: [], ...overrides,
})

describe('pluginUsage', () => {
  it('check_http is automatic monitoring', () => {
    const usage = pluginUsage({ name: 'check_http', service_driven: true })!
    expect(usage.kind).toBe('automatic')
    expect(usage.label).toBe('Automatic monitoring')
    expect(usage.nextStep).toMatch(/Enable the plugin to attach monitoring to matching discovered ports/)
  })

  it('check_ping is a device check', () => {
    const usage = pluginUsage({ name: 'check_ping', service_driven: false, custom_checks: support() })!
    expect(usage.label).toBe('Add device check')
    expect(usage.nextStep).toMatch(/Custom checks → Add check, choose a device/)
  })

  it('check_file_age is a server check that runs as the Nagios user', () => {
    const usage = pluginUsage({ name: 'check_file_age', service_driven: false, custom_checks: support({ class: 'server', target: 'server' }) })!
    expect(usage.label).toBe('Add server check')
    expect(usage.nextStep).toMatch(/Server checks → Add check/)
    expect(usage.nextStep).toMatch(/Nagios server as the Nagios user/)
  })

  it('check_load is managed by Nagios, with or without capability metadata', () => {
    for (const custom_checks of [undefined, support({ class: 'stock', supported: false, target: null })]) {
      const usage = pluginUsage({ name: 'check_load', service_driven: false, custom_checks })!
      expect(usage.label).toBe('Managed by Nagios')
      expect(usage.nextStep).toMatch(/Plugin Manager does not configure them/)
    }
  })

  it('check_dbi is not supported yet, for its password', () => {
    const usage = pluginUsage({
      name: 'check_dbi', service_driven: false,
      custom_checks: support({ class: 'credentials', supported: false, target: null, note: 'Its password cannot be passed to the plugin yet.' }),
    })!
    expect(usage.label).toBe('Not supported yet')
    expect(usage.summary).toBe('Its password cannot be passed to the plugin yet.')
  })

  it('check_ntp names its replacement', () => {
    const note = 'Replaced by check_ntp_time, which discovery already uses for NTP ports.'
    const usage = pluginUsage({ name: 'check_ntp', service_driven: false, custom_checks: support({ class: 'replaced', supported: false, target: null, note }) })!
    expect(usage.label).toBe('Not supported yet')
    expect(usage.summary).toBe(note)
  })

  it('says the password of a device check is write-only (check_disk_smb)', () => {
    const fields = [{ name: 'password', flag: '-p', label: 'SMB password', required: false, placeholder: '', secret: true }]
    const usage = pluginUsage({ name: 'check_disk_smb', service_driven: false, custom_checks: support({ fields }) })!
    expect(usage.label).toBe('Add device check')
    expect(usage.nextStep).toMatch(/masked and write-only/)
  })

  it('has no category when the backend gave no metadata', () => {
    expect(pluginUsage({ name: 'check_custom', service_driven: false })).toBeNull()
  })
})
