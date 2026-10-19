import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { PluginsPage } from '../pages/PluginsPage'
import { monitoringLabel } from '../components/plugin-manager/PluginInventoryTable'
import type { PluginListItem } from '../types/plugin'

function plugin(overrides: Partial<PluginListItem> = {}): PluginListItem {
  return {
    id: 1, name: 'check_ssh', display_name: null, description: 'Checks SSH.', category: null, type: 'Nagios',
    source: 'Baseline (ISO)', status: 'Ready', current_version: '2.4.12', updated_at: '2026-09-26T09:00:00+00:00',
    service_driven: true, monitoring_usage: { services: 0, devices: 0 },
    ...overrides,
  }
}

const emptyList = { items: [], page: 1, per_page: 10, pages: 1, total: 0, has_next: false, has_prev: false }

const api = vi.hoisted(() => ({
  getPluginInventory: vi.fn(),
  getPluginSummary: vi.fn(),
  getPluginScanStatus: vi.fn(),
  startPluginScan: vi.fn(),
}))

vi.mock('../lib/pluginApi', () => api)

// The drawer loads a lot of its own data; stub it to just show which plugin opened.
vi.mock('../components/plugin-manager/PluginDetailsDrawer', () => ({
  PluginDetailsDrawer: ({ pluginId }: { pluginId: number }) => <div>Details for plugin {pluginId}</div>,
}))

const summary = (overrides = {}) => ({
  installed_plugins: 5, active_capabilities: 1, enabled_plugins: 1,
  validation_issues: 0, ...overrides,
})

describe('PluginsPage', () => {
  beforeEach(() => {
    Object.values(api).forEach((fn) => fn.mockReset())
    api.getPluginSummary.mockResolvedValue(summary())
    api.getPluginScanStatus.mockResolvedValue(null)
    api.getPluginInventory.mockResolvedValue({
      ...emptyList,
      items: [
        plugin({ id: 1, name: 'check_ssh', status: 'Active', monitoring_usage: { services: 12, devices: 5 } }),
        plugin({ id: 2, name: 'check_ping', service_driven: false, custom_checks: { class: 'custom', supported: true, target: 'device', note: null, fields: [] } }),
        plugin({ id: 3, name: 'check_http', status: 'Enabled' }),
        plugin({ id: 4, name: 'check_snmp', status: 'Ready' }),
        plugin({ id: 5, name: 'check_dns', status: 'Active', monitoring_usage: { services: 1, devices: 1 } }),
      ],
      total: 5,
    })
  })

  it('is one plugin inventory with category tabs and no Currently Running tab', async () => {
    render(<PluginsPage />)

    expect(await screen.findByText('check_ssh')).toBeInTheDocument()
    expect(screen.getAllByRole('tab').map((t) => t.textContent)).toEqual([
      'All',
      'Network Services',
      'Device Availability',
      'Network Protocols',
      'Servers',
      'Application',
      'Other',
    ])
    expect(screen.queryByText(/currently running/i)).not.toBeInTheDocument()
    expect(screen.getByText('Plugin Inventory')).toBeInTheDocument()
  })

  it('shows only the three supported summary cards, including with legacy response fields', async () => {
    api.getPluginSummary.mockResolvedValue(summary({
      installed_plugins: 8, active_capabilities: 3, validation_issues: 2,
      custom_plugins: 4, updates_available: 5,
    }))
    render(<PluginsPage />)

    for (const [title, value] of [
      ['Installed Plugins', '8'],
      ['Active Capabilities', '3'],
      ['Validation Issues', '2'],
    ]) {
      const label = await screen.findByText(title)
      expect(await within(label.parentElement!.parentElement!).findByText(value)).toBeInTheDocument()
    }
    expect(screen.queryByText('Custom Plugins')).not.toBeInTheDocument()
    expect(screen.queryByText('Updates Available')).not.toBeInTheDocument()
  })

  it('shows how much each plugin covers in a Monitoring column', async () => {
    render(<PluginsPage />)

    const row = (name: string) => screen.getByText(name).closest('tr')!
    await screen.findByText('check_ssh')

    expect(screen.getByRole('columnheader', { name: 'Monitoring' })).toBeInTheDocument()
    expect(within(row('check_ssh')).getByText('12 services on 5 devices')).toBeInTheDocument()
    expect(within(row('check_dns')).getByText('1 service on 1 device')).toBeInTheDocument()
    expect(within(row('check_ping')).getByText('No checks added yet')).toBeInTheDocument()
    expect(within(row('check_ping')).getByText('Add device check')).toBeInTheDocument()
    expect(within(row('check_http')).getByText('Automatic monitoring')).toBeInTheDocument()
    expect(within(row('check_http')).getByText('No matching services yet')).toBeInTheDocument()
    expect(within(row('check_snmp')).getByText('—')).toBeInTheDocument()
  })

  it('warns that nothing is monitored while no plugin is enabled', async () => {
    api.getPluginSummary.mockResolvedValue(summary({ enabled_plugins: 0, active_capabilities: 0 }))
    render(<PluginsPage />)

    expect(await screen.findByText(/No plugins enabled, so no network services are monitored/)).toBeInTheDocument()
  })

  it('shows no warning once a plugin is enabled', async () => {
    render(<PluginsPage />)

    await screen.findByText('check_ssh')
    expect(screen.queryByText(/No plugins enabled/)).not.toBeInTheDocument()
  })

  it('does not flash the warning before the summary has loaded', async () => {
    api.getPluginSummary.mockReturnValue(new Promise(() => {}))
    render(<PluginsPage />)

    await screen.findByText('check_ssh')
    expect(screen.queryByText(/No plugins enabled/)).not.toBeInTheDocument()
  })

  it('opens the plugin details from a row', async () => {
    render(<PluginsPage />)

    fireEvent.click(await screen.findByText('check_ssh'))

    expect(screen.getByText('Details for plugin 1')).toBeInTheDocument()
  })

  it('shows an error when the inventory cannot be loaded', async () => {
    api.getPluginInventory.mockRejectedValue(new Error('Server unavailable'))
    render(<PluginsPage />)

    expect(await screen.findByText('Server unavailable')).toBeInTheDocument()
  })
})

describe('monitoringLabel', () => {
  it.each([
    [plugin({ service_driven: false, custom_checks: { class: 'stock', supported: false, target: null, note: null, fields: [] } }), '—'],
    [plugin({ service_driven: false, custom_checks: { class: 'server', supported: true, target: 'server', note: null, fields: [] } }), 'No checks added yet'],
    [plugin({ monitoring_usage: { services: 1, devices: 1 } }), '1 service on 1 device'],
    [plugin({ monitoring_usage: { services: 3, devices: 2 } }), '3 services on 2 devices'],
    [plugin({ status: 'Enabled' }), 'No matching services yet'],
    [plugin({ status: 'Active' }), 'No matching services yet'],
    [plugin({ status: 'Disabled' }), '—'],
    [plugin({ status: 'Ready' }), '—'],
  ])('describes %#', (item, expected) => {
    expect(monitoringLabel(item)).toBe(expected)
  })
})
