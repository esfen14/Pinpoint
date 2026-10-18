import type { ExportMeta } from '../utils/exportData'
import type { PeriodMeta } from '../types/report'

// Shared wording for the Reports page (#199): durations always carry units.

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '—'
  const total = Math.round(seconds)
  if (total === 0) return '0 s'
  const parts: string[] = []
  const days = Math.floor(total / 86400)
  const hours = Math.floor((total % 86400) / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const secs = total % 60
  if (days) parts.push(`${days} d`)
  if (hours) parts.push(`${hours} h`)
  if (minutes) parts.push(`${minutes} min`)
  if (secs && !days) parts.push(`${secs} s`)
  return parts.join(' ')
}

export function formatPct(value: number | null | undefined): string {
  return value == null ? '—' : `${value}%`
}

export function stateLabel(state: string): string {
  if (state === 'no_data') return 'No recorded data'
  return state.charAt(0).toUpperCase() + state.slice(1)
}

// State colours are always paired with the state's text, never colour alone.
export const STATE_COLOR: Record<string, string> = {
  up: '#16a34a', ok: '#16a34a', down: '#dc2626', critical: '#dc2626',
  warning: '#d97706', unreachable: '#9333ea', unknown: '#6b7280', no_data: '#9ca3af',
  DOWN: '#dc2626', CRITICAL: '#dc2626', WARNING: '#d97706', UNREACHABLE: '#9333ea',
  UNKNOWN: '#6b7280', UP: '#16a34a', OK: '#16a34a',
}

/** Context lines every export carries (#199): period, zone, generation time, source and warnings. */
export function exportMeta(
  period: PeriodMeta,
  extra: Record<string, string | null | undefined> = {},
  generatedAt?: string,
): ExportMeta {
  const zone = period.time_zone
  const meta: ExportMeta = {
    'Report period': `${period.start} to ${period.end}`,
    'Reporting time zone': zone ? `${zone.name} (UTC offset ${zone.utc_offset_seconds / 3600} h)` : 'server local time',
    'Generated at': generatedAt ?? new Date().toISOString(),
    Source: 'Nagios archive',
  }
  for (const [key, value] of Object.entries(extra)) if (value) meta[key] = value
  return meta
}
