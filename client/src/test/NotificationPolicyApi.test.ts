import { afterEach, describe, expect, it, vi } from 'vitest'
import { getNotificationPolicy, saveNotificationPolicy } from '../lib/notificationPolicyApi'
import type { NotificationPolicy } from '../types/notificationPolicy'

const wire: NotificationPolicy = {
  quietHours: [{ weekday: 'monday', start: '09:00', end: '10:00' }],
  hostOptions: ['d', 'r'], serviceOptions: ['w', 'c'],
  renotifyInterval: 15, version: 2, timeZone: 'Nagios server local time',
}

afterEach(() => vi.unstubAllGlobals())

describe('notification policy API', () => {
  it('reads and writes through the shared API envelope with credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, text: async () => JSON.stringify({ success: true, data: wire }) })
    vi.stubGlobal('fetch', fetchMock)
    expect(await getNotificationPolicy()).toEqual(wire)
    expect(fetchMock).toHaveBeenCalledWith('/api/system/notification-policy', expect.objectContaining({ credentials: 'include' }))
    expect(await saveNotificationPolicy(wire)).toEqual(wire)
    expect(fetchMock).toHaveBeenLastCalledWith('/api/system/notification-policy', expect.objectContaining({ method: 'PUT', body: JSON.stringify(wire) }))
  })
})
