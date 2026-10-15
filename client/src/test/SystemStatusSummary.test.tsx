import { act, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { SystemStatusSummary } from '../components/settings/SystemSettings'
import { notifySettingsChanged } from '../lib/settingsEvents'
import { DEFAULT_SYSTEM_SETTINGS } from '../contexts/SystemSettingsContext'

const getPolicy = vi.fn()
const getEscalations = vi.fn()
vi.mock('../lib/notificationPolicyApi', () => ({ getNotificationPolicy: () => getPolicy() }))
vi.mock('../lib/escalationApi', () => ({ getEscalations: () => getEscalations() }))
vi.mock('../contexts/SystemSettingsContext', async (original) => ({
  ...(await original<typeof import('../contexts/SystemSettingsContext')>()),
  useSystemSettings: () => ({ settings: { ...DEFAULT_SYSTEM_SETTINGS, flapDetectionEnabled: false, checkInterval: 2, maxCheckAttempts: 4 } }),
}))

const policy = { quietHours: [], hostOptions: ['d', 'u'], serviceOptions: ['w', 'c', 'r'], renotifyInterval: 30, version: 1, timeZone: 'x' }
const item = { id: 1, first_notification: 2, last_notification: 5, interval_minutes: 10, contact_group: 'g', host_id: null, active: true, reason: '' }

beforeEach(() => {
  getPolicy.mockReset().mockResolvedValue(policy)
  getEscalations.mockReset().mockResolvedValue({ items: [], groups: [], hosts: [] })
})

describe('SystemStatusSummary', () => {
  it('summarises timing, flap detection, notifications and escalations', async () => {
    render(<SystemStatusSummary />)
    expect(await screen.findByText('2 host and 3 service states, no quiet hours')).toBeInTheDocument()
    expect(screen.getByText('Every 2 min, 4 attempts')).toBeInTheDocument()
    expect(screen.getByText('Disabled', { selector: 'span' })).toBeInTheDocument()
    expect(screen.getByText('None active')).toBeInTheDocument()
  })

  it('refreshes after notification policy or escalations are saved', async () => {
    render(<SystemStatusSummary />)
    await screen.findByText('None active')
    getEscalations.mockResolvedValue({ items: [item, { ...item, id: 2, active: false }], groups: [], hosts: [] })
    getPolicy.mockResolvedValue({ ...policy, quietHours: [{ weekday: 'monday', start: '01:00', end: '02:00' }] })
    act(() => notifySettingsChanged())
    expect(await screen.findByText('1 active')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText(/1 quiet window/)).toBeInTheDocument())
  })

  it('says so when notifications cannot be read', async () => {
    getPolicy.mockRejectedValue(new Error('403'))
    render(<SystemStatusSummary />)
    expect(await screen.findByText('Unavailable', { selector: 'span' })).toBeInTheDocument()
  })
})
