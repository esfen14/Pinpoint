import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DeviceIdentityReviews } from '../components/device-inventory/DeviceIdentityReviews'
import type { DeviceSummary, IdentityReview } from '../types/deviceIdentity'
const mocks = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), permissions: new Set<string>() }))
vi.mock('../lib/api', async () => ({ ...await vi.importActual<typeof import('../lib/api')>('../lib/api'), apiGet: (p: string) => mocks.get(p), apiPost: (p: string, b: unknown) => mocks.post(p, b) }))
vi.mock('../contexts/CurrentUserContext', () => ({ useCurrentUser: () => ({ hasPermission: (p: string) => mocks.permissions.has(p) }) }))
const device = (id: number, state = 'ACTIVE'): DeviceSummary => ({ id, display_name: `Device ${id}`, nagios_host_name: `host-${id}`, ip_address: `10.77.0.${id}`, state, monitoring_state: state === 'ACTIVE' ? 'monitored' : 'paused', monitored: state === 'ACTIVE' })
const one = device(1), two = device(2, 'ADDRESS_UNKNOWN')
const review = (kind = 'CONFLICT', devices = [one, two]): IdentityReview => ({ id: 1, kind, devices, message: 'Conflicting identifiers require a decision.', created_at: '2026-10-15T00:00:00', ip_address: one.ip_address, mac_address: null })
let items: IdentityReview[]
let refresh: ReturnType<typeof vi.fn>
function mount() { return render(<DeviceIdentityReviews onMerged={refresh} />) }
async function open() { mount(); await userEvent.click(await screen.findByRole('button', { name: 'Review' })) }
async function choose() {
  await userEvent.selectOptions(screen.getByLabelText('Device record to keep'), '1')
  await userEvent.selectOptions(screen.getByLabelText('Duplicate record to merge'), '2')
}
async function confirm() { await choose(); await userEvent.click(screen.getByRole('button', { name: 'Review merge' })) }
beforeEach(() => {
  mocks.permissions = new Set(['system.discover', 'system.hosts', 'system.hosts.edit']); items = [review()]; refresh = vi.fn()
  mocks.post.mockReset().mockResolvedValue({ config_ok: true })
  mocks.get.mockReset().mockImplementation((p: string) => {
    if (p === '/api/system/discover/review') return Promise.resolve({ items })
    if (p.includes('/lookup')) return Promise.resolve({ items: [device(3)], has_more: false })
    const d = p.includes('/1/') ? one : two
    if (p.endsWith('/identifiers')) return Promise.resolve({ device: d, confidence: 'UNVERIFIED', identifiers: [], recommendation: null })
    if (p.endsWith('/addresses')) return Promise.resolve({ device: d, addresses: [] })
    throw new Error(`Unexpected ${p}`)
  })
})
describe('device identity review', () => {
  it('counts five identity kinds, excludes service changes and loads no evidence with the table', async () => {
    items = ['CONFLICT', 'IDENTITY_CHANGED', 'IP_REUSE', 'DUPLICATE_IDENTITY', 'STATIC_MOVED', 'SERVICE_CHANGED'].map((kind, i) => ({ ...review(kind), id: i + 1 })); mount()
    expect(await screen.findByRole('heading', { name: 'Needs Review (5)' })).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Review' })).toHaveLength(5); expect(mocks.get).toHaveBeenCalledTimes(1)
  })
  it('does not load or show reviews without discover permission', () => {
    mocks.permissions.delete('system.discover'); mount(); expect(screen.queryByText(/Needs Review/)).not.toBeInTheDocument(); expect(mocks.get).not.toHaveBeenCalled()
  })
  it('shows loading and permanent empty section', async () => {
    items = []; mount(); expect(screen.getByText('Loading identity reviews…')).toBeInTheDocument()
    expect(await screen.findByText('No device identity issues need review.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Needs Review (0)' })).toBeInTheDocument()
  })
  it('retries failed review loads', async () => {
    mocks.get.mockRejectedValueOnce(new Error('Offline')); mount(); expect(await screen.findByRole('alert')).toHaveTextContent('Offline')
    await userEvent.click(screen.getByRole('button', { name: 'Retry' })); expect(await screen.findByRole('button', { name: 'Review' })).toBeInTheDocument()
  })
  it('loads comparison on opening and addresses on demand, labels missing evidence', async () => {
    await open(); expect(await screen.findAllByText('UNVERIFIED')).toHaveLength(2)
    expect(screen.getAllByText('No identity identifiers available.')).toHaveLength(2)
    expect(screen.getByText(/Similar names or matching IPs/)).toBeInTheDocument()
    expect(mocks.get.mock.calls.some(([p]) => p.endsWith('/addresses'))).toBe(false)
    await userEvent.click(screen.getAllByRole('button', { name: 'Load address history' })[0]); expect(await screen.findByText('No address history available.')).toBeInTheDocument()
    expect(screen.getByText('host-1')).toBeInTheDocument()
  })
  it('requires hosts permission for details and merge controls', async () => {
    mocks.permissions.delete('system.hosts'); await open(); expect(screen.getAllByText(/system.hosts permission is required/)).toHaveLength(2)
    expect(screen.queryByLabelText('Device record to keep')).not.toBeInTheDocument(); expect(mocks.get).toHaveBeenCalledTimes(1)
  })
  it('permits comparison without merge permission', async () => {
    mocks.permissions.delete('system.hosts.edit'); await open(); expect(await screen.findAllByText('UNVERIFIED')).toHaveLength(2)
    expect(screen.queryByLabelText('Device record to keep')).not.toBeInTheDocument()
  })
  it('retries unavailable identity evidence', async () => {
    const normal = mocks.get.getMockImplementation()!
    mocks.get.mockImplementation((p: string) => p.endsWith('/identifiers') ? Promise.reject(new Error('Evidence unavailable')) : normal(p))
    await open(); expect(await screen.findAllByText('Evidence unavailable')).toHaveLength(2); mocks.get.mockImplementation(normal)
    await userEvent.click(screen.getAllByRole('button', { name: 'Retry evidence' })[0]); expect(await screen.findByText('UNVERIFIED')).toBeInTheDocument()
  })
  it('searches discovered records with insufficient candidates and never defaults direction', async () => {
    items = [review('IP_REUSE', [one])]; await open()
    expect(screen.getByLabelText('Device record to keep')).toHaveValue(''); expect(screen.getByLabelText('Duplicate record to merge')).toHaveValue('')
    await userEvent.type(screen.getByLabelText('Search discovered devices'), 'third'); await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await userEvent.click(await screen.findByRole('button', { name: /Add Device 3/ }))
    expect(within(screen.getByLabelText('Device record to keep')).getByRole('option', { name: /Device 3/ })).toBeInTheDocument()
    expect(mocks.get).toHaveBeenCalledWith('/api/system/hosts/lookup?search=third')
  })
  it('blocks self merge, merged sources and retired/merged targets', async () => {
    items = [review('CONFLICT', [one, device(2, 'RETIRED'), device(3, 'MERGED')])]; await open()
    expect(within(screen.getByLabelText('Device record to keep')).queryByRole('option', { name: /Device 2|Device 3/ })).not.toBeInTheDocument()
    expect(within(screen.getByLabelText('Duplicate record to merge')).queryByRole('option', { name: /Device 3/ })).not.toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('Device record to keep'), '1'); await userEvent.selectOptions(screen.getByLabelText('Duplicate record to merge'), '1')
    expect(screen.getByRole('button', { name: 'Review merge' })).toBeDisabled()
  })
  it('explains consequences, cancellation and closing make no persistent change', async () => {
    await open(); await confirm(); const dialog = screen.getByRole('dialog', { name: 'Confirm device merge' })
    for (const text of [/ID 1/, /ID 2/, /retains its current address/, /leaves monitoring/, /Target records take precedence/, /Historical monitoring snapshots/, /No undo/]) expect(within(dialog).getByText(text)).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' })); fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(); expect(mocks.post).not.toHaveBeenCalled()
  })
  it('submits once, refreshes and reports saved configuration warnings accurately', async () => {
    let resolve!: (v: unknown) => void; mocks.post.mockImplementation(() => new Promise(r => { resolve = r }))
    await open(); await confirm(); await userEvent.click(screen.getByRole('button', { name: 'Merge duplicate' }))
    expect(screen.getByRole('button', { name: 'Saving…' })).toBeDisabled()
    expect(mocks.post).toHaveBeenCalledExactlyOnceWith('/api/system/hosts/2/merge', { target_id: 1 }); items = []
    resolve({ config_ok: false, config_message: 'Reload unavailable' })
    expect(await screen.findByText(/Merge saved.*Reload unavailable/)).toBeInTheDocument()
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1)); expect(await screen.findByText('No device identity issues need review.')).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
  it('shows backend stale validation and retains choices after rejection', async () => {
    mocks.post.mockRejectedValue(new Error('The target device is retired or merged.')); await open(); await confirm()
    await userEvent.click(screen.getByRole('button', { name: 'Merge duplicate' })); expect(await screen.findByRole('alert')).toHaveTextContent('The target device is retired or merged.')
    expect(screen.getByLabelText('Device record to keep')).toHaveValue('1'); expect(refresh).not.toHaveBeenCalled()
  })
  it('contains keyboard focus, focuses confirmation and restores the Review opener', async () => {
    await open()
    const drawer = screen.getByRole('dialog', { name: 'Review device identity' })
    expect(drawer).toHaveFocus()
    const close = within(drawer).getByRole('button', { name: 'Close' })
    await userEvent.tab(); expect(close).toHaveFocus()
    await choose(); await userEvent.click(screen.getByRole('button', { name: 'Review merge' }))
    const confirmation = screen.getByRole('dialog', { name: 'Confirm device merge' })
    expect(confirmation).toHaveFocus()
    await userEvent.tab({ shift: true })
    expect(screen.getByRole('button', { name: 'Merge duplicate' })).toHaveFocus()
    await userEvent.tab(); expect(within(confirmation).getByRole('button', { name: 'Close' })).toHaveFocus()
    await userEvent.keyboard('{Escape}')
    expect(screen.getByRole('dialog', { name: 'Review device identity' })).toHaveFocus()
    await userEvent.keyboard('{Escape}')
    expect(screen.getByRole('button', { name: 'Review' })).toHaveFocus()
  })
  it('makes unavailable address history retryable', async () => {
    const normal = mocks.get.getMockImplementation()!
    mocks.get.mockImplementation((p: string) => p.endsWith('/addresses') ? Promise.reject(new Error('Addresses offline')) : normal(p))
    await open(); await userEvent.click(screen.getAllByRole('button', { name: 'Load address history' })[0])
    expect(await screen.findByRole('alert')).toHaveTextContent('Addresses offline')
    mocks.get.mockImplementation(normal); await userEvent.click(screen.getByRole('button', { name: 'Retry address history' }))
    expect(await screen.findByText('No address history available.')).toBeInTheDocument()
  })

})
