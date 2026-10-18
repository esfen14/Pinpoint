import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { RecentNotifications, type DashboardNotification } from '../components/dashboard/RecentNotifications'
import { fromRawNotification, notificationTitle } from '../types/notification'

vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: { permissions: [] }, isLoading: false, hasPermission: () => false }),
}))
vi.mock('../contexts/SystemSettingsContext', () => ({
  useSystemSettings: () => ({ settings: { dateTimeFormat: 'DD/MM/YYYY', timeZone: 'UTC+00:00' } }),
}))

const COMMENT = 'PinPoint automatic recovery did not succeed: action restart-web ended failed (run 7).'

// What GET /api/system/notifications returns for the entry captured on the lab appliance.
const custom = {
  timestamp: 1792243944, hostname: 'web-01', servicedesc: 'HTTP', state: '', notificationtype: 'CUSTOM',
  contact: 'nagiosadmin', output: 'HTTP CRITICAL - Connection refused', is_custom: true, comment: COMMENT,
  is_read: false, repeat_count: 1,
}
const problem = { ...custom, notificationtype: '1', is_custom: false, comment: undefined }

describe('the bell: a custom notification', () => {
  it('is marked custom and shows its comment, keeping the plugin output in the detail', () => {
    const item = fromRawNotification(custom, 0)
    expect(item.isCustom).toBe(true)
    expect(item.comment).toBe(COMMENT)
    expect(item.message).toBe(COMMENT)
    expect(item.fullMessage).toContain(COMMENT)
    expect(item.fullMessage).toContain('HTTP CRITICAL - Connection refused')
  })

  it('is titled as a custom notification', () => {
    expect(notificationTitle(fromRawNotification(custom, 0))).toBe('Custom notification web-01 / HTTP')
  })

  it('still shows its plugin output when nobody here sent it (no comment)', () => {
    const item = fromRawNotification({ ...custom, comment: null }, 0)
    expect(item.isCustom).toBe(true)
    expect(item.comment).toBeNull()
    expect(item.message).toBe('HTTP CRITICAL - Connection refused')
  })

  it('leaves an ordinary notification as it was', () => {
    const item = fromRawNotification(problem, 0)
    expect(item.isCustom).toBe(false)
    expect(item.comment).toBeNull()
    expect(item.message).toBe('HTTP CRITICAL - Connection refused')
    expect(notificationTitle(item)).toBe('1 web-01 / HTTP')
  })

  it('is recognised by its type alone when the flag is missing', () => {
    expect(fromRawNotification({ ...custom, is_custom: undefined }, 0).isCustom).toBe(true)
  })
})

function renderRecent(notifications: DashboardNotification[]) {
  return render(<MemoryRouter><RecentNotifications notifications={notifications} isLoading={false} /></MemoryRouter>)
}

describe('the Dashboard: a custom notification', () => {
  it('says Custom in the state column and shows its comment', () => {
    renderRecent([{
      timestamp: 1792243944, type: 'CUSTOM', hostname: 'web-01', service_name: 'HTTP', state: '', contact: 'nagiosadmin',
      message: 'HTTP CRITICAL - Connection refused', is_custom: true, comment: COMMENT,
    }])
    const row = screen.getByText('web-01 / HTTP').closest('tr') as HTMLElement
    expect(row).toHaveTextContent('Custom')
    expect(screen.getByText(COMMENT)).toBeInTheDocument()
  })

  it('falls back to the plugin output without a comment', () => {
    renderRecent([{
      timestamp: 1792243944, type: 'CUSTOM', hostname: 'web-01', service_name: 'HTTP', state: '', contact: 'nagiosadmin',
      message: 'HTTP CRITICAL - Connection refused', is_custom: true, comment: null,
    }])
    expect(screen.getByText('HTTP CRITICAL - Connection refused')).toBeInTheDocument()
    expect(screen.getByText('web-01 / HTTP').closest('tr')).toHaveTextContent('Custom')
  })

  it('leaves an ordinary notification as it was', () => {
    renderRecent([{
      timestamp: 1792243944, type: '1', hostname: 'web-01', service_name: 'HTTP', state: 'CRITICAL', contact: 'admin',
      message: 'HTTP CRITICAL', is_custom: false,
    }])
    const row = screen.getByText('web-01 / HTTP').closest('tr') as HTMLElement
    expect(row).toHaveTextContent('CRITICAL')
    expect(row).not.toHaveTextContent('Custom')
  })

  it('still renders notifications from a server that sends neither field', () => {
    renderRecent([{
      timestamp: 1792243944, type: 'PROBLEM', hostname: 'db', service_name: null, state: 'DOWN', contact: 'admin', message: 'down',
    }])
    expect(screen.getByText('down')).toBeInTheDocument()
  })
})
