import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { RemoteRestartDialog } from '../components/ncpa-deployment/RemoteRestartDialog'
import { ApiError } from '../lib/api'

const api = vi.hoisted(() => ({ getRemoteRestart: vi.fn(), saveRemoteRestart: vi.fn() }))
vi.mock('../lib/ncpaDeploymentApi', () => api)
const onClose = vi.fn()

beforeEach(() => {
  vi.resetAllMocks()
  api.getRemoteRestart.mockResolvedValue({ enabled: false, services: [], trusted: true })
  api.saveRemoteRestart.mockResolvedValue({ enabled: true, services: ['apache2'], trusted: true, redeploy_needed: true })
})

it('loads, saves the device switch and services, and explains redeployment', async () => {
  render(<RemoteRestartDialog deviceId={7} hostname="web-01" onClose={onClose} />)
  expect(screen.getByText(/Loading restart settings/)).toBeInTheDocument()
  expect(await screen.findByLabelText('Services allowed to restart')).toHaveValue('')
  expect(screen.getByText(/No services are allowed/)).toBeInTheDocument()
  fireEvent.click(screen.getByLabelText('Allow remote service restart'))
  fireEvent.change(screen.getByLabelText('Services allowed to restart'), { target: { value: 'apache2\nncpa' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save settings' }))
  await waitFor(() => expect(api.saveRemoteRestart).toHaveBeenCalledWith(7, { enabled: true, services: ['apache2', 'ncpa'] }))
  expect(await screen.findByRole('status')).toHaveTextContent(/Saved.*Clean up.*redeploy/)
  expect(onClose).not.toHaveBeenCalled()
})

it('offers a retry after a load error', async () => {
  api.getRemoteRestart.mockRejectedValueOnce(new ApiError('Unable to load settings', 500))
  render(<RemoteRestartDialog deviceId={7} hostname="web-01" onClose={onClose} />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load settings')
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
  expect(await screen.findByLabelText('Services allowed to restart')).toBeInTheDocument()
})

it('keeps values on save failure and shows the server explanation', async () => {
  api.saveRemoteRestart.mockRejectedValue(new ApiError('Choose at least one service.', 400))
  render(<RemoteRestartDialog deviceId={7} hostname="web-01" onClose={onClose} />)
  fireEvent.click(await screen.findByLabelText('Allow remote service restart'))
  fireEvent.click(screen.getByRole('button', { name: 'Save settings' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Choose at least one service.')
  expect(screen.getByLabelText('Allow remote service restart')).toBeChecked()
})

it('requires a trusted deployment to enable, but can prepare the list before deployment', async () => {
  api.getRemoteRestart.mockResolvedValue({ enabled: false, services: ['apache2'], trusted: false })
  render(<RemoteRestartDialog deviceId={7} hostname="web-01" onClose={onClose} />)
  expect(await screen.findByLabelText('Allow remote service restart')).toBeDisabled()
  expect(screen.getByLabelText('Services allowed to restart')).toHaveValue('apache2')
  expect(screen.getByText(/Trust and deploy this device/)).toBeInTheDocument()
})

it('shows permission denial without exposing editable controls', async () => {
  api.getRemoteRestart.mockRejectedValue(new ApiError('You do not have permission.', 403))
  render(<RemoteRestartDialog deviceId={7} hostname="web-01" onClose={onClose} />)
  expect(await screen.findByRole('alert')).toHaveTextContent(/permission/)
  expect(screen.queryByRole('button', { name: 'Save settings' })).not.toBeInTheDocument()
})

it('can turn an enabled policy off after deployment trust is lost', async () => {
  api.getRemoteRestart.mockResolvedValue({ enabled: true, services: ['apache2'], trusted: false })
  render(<RemoteRestartDialog deviceId={7} hostname="web-01" onClose={onClose} />)
  const enabled = await screen.findByLabelText('Allow remote service restart')
  expect(enabled).toBeEnabled()
  fireEvent.click(enabled)
  fireEvent.click(screen.getByRole('button', { name: 'Save settings' }))
  await waitFor(() => expect(api.saveRemoteRestart).toHaveBeenCalledWith(7, { enabled: false, services: ['apache2'] }))
})
