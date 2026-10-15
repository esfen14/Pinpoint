import { describe, expect, it } from 'vitest'
import { bandwidthScale, formatBandwidth, formatLinkSpeed } from '../utils/formatBandwidth'

describe('formatBandwidth', () => {
  it.each([
    [0, '0 bit/s'],
    [999, '999 bit/s'],
    [1000, '1.00 kbit/s'],
    [12_500, '12.5 kbit/s'],
    [1_500_000, '1.50 Mbit/s'],
    [250_000_000, '250 Mbit/s'],
    [1_000_000_000, '1.00 Gbit/s'],
    [9_990_000_000, '9.99 Gbit/s'],
    [100e9, '100 Gbit/s'],
    [2e12, '2.00 Tbit/s'],
  ])('%d bit/s is shown as %s', (bps, text) => {
    expect(formatBandwidth(bps)).toBe(text)
  })

  it('shows a dash when there is no value', () => {
    expect(formatBandwidth(null)).toBe('—')
    expect(formatBandwidth(undefined)).toBe('—')
    expect(formatBandwidth(Number.NaN)).toBe('—')
  })

  it('never goes beyond Tbit/s', () => {
    expect(bandwidthScale(5e15).unit).toBe('Tbit/s')
  })

  it('picks one unit for a whole chart from its peak', () => {
    expect(bandwidthScale(0)).toEqual({ unit: 'bit/s', divisor: 1 })
    expect(bandwidthScale(45_000)).toEqual({ unit: 'kbit/s', divisor: 1000 })
    expect(bandwidthScale(3_200_000)).toEqual({ unit: 'Mbit/s', divisor: 1_000_000 })
    expect(bandwidthScale(1_000_000_000)).toEqual({ unit: 'Gbit/s', divisor: 1_000_000_000 })
  })

  it('formats a link speed, or nothing when unknown', () => {
    expect(formatLinkSpeed(1_000_000_000)).toBe('1.00 Gbit/s')
    expect(formatLinkSpeed(null)).toBeNull()
    expect(formatLinkSpeed(0)).toBeNull()
  })
})
