import { BROWSER_TIME_ZONE, parseServerDate, parseUtcOffsetMinutes } from './formatDateTime'
import type { MaintenanceInput, MaintenanceRecurrence } from '../types/maintenance'

// Maintenance times are typed in the Time Zone chosen in Settings (a fixed UTC offset, or the
// viewer's browser) and sent to the server as UTC. These helpers convert between the
// "YYYY-MM-DDTHH:mm" value of a datetime-local input and an ISO instant.

export const MAX_COMMENT_CHARS = 200
const DAY_MS = 24 * 60 * 60 * 1000
const MAX_ONE_OFF_MS = 30 * DAY_MS
const MAX_SPAN_MS = 366 * DAY_MS
const PERIOD_MS: Record<MaintenanceRecurrence, number | null> = { none: null, daily: DAY_MS, weekly: 7 * DAY_MS }

const INPUT_PATTERN = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/

function pad(n: number) {
  return String(n).padStart(2, '0')
}

/** The wall-clock text typed in `timeZone` as an ISO instant (UTC), or null if unreadable. */
export function inputToIso(value: string, timeZone: string): string | null {
  const match = INPUT_PATTERN.exec(value)
  if (!match) return null
  const [year, month, day, hour, minute] = match.slice(1).map(Number)
  if (timeZone === BROWSER_TIME_ZONE) {
    const local = new Date(year, month - 1, day, hour, minute)
    return Number.isNaN(local.getTime()) ? null : local.toISOString()
  }
  const wall = Date.UTC(year, month - 1, day, hour, minute)
  return new Date(wall - parseUtcOffsetMinutes(timeZone, new Date(wall)) * 60_000).toISOString()
}

/** An ISO instant as the wall-clock text for a datetime-local input in `timeZone`. */
export function isoToInput(value: string | null | undefined, timeZone: string): string {
  const date = parseServerDate(value)
  if (!date) return ''
  const zoned = new Date(date.getTime() + parseUtcOffsetMinutes(timeZone, date) * 60_000)
  return (
    `${zoned.getUTCFullYear()}-${pad(zoned.getUTCMonth() + 1)}-${pad(zoned.getUTCDate())}` +
    `T${pad(zoned.getUTCHours())}:${pad(zoned.getUTCMinutes())}`
  )
}

/**
 * The IANA zone sent with a window so a daily or weekly one keeps its local time across a
 * daylight-saving change. A fixed UTC offset has no daylight saving, so UTC repeats the same.
 */
export function recurrenceZone(timeZone: string): string {
  if (timeZone !== BROWSER_TIME_ZONE) return 'UTC'
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  } catch {
    return 'UTC'
  }
}

export type MaintenanceForm = {
  deviceId: number | null
  start: string
  end: string
  recurrence: MaintenanceRecurrence
  until: string
  comment: string
}

/** The same checks the server makes (maintenance.validate_window); returns the first problem. */
export function validateForm(form: MaintenanceForm, timeZone: string, now: Date = new Date()): string | null {
  const start = inputToIso(form.start, timeZone)
  const end = inputToIso(form.end, timeZone)
  if (!start) return 'Choose when the window starts.'
  if (!end) return 'Choose when the window ends.'
  const startMs = Date.parse(start)
  const endMs = Date.parse(end)
  if (endMs <= startMs) return 'The end must be after the start.'
  if (endMs <= now.getTime()) return 'The window must end in the future.'

  const period = PERIOD_MS[form.recurrence]
  if (period === null && endMs - startMs > MAX_ONE_OFF_MS) return 'A window can last at most 30 days.'
  if (period !== null && endMs - startMs > period) {
    return `A ${form.recurrence} window cannot last longer than one ${form.recurrence === 'daily' ? 'day' : 'week'}.`
  }

  if (period !== null && form.until) {
    const until = inputToIso(form.until, timeZone)
    if (!until) return 'Choose when the repeats stop, or leave it empty.'
    if (Date.parse(until) < startMs) return 'Repeats must not stop before the window starts.'
    if (Date.parse(until) - startMs > MAX_SPAN_MS) return 'Repeats can be scheduled at most 366 days ahead.'
  }

  const comment = form.comment.trim()
  if (!comment) return 'Add a reason for the maintenance.'
  if (comment.length > MAX_COMMENT_CHARS) return `The reason must be at most ${MAX_COMMENT_CHARS} characters.`
  return null
}

/** The request body for a valid form (call validateForm first). */
export function formToInput(form: MaintenanceForm, timeZone: string): MaintenanceInput {
  const repeats = form.recurrence !== 'none'
  return {
    deviceId: form.deviceId,
    startAt: inputToIso(form.start, timeZone) ?? '',
    endAt: inputToIso(form.end, timeZone) ?? '',
    recurrence: form.recurrence,
    recurrenceUntil: repeats && form.until ? inputToIso(form.until, timeZone) : null,
    timeZone: recurrenceZone(timeZone),
    comment: form.comment.trim(),
  }
}
