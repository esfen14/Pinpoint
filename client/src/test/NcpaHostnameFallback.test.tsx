import { describe, it, expect } from 'vitest'
import { fromRawDevice, fromRawResult } from '../types/ncpaDeployment'

describe('NCPA Deployment device name', () => {
  const device = (hostname: string | null) => fromRawDevice({
    device_id: 1, hostname, ip_address: '10.0.20.9', trusted: true, fingerprint: null,
    agent_status: null, last_error: null, last_outcome: null, last_run_id: null, deployable: true,
  } as never)

  it('shows the hostname when there is one', () => {
    expect(device('web-01').hostname).toBe('web-01')
  })

  it('falls back to the IP address instead of "Unknown"', () => {
    expect(device('Unknown').hostname).toBe('10.0.20.9')
    expect(device(null).hostname).toBe('10.0.20.9')
  })

  it('applies the same fallback to run results', () => {
    const result = fromRawResult({ device_id: 2, hostname: 'Unknown', ip_address: '10.0.20.8', outcome: 'Failed', error: null } as never)
    expect(result.hostname).toBe('10.0.20.8')
  })
})
