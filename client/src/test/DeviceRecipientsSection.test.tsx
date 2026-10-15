import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DeviceRecipientsSection } from '../components/device-inventory/DeviceRecipientsSection'

const api = vi.hoisted(() => ({ get: vi.fn(), put: vi.fn() }))
vi.mock('../lib/api', async () => ({
  ...await vi.importActual<typeof import('../lib/api')>('../lib/api'),
  apiGet: (path: string) => api.get(path),
  apiPut: (path: string, body: unknown) => api.put(path, body),
}))
const data = {
  recipient_ids: [1], using_default: false, editable: true,
  users: [
    { id: 1, name: 'Alice Admin', email: 'alice@example.com', eligible: true },
    { id: 2, name: 'Bob Operator', email: 'bob@example.com', eligible: true },
    { id: 3, name: 'Carol Paused', email: 'carol@example.com', eligible: false },
  ],
}
beforeEach(() => {
  api.get.mockReset().mockResolvedValue(data)
  api.put.mockReset().mockResolvedValue({ ...data, recipient_ids: [1, 2] })
})

describe('Host email recipients', () => {
  it('loads saved choices and sends selected IDs', async () => {
    render(<DeviceRecipientsSection deviceId={4} />)
    const bob = await screen.findByRole('checkbox', { name: /Bob Operator/ })
    expect(screen.getByRole('checkbox', { name: /Alice Admin/ })).toBeChecked()
    fireEvent.click(bob)
    fireEvent.click(screen.getByRole('button', { name: 'Save recipients' }))
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/api/system/hosts/4/recipients', { recipient_ids: [1, 2] }))
    expect(await screen.findByText('Alert recipients saved.')).toBeInTheDocument()
  })
  it('clearing choices sends an empty list and explains the default', async () => {
    api.put.mockResolvedValue({ ...data, recipient_ids: [], using_default: true })
    render(<DeviceRecipientsSection deviceId={4} />)
    fireEvent.click(await screen.findByRole('checkbox', { name: /Alice Admin/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save recipients' }))
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/api/system/hosts/4/recipients', { recipient_ids: [] }))
    expect(await screen.findByText(/Using the default recipients/)).toBeInTheDocument()
  })
  it('shows ineligible selections with their eligibility explanation', async () => {
    api.get.mockResolvedValue({ ...data, recipient_ids: [3], using_default: true })
    render(<DeviceRecipientsSection deviceId={4} />)
    expect(await screen.findByRole('checkbox', { name: /Carol Paused/ })).toBeChecked()
    expect(screen.getByText(/Inactive or email alerts off/)).toBeInTheDocument()
    expect(screen.getByText(/Using the default recipients/)).toBeInTheDocument()
  })
  it('shows apply errors and preserves the editable choice', async () => {
    api.put.mockRejectedValue(new Error('Nagios reload failed'))
    render(<DeviceRecipientsSection deviceId={4} />)
    fireEvent.click(await screen.findByRole('checkbox', { name: /Bob Operator/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save recipients' }))
    expect(await screen.findByText('Nagios reload failed')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /Bob Operator/ })).toBeChecked()
    expect(screen.getByRole('button', { name: 'Save recipients' })).toBeEnabled()
  })
  it('offers retry after a load error', async () => {
    api.get.mockRejectedValueOnce(new Error('Unavailable'))
    render(<DeviceRecipientsSection deviceId={4} />)
    expect(await screen.findByText('Unavailable')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByRole('checkbox', { name: /Bob Operator/ })).toBeInTheDocument()
  })
  it('shows an empty account state', async () => {
    api.get.mockResolvedValue({ ...data, users: [], recipient_ids: [], using_default: true })
    render(<DeviceRecipientsSection deviceId={4} />)
    expect(await screen.findByText('No user accounts available.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save recipients' })).toBeDisabled()
  })
  it('retired and merged devices are read only', async () => {
    api.get.mockResolvedValue({ ...data, editable: false })
    render(<DeviceRecipientsSection deviceId={4} />)
    expect(await screen.findByText('This device is retired or merged.')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /Alice Admin/ })).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Save recipients' })).not.toBeInTheDocument()
  })
  it('disables editing while a save is pending', async () => {
    api.put.mockReturnValue(new Promise(() => {}))
    render(<DeviceRecipientsSection deviceId={4} />)
    fireEvent.click(await screen.findByRole('checkbox', { name: /Bob Operator/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save recipients' }))
    expect(screen.getByRole('button', { name: 'Saving…' })).toBeDisabled()
    expect(screen.getByRole('checkbox', { name: /Alice Admin/ })).toBeDisabled()
  })
})
