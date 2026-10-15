// Bandwidth is measured in bit/s; these helpers pick the unit that keeps the number short
// (bit/s, kbit/s, Mbit/s, Gbit/s, Tbit/s) using decimal steps of 1000, as network speeds are quoted.

const UNITS = ['bit/s', 'kbit/s', 'Mbit/s', 'Gbit/s', 'Tbit/s']

export type BandwidthScale = { unit: string; divisor: number }

/** The unit for a whole chart, chosen from its largest value so every tick shares one unit. */
export function bandwidthScale(maxBps: number | null | undefined): BandwidthScale {
  let step = 0
  let value = Math.abs(maxBps ?? 0)
  while (value >= 1000 && step < UNITS.length - 1) {
    value /= 1000
    step += 1
  }
  return { unit: UNITS[step], divisor: 1000 ** step }
}

/** "1.5 Mbit/s": a single value in its own best unit. "—" when there is no value. */
export function formatBandwidth(bps: number | null | undefined): string {
  if (bps == null || !Number.isFinite(bps)) return '—'
  const { unit, divisor } = bandwidthScale(bps)
  const scaled = bps / divisor
  const digits = scaled >= 100 || unit === 'bit/s' ? 0 : scaled >= 10 ? 1 : 2
  return `${scaled.toFixed(digits)} ${unit}`
}

/** The speed of a link ("1 Gbit/s"), or null when unknown. */
export function formatLinkSpeed(bps: number | null | undefined): string | null {
  return bps ? formatBandwidth(bps) : null
}
