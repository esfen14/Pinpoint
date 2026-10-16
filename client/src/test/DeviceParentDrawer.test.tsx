import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { StatusDetailDrawer } from '../components/device-inventory/StatusDetailDrawer'

const api = vi.hoisted(() => ({ detail: vi.fn(), topology: vi.fn(), save: vi.fn() }))
vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, apiGet: (path: string) => api.detail(path) }
})
vi.mock('../lib/topologyApi', () => ({ getTopology: () => api.topology(), setDeviceParents: (...args: unknown[]) => api.save(...args) }))
vi.mock('../contexts/CurrentUserContext', () => ({ useCurrentUser: () => ({ hasPermission: (name: string) => ['system.hosts.edit', 'system.network_health'].includes(name) }) }))
vi.mock('../hooks/useDisplayTime', () => ({ useDisplayTime: () => ({ formatDateTime: (value: string) => value }) }))
vi.mock('../components/device-inventory/FlapHistorySection', () => ({ FlapHistorySection: () => null }))

it('keeps the parent save confirmation visible while refreshing the inventory table', async () => {
  api.detail.mockResolvedValueOnce({ hostname: 'child', device_id: 1, state: 'UP', state_type: 'HARD', plugin_output: 'PING OK', check_latency: 0.01, check_execution_time: 0.01, perf_data: [], services: [] })
    .mockImplementation(() => new Promise(() => {}))
  api.topology.mockResolvedValue({ devices: [
    { id: 1, nagios_host_name: 'child', parent_device_ids: [], editable: true },
    { id: 2, nagios_host_name: 'router', parent_device_ids: [], editable: true, monitoring_state: 'monitored', ip_address: '10.77.0.3' },
  ], edges: [], suggested_gateway_id: null })
  api.save.mockResolvedValue({})
  const onChanged = vi.fn()
  render(<StatusDetailDrawer hostname="child" onClose={() => {}} onMonitoringChanged={onChanged} />)
  await userEvent.click(await screen.findByRole('checkbox', { name: /router/ }))
  await userEvent.click(screen.getByRole('button', { name: 'Save parents' }))
  await waitFor(() => expect(onChanged).toHaveBeenCalledOnce())
  expect(await screen.findByText('Parent devices saved.')).toBeVisible()
  expect(api.detail).toHaveBeenCalledTimes(1)
})
