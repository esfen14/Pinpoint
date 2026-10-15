import { describe, expect, it } from 'vitest'
import { formToInput, inputToIso, isoToInput, recurrenceZone, validateForm, type MaintenanceForm } from '../utils/maintenanceTime'

const base: MaintenanceForm = { deviceId: null, start: '2099-10-21T10:00', end: '2099-10-21T12:00', recurrence: 'none', until: '', comment: 'patching' }
const NOW = new Date('2099-10-01T00:00:00Z')

describe('maintenance time conversion', () => {
  it('reads typed time in the display offset and stores UTC', () => {
    expect(inputToIso('2099-10-21T10:00', 'UTC+08:00')).toBe('2099-10-21T02:00:00.000Z')
    expect(inputToIso('2099-10-21T10:00', 'UTC-05:00')).toBe('2099-10-21T15:00:00.000Z')
    expect(inputToIso('2099-10-21T10:00', 'UTC+00:00')).toBe('2099-10-21T10:00:00.000Z')
  })

  it('shows stored UTC back in the display offset', () => {
    expect(isoToInput('2099-10-21T02:00:00Z', 'UTC+08:00')).toBe('2099-10-21T10:00')
    expect(isoToInput('2099-10-21T02:00:00Z', 'UTC-05:00')).toBe('2099-10-20T21:00')
    expect(isoToInput(null, 'UTC+08:00')).toBe('')
  })

  it('round trips, including the viewer\'s own browser zone', () => {
    for (const zone of ['UTC+05:30', 'UTC-03:00', 'Browser']) {
      expect(isoToInput(inputToIso('2099-03-15T23:45', zone), zone)).toBe('2099-03-15T23:45')
    }
  })

  it('rejects unreadable text', () => {
    expect(inputToIso('', 'UTC+00:00')).toBeNull()
    expect(inputToIso('tomorrow', 'UTC+00:00')).toBeNull()
  })

  it('sends UTC as the repeat zone for a fixed offset', () => {
    expect(recurrenceZone('UTC+08:00')).toBe('UTC')
    expect(recurrenceZone('Browser')).toMatch(/^[A-Za-z_]+(\/[A-Za-z_+\-0-9]+)*$/)
  })
})

describe('validateForm', () => {
  it('accepts a good window', () => {
    expect(validateForm(base, 'UTC+08:00', NOW)).toBeNull()
  })

  it.each([
    [{ start: '' }, /starts/],
    [{ end: '' }, /ends/],
    [{ end: '2099-10-21T09:00' }, /after the start/],
    [{ start: '2000-01-01T00:00', end: '2000-01-01T01:00' }, /future/],
    [{ end: '2099-12-31T12:00' }, /30 days/],
    [{ recurrence: 'daily', end: '2099-10-22T12:00' }, /daily window/],
    [{ recurrence: 'weekly', end: '2099-10-30T12:00' }, /weekly window/],
    [{ recurrence: 'daily', until: '2099-10-20T00:00' }, /before the window starts/],
    [{ recurrence: 'daily', until: '2101-10-20T00:00' }, /366 days/],
    [{ comment: '   ' }, /reason/],
    [{ comment: 'x'.repeat(201) }, /at most 200/],
  ] as [Partial<MaintenanceForm>, RegExp][])('rejects %j', (change, message) => {
    expect(validateForm({ ...base, ...change }, 'UTC+08:00', NOW)).toMatch(message)
  })

  it('builds the request body', () => {
    expect(formToInput({ ...base, recurrence: 'daily', until: '2099-11-21T10:00', comment: ' patching ' }, 'UTC+08:00')).toEqual({
      deviceId: null,
      startAt: '2099-10-21T02:00:00.000Z',
      endAt: '2099-10-21T04:00:00.000Z',
      recurrence: 'daily',
      recurrenceUntil: '2099-11-21T02:00:00.000Z',
      timeZone: 'UTC',
      comment: 'patching',
    })
  })

  it('drops the stop-repeating time of a window that does not repeat', () => {
    expect(formToInput({ ...base, until: '2099-11-21T10:00' }, 'UTC+08:00').recurrenceUntil).toBeNull()
  })
})
