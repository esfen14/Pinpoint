import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { RegisterAgentDialog } from '../components/ncpa-deployment/RegisterAgentDialog'
import { NcpaDevicesTable } from '../components/ncpa-deployment/NcpaDevicesTable'
import { ApiError } from '../lib/api'
import type { NcpaDevice } from '../types/ncpaDeployment'

const api = vi.hoisted(() => ({ registerManualAgent: vi.fn(), getRegisterCandidates: vi.fn() }))
vi.mock('../lib/ncpaDeploymentApi', () => api)

const TOKEN = 'a1'.repeat(16)

const DEVICE: NcpaDevice = {
  id: 7, hostname: 'win-07', ipAddress: '10.0.20.7', trusted: false, fingerprint: null,
  agentStatus: 'Pending NCPA', lastError: null, lastOutcome: null, lastRunId: null, deployable: true,
}

function setup() {
  const onClose = vi.fn()
  const onRegistered = vi.fn()
  render(<RegisterAgentDialog device={DEVICE} onClose={onClose} onRegistered={onRegistered} />)
  return { onClose, onRegistered }
}

describe('RegisterAgentDialog', () => {
  beforeEach(() => { api.registerManualAgent.mockReset(); api.getRegisterCandidates.mockReset() })

  it('rejects a malformed token or port without calling the server', () => {
    setup()
    fireEvent.change(screen.getByLabelText('NCPA token'), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: 'Register agent' }))
    expect(screen.getByRole('alert')).toHaveTextContent('32 hexadecimal characters')

    fireEvent.change(screen.getByLabelText('NCPA token'), { target: { value: TOKEN } })
    fireEvent.change(screen.getByLabelText('Port (optional)'), { target: { value: '70000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Register agent' }))
    expect(screen.getByRole('alert')).toHaveTextContent('between 1 and 65535')
    expect(api.registerManualAgent).not.toHaveBeenCalled()
  })

  it('registers, shows the result and notifies the page', async () => {
    api.registerManualAgent.mockResolvedValue({
      device_id: 7, agent_status: 'Deployed NCPA', port: 5700, disks: ['C:'], config_applied: true, message: 'Applied.',
    })
    const { onRegistered } = setup()
    fireEvent.change(screen.getByLabelText('NCPA token'), { target: { value: TOKEN } })
    fireEvent.change(screen.getByLabelText('Port (optional)'), { target: { value: '5700' } })
    fireEvent.click(screen.getByRole('button', { name: 'Register agent' }))
    await waitFor(() => expect(api.registerManualAgent).toHaveBeenCalledWith(7, TOKEN, 5700))
    expect(await screen.findByText(/Agent registered/)).toBeInTheDocument()
    expect(screen.getByText(/Disks found: C:/)).toBeInTheDocument()
    expect(onRegistered).toHaveBeenCalled()
    expect(screen.queryByLabelText('NCPA token')).not.toBeInTheDocument()
  })

  it('shows the server message and clears the token after a failure', async () => {
    api.registerManualAgent.mockRejectedValue(new ApiError('Unable to connect to NCPA on port 5693.', 502))
    const { onRegistered } = setup()
    fireEvent.change(screen.getByLabelText('NCPA token'), { target: { value: TOKEN } })
    fireEvent.click(screen.getByRole('button', { name: 'Register agent' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to connect to NCPA')
    expect(screen.getByLabelText('NCPA token')).toHaveValue('')
    expect(api.registerManualAgent).toHaveBeenCalledWith(7, TOKEN, undefined)
    expect(onRegistered).not.toHaveBeenCalled()
  })

  it('has a Windows install help panel', () => {
    setup()
    expect(screen.getByText('Installing NCPA on Windows')).toBeInTheDocument()
  })
})

describe('RegisterAgentDialog without a preselected device', () => {
  beforeEach(() => { api.registerManualAgent.mockReset(); api.getRegisterCandidates.mockReset() })

  it('lists candidates, requires a choice, then registers for the picked device', async () => {
    api.getRegisterCandidates.mockResolvedValue([
      { id: 9, hostname: 'win-09', ipAddress: '10.0.20.9', agentStatus: null },
    ])
    api.registerManualAgent.mockResolvedValue({
      device_id: 9, agent_status: 'Deployed NCPA', port: 5693, disks: ['C:'], config_applied: true, message: 'ok',
    })
    render(<RegisterAgentDialog device={null} onClose={vi.fn()} onRegistered={vi.fn()} />)
    await screen.findByRole('option', { name: 'win-09 (10.0.20.9)' })
    fireEvent.change(screen.getByLabelText('NCPA token'), { target: { value: TOKEN } })
    fireEvent.click(screen.getByRole('button', { name: 'Register agent' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Choose a device')
    expect(api.registerManualAgent).not.toHaveBeenCalled()
    fireEvent.change(screen.getByLabelText('Device'), { target: { value: '9' } })
    fireEvent.click(screen.getByRole('button', { name: 'Register agent' }))
    await waitFor(() => expect(api.registerManualAgent).toHaveBeenCalledWith(9, TOKEN, undefined))
  })

  it('shows a load error', async () => {
    api.getRegisterCandidates.mockRejectedValue(new ApiError('Nope.', 500))
    render(<RegisterAgentDialog device={null} onClose={vi.fn()} onRegistered={vi.fn()} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Nope.')
  })
})

describe('NcpaDevicesTable register action', () => {
  const props = {
    isLoading: false, isRunning: false, selected: new Set<number>(), onSelectedChange: vi.fn(),
    onDeploySelected: vi.fn(), onVerify: vi.fn(), onRetry: vi.fn(), onCleanup: vi.fn(), onRemoteRestart: vi.fn(),
  }

  it('offers registration unless the agent is already deployed', () => {
    const onRegister = vi.fn()
    const deployed = { ...DEVICE, id: 8, hostname: 'web-08', agentStatus: 'Deployed NCPA' as const }
    render(<NcpaDevicesTable {...props} devices={[DEVICE, deployed]} onRegister={onRegister} />)
    const row = screen.getByText('win-07').closest('tr')!
    fireEvent.click(within(row).getByRole('button', { name: /Register an agent I installed/ }))
    expect(onRegister).toHaveBeenCalledWith(DEVICE)
    expect(within(screen.getByText('web-08').closest('tr')!).queryByRole('button', { name: /Register an agent/ })).not.toBeInTheDocument()
  })
})
