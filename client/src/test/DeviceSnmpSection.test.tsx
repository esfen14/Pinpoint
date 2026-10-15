import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { DeviceSnmpSection } from '../components/device-inventory/DeviceSnmpSection'
import type { DeviceVariablesResponse } from '../types/devicePluginVariables'

const api = vi.hoisted(() => ({
  getDevicePluginVariables: vi.fn(), saveDevicePluginVariables: vi.fn(),
  resetDevicePluginVariables: vi.fn(), testDeviceSnmp: vi.fn(),
}))
vi.mock('../lib/devicePluginVariablesApi', () => api)

const permissions = vi.hoisted(() => ({ granted: new Set<string>() }))
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: null, isLoading: false, hasPermission: (name: string) => permissions.granted.has(name) }),
}))

const saved = (overrides: Partial<DeviceVariablesResponse> = {}): DeviceVariablesResponse => ({
  plugin: 'snmp', variables: {}, secrets_set: { auth_password: false, priv_password: false },
  editable: ['community', 'protocol'], in_use: true, ...overrides,
})

const v3Saved = saved({
  variables: { protocol: '3', security_level: 'authPriv', v3_user: 'monitor', auth_protocol: 'SHA', priv_protocol: 'AES', port: 1161 },
  secrets_set: { auth_password: true, priv_password: true },
})

function renderSection() {
  return render(<DeviceSnmpSection deviceId={4} hostname="switch-a" />)
}

const choose = (label: string | RegExp, value: string) =>
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
const type = (label: string | RegExp, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } })

beforeEach(() => {
  api.getDevicePluginVariables.mockReset().mockResolvedValue(saved())
  api.saveDevicePluginVariables.mockReset().mockImplementation(async () => saved())
  api.resetDevicePluginVariables.mockReset().mockResolvedValue(saved())
  api.testDeviceSnmp.mockReset().mockResolvedValue({ ok: true, state: 'OK', message: 'SNMP OK - 12345' })
  permissions.granted = new Set(['system.hosts', 'system.hosts.edit'])
})

describe('states of the section', () => {
  it('shows a loading indicator first', () => {
    api.getDevicePluginVariables.mockReturnValue(new Promise(() => {}))
    renderSection()
    expect(screen.getByText('Loading SNMP settings…')).toBeInTheDocument()
  })

  it('shows the error with Retry, and Retry loads again', async () => {
    api.getDevicePluginVariables.mockRejectedValueOnce(new ApiError('Device not found.', 404))
    renderSection()
    expect(await screen.findByText('Device not found.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByLabelText('SNMP version')).toBeInTheDocument()
  })

  it('is not shown for a device without an SNMP port', async () => {
    api.getDevicePluginVariables.mockResolvedValue(saved({ in_use: false }))
    const { container } = renderSection()
    await waitFor(() => expect(api.getDevicePluginVariables).toHaveBeenCalled())
    await waitFor(() => expect(screen.queryByText('Loading SNMP settings…')).not.toBeInTheDocument())
    expect(container).toBeEmptyDOMElement()
  })

  it('shows the defaults as "Default" and the form read-only without edit permission', async () => {
    permissions.granted = new Set(['system.hosts'])
    renderSection()
    expect(await screen.findByLabelText('SNMP version')).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Test' })).not.toBeInTheDocument()
    expect(screen.getByText(/view SNMP settings but not change/i)).toBeInTheDocument()
  })
})

describe('version choice', () => {
  it('shows the community for v2c and no v3 fields', async () => {
    renderSection()
    await screen.findByLabelText('SNMP version')
    choose('SNMP version', '2c')
    expect(screen.getByLabelText('Community')).toBeInTheDocument()
    expect(screen.queryByLabelText('SNMP v3 user')).not.toBeInTheDocument()
  })

  it('shows the v3 fields for version 3 and hides the community', async () => {
    renderSection()
    await screen.findByLabelText('SNMP version')
    choose('SNMP version', '3')
    expect(screen.getByLabelText('Security level')).toBeInTheDocument()
    expect(screen.getByLabelText('SNMP v3 user')).toBeInTheDocument()
    expect(screen.queryByLabelText('Community')).not.toBeInTheDocument()
  })

  it('shows only the fields the security level needs', async () => {
    renderSection()
    await screen.findByLabelText('SNMP version')
    choose('SNMP version', '3')
    choose('Security level', 'noAuthNoPriv')
    expect(screen.queryByLabelText('Authentication password')).not.toBeInTheDocument()
    choose('Security level', 'authNoPriv')
    expect(screen.getByLabelText('Authentication password')).toBeInTheDocument()
    expect(screen.queryByLabelText('Privacy password')).not.toBeInTheDocument()
    choose('Security level', 'authPriv')
    expect(screen.getByLabelText('Privacy password')).toBeInTheDocument()
  })
})

describe('validation before sending', () => {
  async function openV3() {
    renderSection()
    await screen.findByLabelText('SNMP version')
    choose('SNMP version', '3')
  }

  it('blocks a missing security level, user and passwords with a message', async () => {
    await openV3()
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Choose a security level.')
    choose('Security level', 'authPriv')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter the SNMP v3 user name.')
    type('SNMP v3 user', 'monitor')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter the authentication password.')
    type('Authentication password', 'authsecret1')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter the privacy password.')
    expect(api.saveDevicePluginVariables).not.toHaveBeenCalled()
  })

  it('also blocks the Test action', async () => {
    await openV3()
    fireEvent.click(screen.getByRole('button', { name: 'Test' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Choose a security level.')
    expect(api.testDeviceSnmp).not.toHaveBeenCalled()
  })
})

describe('saving', () => {
  it('sends the v3 fields and passwords, then clears the password boxes', async () => {
    api.saveDevicePluginVariables.mockResolvedValue(v3Saved)
    renderSection()
    await screen.findByLabelText('SNMP version')
    choose('SNMP version', '3')
    choose('Security level', 'authPriv')
    type('SNMP v3 user', ' monitor ')
    type('Authentication password', 'authsecret1')
    type('Privacy password', 'privsecret1')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(api.saveDevicePluginVariables).toHaveBeenCalledWith(4, {
      protocol: '3', security_level: 'authPriv', v3_user: 'monitor',
      auth_protocol: 'SHA', auth_password: 'authsecret1', priv_protocol: 'AES', priv_password: 'privsecret1',
    }, []))
    expect(await screen.findByRole('status')).toHaveTextContent('SNMP settings saved.')
    expect(screen.getByLabelText('Authentication password')).toHaveValue('')
    expect(screen.getByLabelText('Privacy password')).toHaveValue('')
  })

  it('never displays a saved password and offers to keep it', async () => {
    api.getDevicePluginVariables.mockResolvedValue(v3Saved)
    renderSection()
    const auth = await screen.findByLabelText('Authentication password')
    expect(auth).toHaveValue('')
    expect(auth).toHaveAttribute('type', 'password')
    expect(auth).toHaveAttribute('placeholder', 'Saved. Leave blank to keep it.')
    expect(document.body.textContent).not.toMatch(/secret/i)
  })

  it('keeps a saved password when the box is left blank, and keeps unrelated saved values', async () => {
    api.getDevicePluginVariables.mockResolvedValue(v3Saved)
    renderSection()
    await screen.findByLabelText('Authentication password')
    type('SNMP v3 user', 'other')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.saveDevicePluginVariables).toHaveBeenCalledWith(4, {
      port: 1161, protocol: '3', security_level: 'authPriv', v3_user: 'other',
      auth_protocol: 'SHA', priv_protocol: 'AES',
    }, []))
  })

  it('can remove a saved password', async () => {
    api.getDevicePluginVariables.mockResolvedValue(v3Saved)
    renderSection()
    await screen.findByLabelText('Authentication password')
    fireEvent.click(screen.getByRole('button', { name: 'Remove saved privacy password' }))
    choose('Security level', 'authNoPriv')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.saveDevicePluginVariables).toHaveBeenCalled())
    expect(api.saveDevicePluginVariables.mock.calls[0][2]).toEqual([])
  })

  it('sends only the version and community for v2c', async () => {
    renderSection()
    await screen.findByLabelText('SNMP version')
    choose('SNMP version', '2c')
    type('Community', 'lab')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.saveDevicePluginVariables).toHaveBeenCalledWith(4, { protocol: '2c', community: 'lab' }, []))
  })

  it("shows the server's message when saving fails, keeping what was typed", async () => {
    api.saveDevicePluginVariables.mockRejectedValue(new ApiError('The settings could not be applied: nope', 422))
    renderSection()
    await screen.findByLabelText('SNMP version')
    choose('SNMP version', '2c')
    type('Community', 'lab')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('nope')
    expect(screen.getByLabelText('Community')).toHaveValue('lab')
  })
})

describe('test action', () => {
  it('reports success', async () => {
    renderSection()
    await screen.findByLabelText('SNMP version')
    fireEvent.click(screen.getByRole('button', { name: 'Test' }))
    expect(await screen.findByRole('status')).toHaveTextContent('SNMP OK - 12345')
    expect(api.testDeviceSnmp).toHaveBeenCalledWith(4, {})
  })

  it('reports the failure reason', async () => {
    api.testDeviceSnmp.mockResolvedValue({ ok: false, state: 'CRITICAL', message: 'The device did not answer in time.' })
    renderSection()
    await screen.findByLabelText('SNMP version')
    fireEvent.click(screen.getByRole('button', { name: 'Test' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('The device did not answer in time.')
  })

  it('shows a request error', async () => {
    api.testDeviceSnmp.mockRejectedValue(new ApiError('Unknown variable.', 400))
    renderSection()
    await screen.findByLabelText('SNMP version')
    fireEvent.click(screen.getByRole('button', { name: 'Test' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Unknown variable.')
  })
})

describe('reset', () => {
  it('is offered only when something is saved and returns to the defaults', async () => {
    renderSection()
    await screen.findByLabelText('SNMP version')
    expect(screen.getByRole('button', { name: 'Reset to defaults' })).toBeDisabled()
  })

  it('resets a saved override', async () => {
    api.getDevicePluginVariables.mockResolvedValue(v3Saved)
    renderSection()
    await screen.findByLabelText('Authentication password')
    fireEvent.click(screen.getByRole('button', { name: 'Reset to defaults' }))
    await waitFor(() => expect(api.resetDevicePluginVariables).toHaveBeenCalledWith(4))
    expect(await screen.findByRole('status')).toHaveTextContent('SNMP settings reset')
    expect((screen.getByLabelText('SNMP version') as HTMLSelectElement).value).toBe('')
  })
})
