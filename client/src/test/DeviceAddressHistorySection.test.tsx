import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DeviceAddressHistorySection } from '../components/device-inventory/DeviceAddressHistorySection'

const api = vi.hoisted(() => ({ get: vi.fn() }))
vi.mock('../lib/deviceIdentityApi', () => ({ getAddressEvidence: (id: number) => api.get(id) }))

const row = (id: number, ip: string, current: boolean) => ({
  id, ip_address: ip, current, first_seen_at: '2026-11-03T10:00:00', last_seen_at: '2026-11-03T11:00:00', closed_at: current ? null : '2026-11-03T11:00:00',
})

beforeEach(() => api.get.mockReset())

describe('Device IP address history', () => {
  it('lists the addresses in the order the API returns them, marking the current one', async () => {
    api.get.mockResolvedValue({ device: {}, addresses: [row(3, '10.0.0.20', true), row(2, '10.0.0.25', false), row(1, '10.0.0.20', false)] })
    render(<DeviceAddressHistorySection deviceId={7} />)

    await screen.findByText('IP address history')
    const cells = await screen.findAllByText(/^10\.0\.0\.(20|25)/)
    expect(cells.map((c) => c.textContent?.replace('Current', ''))).toEqual(['10.0.0.20', '10.0.0.25', '10.0.0.20'])
    expect(screen.getAllByText('Current')).toHaveLength(1)
    expect(screen.getByText('First seen')).toBeInTheDocument()
    expect(screen.getByText('Last seen')).toBeInTheDocument()
    expect(api.get).toHaveBeenCalledWith(7)
  })

  it('says when there is no history', async () => {
    api.get.mockResolvedValue({ device: {}, addresses: [] })
    render(<DeviceAddressHistorySection deviceId={7} />)
    expect(await screen.findByText('No address history recorded.')).toBeInTheDocument()
  })

  it('offers retry after a load error', async () => {
    api.get.mockRejectedValueOnce(new Error('Unavailable')).mockResolvedValue({ device: {}, addresses: [row(1, '10.0.0.5', true)] })
    render(<DeviceAddressHistorySection deviceId={7} />)
    expect(await screen.findByText('Unavailable')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await waitFor(() => expect(screen.getByText(/10\.0\.0\.5/)).toBeInTheDocument())
  })
})
