import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { errorMessage } from '../../lib/api'
import { getBandwidth, getBandwidthChoices } from '../../lib/bandwidthApi'
import type { Bandwidth, BandwidthDevice } from '../../types/bandwidth'
import { formatBandwidth, formatLinkSpeed } from '../../utils/formatBandwidth'
import { BANDWIDTH_HOURS_OPTIONS, type TrendHours } from '../../utils/trendHours'
import { DropdownSelect } from '../shared/DropdownSelect'
import { BandwidthChart } from './BandwidthChart'
import { TimeRangeSelect } from './TimeRangeSelect'

type Choices = { devices: BandwidthDevice[] | null; error: string | null }
// What the chart area shows for the current device, interface and range.
type Reading = { key: string; data: Bandwidth | null; error: string | null }

// Interface Bandwidth (spec files/Display_Requirements.md): the in and out bit rate of one interface of
// an SNMP device. The device and interface lists come from GET /network-health/bandwidth/interfaces and
// the rates from GET /network-health/bandwidth; the server computes them from the stored octet counters.
// It loads its own data, so a failure here never blanks the rest of the page.
type BandwidthCardProps = {
  // Called with the reading on screen (null while loading, on an error or with nothing chosen), so the
  // page can show the same interface in its side widget.
  onReading?: (reading: Bandwidth | null) => void
}

export function BandwidthCard({ onReading }: BandwidthCardProps = {}) {
  const [choices, setChoices] = useState<Choices>({ devices: null, error: null })
  const [choicesKey, setChoicesKey] = useState(0)
  const [hostname, setHostname] = useState<string | null>(null)
  const [ifIndex, setIfIndex] = useState<number | null>(null)
  const [hours, setHours] = useState<TrendHours>(24)
  const [reading, setReading] = useState<Reading | null>(null)

  useEffect(() => {
    let cancelled = false
    getBandwidthChoices()
      .then((devices) => {
        if (cancelled) return
        setChoices({ devices, error: null })
        const first = devices.find((device) => device.interfaces.length > 0)
        setHostname((current) => current ?? first?.hostname ?? null)
        setIfIndex((current) => current ?? first?.interfaces[0].ifIndex ?? null)
      })
      .catch((err) => {
        if (!cancelled) setChoices({ devices: null, error: errorMessage(err, 'Unable to load the SNMP devices.') })
      })
    return () => {
      cancelled = true
    }
  }, [choicesKey])

  const device = choices.devices?.find((d) => d.hostname === hostname) ?? null
  const selected = device?.interfaces.find((i) => i.ifIndex === ifIndex) ?? null
  const requestKey = selected && hostname ? `${hostname}:${selected.ifIndex}:${hours}` : null

  useEffect(() => {
    if (!requestKey || !hostname || !selected) return
    let cancelled = false
    getBandwidth(hostname, selected.ifIndex, hours)
      .then((data) => {
        if (!cancelled) setReading({ key: requestKey, data, error: null })
      })
      .catch((err) => {
        if (!cancelled) setReading({ key: requestKey, data: null, error: errorMessage(err, 'Unable to load the bandwidth.') })
      })
    return () => {
      cancelled = true
    }
    // selected is derived from hostname, choices and requestKey; requestKey changes with all of them.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestKey])

  const reloadChoices = useCallback(() => {
    setChoices({ devices: null, error: null })
    setChoicesKey((key) => key + 1)
  }, [])

  function chooseDevice(name: string) {
    const next = choices.devices?.find((d) => d.hostname === name)
    setHostname(name)
    setIfIndex(next?.interfaces[0]?.ifIndex ?? null)
  }

  const current = reading && reading.key === requestKey ? reading : null
  const data = current?.data ?? null
  useEffect(() => {
    onReading?.(data)
  }, [data, onReading])

  const hasPoints = !!data && [...data.inPoints, ...data.outPoints].some((point) => point.bps != null)
  const speed = formatLinkSpeed(data?.interface.speedBps ?? selected?.speedBps)

  const title = 'Interface Bandwidth'
  let body
  if (choices.error) {
    body = (
      <div className="space-y-2">
        <p className="text-sm text-red-600 dark:text-red-400">{choices.error}</p>
        <button
          type="button"
          onClick={reloadChoices}
          className="rounded-lg border border-[var(--border)] px-3 py-1 text-xs font-medium text-[var(--text)] hover:bg-[var(--hover)]"
        >
          Retry
        </button>
      </div>
    )
  } else if (!choices.devices) {
    body = (
      <p className="flex items-center text-sm text-[var(--text-muted)]">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading SNMP devices…
      </p>
    )
  } else if (choices.devices.length === 0) {
    body = (
      <p className="py-6 text-center text-sm text-[var(--text-muted)]">
        No SNMP device is monitored yet. Bandwidth is read from devices that answer SNMP; run a scan from Network Discovery to find them.
      </p>
    )
  } else if (!device || !selected) {
    body = (
      <p className="py-6 text-center text-sm text-[var(--text-muted)]">
        No interface is monitored yet. Open a device in <Link to="/device-inventory" className="underline">Device Inventory</Link> and
        turn on monitoring for an interface to chart its bandwidth.
      </p>
    )
  } else if (!current) {
    body = (
      <p className="flex items-center py-6 text-sm text-[var(--text-muted)]">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading bandwidth…
      </p>
    )
  } else if (current.error) {
    body = <p role="alert" className="py-6 text-center text-sm text-red-600 dark:text-red-400">{current.error}</p>
  } else if (data && data.status === 'insufficient_data') {
    body = (
      <p className="py-6 text-center text-sm text-[var(--text-muted)]">
        Insufficient data: a rate needs at least two readings from the interface in this time range. Check back after the next few
        SNMP checks, or choose a longer range.
      </p>
    )
  } else if (data && !hasPoints) {
    body = <p className="py-6 text-center text-sm text-[var(--text-muted)]">No bandwidth data in the selected time window.</p>
  } else if (data) {
    body = (
      <>
        {data.latest && (
          <dl className="mb-3 flex flex-wrap gap-x-8 gap-y-1 text-sm">
            <div>
              <dt className="text-[var(--text-muted)]">In (latest)</dt>
              <dd className="font-semibold text-[var(--text)]">
                {formatBandwidth(data.latest.inBps)}
                {data.latest.inUtilisationPct != null && ` · ${data.latest.inUtilisationPct.toFixed(1)}% of link`}
              </dd>
            </div>
            <div>
              <dt className="text-[var(--text-muted)]">Out (latest)</dt>
              <dd className="font-semibold text-[var(--text)]">
                {formatBandwidth(data.latest.outBps)}
                {data.latest.outUtilisationPct != null && ` · ${data.latest.outUtilisationPct.toFixed(1)}% of link`}
              </dd>
            </div>
            {speed && (
              <div>
                <dt className="text-[var(--text-muted)]">Link speed</dt>
                <dd className="font-semibold text-[var(--text)]">{speed}</dd>
              </div>
            )}
          </dl>
        )}
        <BandwidthChart data={data} />
      </>
    )
  }

  const ready = !!choices.devices && choices.devices.length > 0

  return (
    <div id="interface-bandwidth" className="rounded-2xl bg-[var(--card)] border border-[var(--border)] p-5 shadow-sm">
      <div className="mb-1 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-[var(--text)]">{title}</h3>
          <p className="text-sm text-[var(--text-muted)]">Datasource: SNMP ifInOctets / ifOutOctets</p>
        </div>
        {ready && (
          <div className="flex flex-wrap items-center gap-2">
            <TimeRangeSelect hours={hours} onChange={setHours} options={BANDWIDTH_HOURS_OPTIONS} />
            <DropdownSelect
              label="Device"
              value={hostname}
              options={choices.devices!.map((d) => ({ value: d.hostname, label: d.hostname }))}
              onChange={chooseDevice}
            />
            <DropdownSelect
              label="Interface"
              value={ifIndex}
              options={(device?.interfaces ?? []).map((i) => ({ value: i.ifIndex, label: i.name }))}
              onChange={setIfIndex}
              disabled={!device || device.interfaces.length === 0}
            />
          </div>
        )}
      </div>
      <p className="mb-4 text-xs text-[var(--text-muted)]">
        Data sent and received by an interface. Add interfaces in Device Inventory.
      </p>
      {body}
    </div>
  )
}
