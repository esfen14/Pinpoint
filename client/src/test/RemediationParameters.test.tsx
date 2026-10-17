import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { ActionFormDialog } from '../components/remediation/ActionFormDialog'
import type { ActionTypeInfo, RemediationAction } from '../types/remediation'
import { ApiError } from '../lib/api'
const api = vi.hoisted(() => ({ createAction: vi.fn(), updateAction: vi.fn() }))
vi.mock('../lib/remediationApi', async () => ({ ...await vi.importActual('../lib/remediationApi'), ...api }))
const types: ActionTypeInfo[] = [
  { key: 'record_only', label: 'Record only', description: 'Record.', parameters: [] },
  { key: 'restart_local_service', label: 'Local restart', description: 'Local.', parameters: [{ name: 'unit', label: 'Service to restart', type: 'choice', choices: ['nagios'], required: true }] },
  { key: 'restart_remote_service', label: 'Remote restart', description: 'Remote.', parameters: [{ name: 'unit', label: 'Service to restart', type: 'text', required: true }] },
]
const action: RemediationAction = {
  id: 1, name: 'restart-web', actionType: 'restart_remote_service', scopeKind: 'host', hostPattern: 'web-*', servicePattern: null,
  parameters: { unit: 'apache2' }, enabled: true, maxRunsPerHour: 2, cooldownSeconds: 600, runWhenAcknowledged: false, notifyOn: ['failed', 'capped', 'repeated'], version: 4, updatedAt: null, updatedBy: null,
}
function show(existing: RemediationAction | null = null) {
  render(<ActionFormDialog types={types} action={existing} onClose={vi.fn()} onSaved={vi.fn()} onReload={vi.fn()} />)
}
beforeEach(() => { vi.resetAllMocks(); api.createAction.mockResolvedValue(action); api.updateAction.mockResolvedValue(action) })

it('sends the remote unit when creating an action', async () => {
  show()
  fireEvent.change(screen.getByLabelText('Action type'), { target: { value: 'restart_remote_service' } })
  fireEvent.change(screen.getByLabelText('Service to restart'), { target: { value: 'apache2' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save action' }))
  await waitFor(() => expect(api.createAction).toHaveBeenCalledWith(expect.objectContaining({ actionType: 'restart_remote_service', parameters: { unit: 'apache2' } })))
})
it('prefills and updates the remote unit with the action version', async () => {
  show(action)
  expect(screen.getByLabelText('Service to restart')).toHaveValue('apache2')
  fireEvent.change(screen.getByLabelText('Service to restart'), { target: { value: 'ncpa' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save action' }))
  await waitFor(() => expect(api.updateAction).toHaveBeenCalledWith(1, expect.objectContaining({ parameters: { unit: 'ncpa' } }), 4))
})
it('offers only local API choices and clears parameters for record only', async () => {
  show(action)
  fireEvent.change(screen.getByLabelText('Action type'), { target: { value: 'restart_local_service' } })
  const unit = screen.getByRole('combobox', { name: 'Service to restart' })
  expect(unit).toHaveValue('')
  fireEvent.change(unit, { target: { value: 'nagios' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save action' }))
  await waitFor(() => expect(api.updateAction).toHaveBeenCalledWith(1, expect.objectContaining({ parameters: { unit: 'nagios' } }), 4))
  fireEvent.change(screen.getByLabelText('Action type'), { target: { value: 'record_only' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save action' }))
  await waitFor(() => expect(api.updateAction).toHaveBeenLastCalledWith(1, expect.objectContaining({ parameters: {} }), 4))
})
it('associates parameter validation with its field', async () => {
  api.updateAction.mockRejectedValue(new ApiError('Invalid', 400, { fields: { 'parameters.unit': 'Use a plain service name.' } }))
  show(action)
  fireEvent.click(screen.getByRole('button', { name: 'Save action' }))
  expect(await screen.findByText('Use a plain service name.')).toBeInTheDocument()
  expect(screen.getByLabelText('Service to restart')).toHaveAccessibleDescription('Use a plain service name.')
})
