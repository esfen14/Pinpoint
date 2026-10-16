import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { CheckOptionsDialog } from '../components/device-inventory/CheckOptionsDialog'
import { DevicePortsSection } from '../components/device-inventory/DevicePortsSection'
import type { DeviceVariablesResponse } from '../types/devicePluginVariables'
import { port, ports } from './devicePortsFixtures'

const api = vi.hoisted(() => ({
  getDevicePluginVariables: vi.fn(), saveDevicePluginVariables: vi.fn(), resetDevicePluginVariables: vi.fn(),
}))
vi.mock('../lib/devicePluginVariablesApi', () => api)

const portsApi = vi.hoisted(() => ({ getDevicePorts: vi.fn(), changePort: vi.fn() }))
vi.mock('../lib/devicePortsApi', () => portsApi)

const permissions = vi.hoisted(() => ({ granted: new Set<string>() }))
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: null, isLoading: false, hasPermission: (name: string) => permissions.granted.has(name) }),
}))

const WEB_EDITABLE = ['port', 'url', 'warning', 'critical', 'expected_text', 'expected_status', 'virtual_host', 'method']

const saved = (plugin: string, variables: DeviceVariablesResponse['variables'] = {}): DeviceVariablesResponse => ({
  plugin, variables, secrets_set: {}, editable: WEB_EDITABLE, in_use: null,
})

function renderDialog(plugin = 'http', canEdit = true, onClose = vi.fn()) {
  render(<CheckOptionsDialog deviceId={4} hostname="web-01" plugin={plugin} canEdit={canEdit} onClose={onClose} />)
  return onClose
}

const type = (label: string | RegExp, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } })

beforeEach(() => {
  api.getDevicePluginVariables.mockReset().mockImplementation((_id: number, plugin: string) => Promise.resolve(saved(plugin)))
  api.saveDevicePluginVariables.mockReset().mockImplementation((_id, variables, _clear, plugin) => Promise.resolve(saved(plugin, variables)))
  api.resetDevicePluginVariables.mockReset().mockImplementation((_id: number, plugin: string) => Promise.resolve(saved(plugin)))
  portsApi.getDevicePorts.mockReset()
  portsApi.changePort.mockReset()
  permissions.granted = new Set(['system.hosts', 'system.hosts.edit'])
})

describe('states', () => {
  it('shows a loading indicator, then the web fields', async () => {
    api.getDevicePluginVariables.mockReturnValue(new Promise(() => {}))
    renderDialog()
    expect(screen.getByText('Loading check options…')).toBeInTheDocument()
  })

  it('loads the options of the device and service it is given', async () => {
    renderDialog('https')
    await screen.findByLabelText('Expected text')
    expect(api.getDevicePluginVariables).toHaveBeenCalledWith(4, 'https')
  })

  it('shows the load error with Retry, and Retry loads again', async () => {
    api.getDevicePluginVariables.mockRejectedValueOnce(new ApiError('Device not found.', 404))
    renderDialog()
    expect(await screen.findByText('Device not found.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByLabelText('Expected text')).toBeInTheDocument()
    expect(api.getDevicePluginVariables).toHaveBeenCalledTimes(2)
  })

  it('shows the four web fields and, for mail, only the greeting with its default', async () => {
    renderDialog('http')
    await screen.findByLabelText('Expected text')
    expect(screen.getByLabelText('Expected status codes')).toBeInTheDocument()
    expect(screen.getByLabelText('Virtual host')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Request method' })).toBeInTheDocument()
  })

  it('shows the greeting field alone for IMAP', async () => {
    renderDialog('imap')
    expect(await screen.findByLabelText('Expected greeting')).toHaveAttribute('placeholder', '* OK')
    expect(screen.getByText(/Default: \* OK/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Virtual host')).not.toBeInTheDocument()
  })

  it('shows the saved options', async () => {
    api.getDevicePluginVariables.mockResolvedValue(saved('http', { expected_text: 'Welcome', method: 'HEAD' }))
    renderDialog()
    expect(await screen.findByLabelText('Expected text')).toHaveValue('Welcome')
    expect(screen.getByRole('button', { name: 'Request method' })).toHaveTextContent('HEAD')
  })
})

describe('saving', () => {
  it('sends the filled fields for the service and confirms', async () => {
    renderDialog('http')
    await screen.findByLabelText('Expected text')
    type('Expected text', 'Welcome')
    type('Expected status codes', '200,301')
    type('Virtual host', 'www.example.com')
    fireEvent.click(screen.getByRole('button', { name: 'Request method' }))
    fireEvent.click(screen.getByRole('option', { name: 'HEAD' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('Check options saved.')).toBeInTheDocument()
    expect(api.saveDevicePluginVariables).toHaveBeenCalledWith(
      4,
      { expected_text: 'Welcome', expected_status: '200,301', virtual_host: 'www.example.com', method: 'HEAD' },
      [],
      'http',
    )
  })

  it('keeps saved values the form does not own', async () => {
    api.getDevicePluginVariables.mockResolvedValue(saved('http', { warning: '2', expected_text: 'old' }))
    renderDialog()
    await screen.findByLabelText('Expected text')
    type('Expected text', 'new')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.saveDevicePluginVariables).toHaveBeenCalled())
    expect(api.saveDevicePluginVariables.mock.calls[0][1]).toEqual({ warning: '2', expected_text: 'new' })
  })

  it('blocks invalid values with a message and sends nothing', async () => {
    renderDialog()
    await screen.findByLabelText('Expected text')
    type('Expected status codes', '999')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('HTTP status codes from 100 to 599')
    type('Expected status codes', '200')
    type('Expected text', "it's")
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Expected text cannot contain')
    expect(api.saveDevicePluginVariables).not.toHaveBeenCalled()
  })

  it("shows the server's 400 and 422 messages", async () => {
    renderDialog()
    await screen.findByLabelText('Expected text')
    type('Expected text', 'ok')
    api.saveDevicePluginVariables.mockRejectedValueOnce(new ApiError("Variable 'expected_text' contains a forbidden character.", 400, { field: 'expected_text' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent("Variable 'expected_text' contains a forbidden character.")

    api.saveDevicePluginVariables.mockRejectedValueOnce(new ApiError('The settings could not be applied: nagios said no', 422))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('could not be applied: nagios said no'))
  })

  it('shows what the server stored after saving', async () => {
    renderDialog('imap')
    await screen.findByLabelText('Expected greeting')
    type('Expected greeting', '* OK Dovecot')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await screen.findByText('Check options saved.')
    expect(screen.getByLabelText('Expected greeting')).toHaveValue('* OK Dovecot')
  })
})

describe('reset to defaults', () => {
  it('is disabled while nothing is saved', async () => {
    renderDialog()
    await screen.findByLabelText('Expected text')
    expect(screen.getByRole('button', { name: 'Reset to defaults' })).toBeDisabled()
  })

  it('removes the override and empties the form', async () => {
    api.getDevicePluginVariables.mockResolvedValue(saved('http', { expected_text: 'Welcome' }))
    renderDialog()
    await screen.findByDisplayValue('Welcome')
    fireEvent.click(screen.getByRole('button', { name: 'Reset to defaults' }))

    expect(await screen.findByText('Check options reset to the defaults.')).toBeInTheDocument()
    expect(api.resetDevicePluginVariables).toHaveBeenCalledWith(4, 'http')
    expect(screen.getByLabelText('Expected text')).toHaveValue('')
  })

  it('shows the error when the reset fails', async () => {
    api.getDevicePluginVariables.mockResolvedValue(saved('http', { expected_text: 'Welcome' }))
    api.resetDevicePluginVariables.mockRejectedValueOnce(new ApiError('The settings could not be applied: nope', 422))
    renderDialog()
    await screen.findByDisplayValue('Welcome')
    fireEvent.click(screen.getByRole('button', { name: 'Reset to defaults' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('nope')
    expect(screen.getByLabelText('Expected text')).toHaveValue('Welcome')
  })
})

describe('without system.hosts.edit', () => {
  it('shows the saved options read-only', async () => {
    api.getDevicePluginVariables.mockResolvedValue(saved('http', { expected_text: 'Welcome' }))
    renderDialog('http', false)
    const field = await screen.findByLabelText('Expected text')
    expect(field).toHaveValue('Welcome')
    expect(field).toBeDisabled()
    expect(screen.getByLabelText('Expected status codes')).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Request method' })).toBeDisabled()
    expect(screen.getByText(/You can view the options but not change them/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Reset to defaults' })).not.toBeInTheDocument()
  })

  it('closes with Close', async () => {
    const onClose = renderDialog('http', false)
    await screen.findByLabelText('Expected text')
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(onClose).toHaveBeenCalled()
  })
})

describe('the Check options action of the Ports section', () => {
  const renderPorts = () =>
    render(
      <MemoryRouter>
        <DevicePortsSection deviceId={4} hostname="web-01" />
      </MemoryRouter>,
    )
  const web = (overrides = {}) => port({ number: 80, service_name: 'http', plugin_name: 'http', check_plugin: 'check_http', ...overrides })

  it.each(['http', 'https', 'pop3', 'imap', 'pop3s', 'imaps'])('is offered on a monitored %s port', async (plugin) => {
    portsApi.getDevicePorts.mockResolvedValue(ports([web({ plugin_name: plugin, service_name: plugin })]))
    renderPorts()
    expect(await screen.findByRole('button', { name: 'Check options for tcp/80 on web-01' })).toBeInTheDocument()
  })

  it('is not offered on ssh, on a suggested port or on an archived one', async () => {
    portsApi.getDevicePorts.mockResolvedValue(ports([
      port(),
      web({ number: 8080, state: 'SUGGESTED', plugin_name: null }),
      web({ number: 8081, state: 'ARCHIVED' }),
    ]))
    renderPorts()
    await screen.findByText('tcp/22')
    expect(screen.queryByRole('button', { name: /Check options/ })).not.toBeInTheDocument()
  })

  it('opens the form, saves and shows the options again after a reload', async () => {
    portsApi.getDevicePorts.mockResolvedValue(ports([web()]))
    const stored = { current: saved('http') }
    api.getDevicePluginVariables.mockImplementation(() => Promise.resolve(stored.current))
    api.saveDevicePluginVariables.mockImplementation((_id, variables) => {
      stored.current = saved('http', variables)
      return Promise.resolve(stored.current)
    })
    renderPorts()
    fireEvent.click(await screen.findByRole('button', { name: 'Check options for tcp/80 on web-01' }))
    await screen.findByLabelText('Expected text')
    type('Expected text', 'Welcome')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await screen.findByText('Check options saved.')

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Check options for tcp/80 on web-01' }))
    expect(await screen.findByDisplayValue('Welcome')).toBeInTheDocument()
  })

  it('is read-only for a user without system.hosts.edit, who still sees the action', async () => {
    permissions.granted = new Set(['system.hosts'])
    portsApi.getDevicePorts.mockResolvedValue(ports([web()]))
    renderPorts()
    fireEvent.click(await screen.findByRole('button', { name: 'Check options for tcp/80 on web-01' }))
    expect(await screen.findByLabelText('Expected text')).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument()
  })

  it('is read-only on a retired device', async () => {
    portsApi.getDevicePorts.mockResolvedValue(ports([web()], { state: 'RETIRED' }))
    renderPorts()
    fireEvent.click(await screen.findByRole('button', { name: 'Check options for tcp/80 on web-01' }))
    expect(await screen.findByLabelText('Expected text')).toBeDisabled()
  })
})
