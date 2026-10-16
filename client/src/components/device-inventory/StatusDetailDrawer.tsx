import { DeviceIdentityReviews } from './DeviceIdentityReviews'
import type { MergeResult } from '../../types/deviceIdentity'
import { useEffect, useState } from 'react'

import { apiDelete, apiGet, apiPost, errorMessage } from '../../lib/api'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { DeviceParentSection } from './DeviceParentSection'
import { DeviceMonitoringSection } from './DeviceMonitoringSection'
import { DeviceRecipientsSection } from './DeviceRecipientsSection'
import { DeviceInterfacesSection } from './DeviceInterfacesSection'
import { DeviceSnmpSection } from './DeviceSnmpSection'
import { DevicePortsSection } from './DevicePortsSection'
import { FlapHistorySection } from './FlapHistorySection'
import type { MonitoringState } from '../../types/host'
import { useDisplayTime } from '../../hooks/useDisplayTime'
import { DrawerShell } from '../shared/DrawerShell'
import { CheckNowButton } from '../shared/CheckNowButton'
import { NagiosSyncNotice } from '../shared/NagiosSyncNotice'
import { nagiosSyncNotice, type NagiosSyncResult } from '../../types/nagiosSync'


type PerfMetric = {
  metric: string
  value: number
  unit: string | null
  warn: number | null
  crit: number | null
  min: number | null
  max: number | null
}

type Detail = {
  hostname: string
  // The discovered device behind this host; null for a host with no device record (e.g. localhost).
  device_id?: number | null
  monitoring_state?: MonitoringState | null
  service?: string
  state: string
  state_type: string
  plugin_output: string
  check_latency: number
  check_execution_time: number
  is_flapping: boolean
  in_downtime: boolean
  nagios_ack: string
  ack: { comment: string; acknowledged_by: string; acknowledged_at: string } | null
  perf_data: PerfMetric[]
  services?: { service: string; state: string; plugin_output: string; last_check: string | null }[]
} & Record<string, unknown>

type Props = {
  hostname: string
  onClose: () => void
  // Called after the device was paused or resumed, so the host table can load again.
  onMonitoringChanged?: () => void
  onIdentityMerged?: (result: MergeResult) => void
}

const TIMESTAMP_LABELS: Record<string, string> = {
  last_check: 'Last check',
  last_state_change: 'Last state change',
  last_hard_state_change: 'Last hard state change',
  last_time_up: 'Last up',
  last_time_down: 'Last down',
  last_time_unreachable: 'Last unreachable',
  last_time_ok: 'Last OK',
  last_time_warning: 'Last warning',
  last_time_critical: 'Last critical',
  last_time_unknown: 'Last unknown',
}

function stateClass(state: string) {
  switch (state.toUpperCase()) {
    case 'UP':
    case 'OK':
      return 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
    case 'WARNING':
      return 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
    case 'DOWN':
    case 'CRITICAL':
    case 'UNREACHABLE':
      return 'bg-red-500/15 text-red-600 dark:text-red-400'
    default:
      return 'bg-gray-500/15 text-[var(--text-muted)]'
  }
}

function threshold(value: number | null, unit: string | null) {
  return value == null ? '—' : `${value}${unit ?? ''}`
}

export function StatusDetailDrawer({ hostname, onClose, onMonitoringChanged, onIdentityMerged }: Props) {
  const { formatDateTime } = useDisplayTime()
  const [service, setService] = useState<string | null>(null)
  const [detail, setDetail] = useState<Detail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { hasPermission } = useCurrentUser()
  const [reloadKey, setReloadKey] = useState(0)
  const [comment, setComment] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [ackError, setAckError] = useState<string | null>(null)
  const [syncNotice, setSyncNotice] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setDetail(null)
    setError(null)
    const path = service
      ? `/api/system/network-health/services/${encodeURIComponent(hostname)}/${service
          .split('/')
          .map(encodeURIComponent)
          .join('/')}/detail`
      : `/api/system/network-health/hosts/${encodeURIComponent(hostname)}/detail`
    apiGet<Detail>(path)
      .then((data) => {
        if (!cancelled) setDetail(data)
      })
      .catch((err) => {
        if (!cancelled) setError(errorMessage(err, 'Unable to load details.'))
      })
    return () => {
      cancelled = true
    }
  }, [hostname, service, reloadKey])

  useEffect(() => {
    setComment('')
    setAckError(null)
    setSyncNotice(null)
  }, [hostname, service])

  async function changeAcknowledgement(acknowledge: boolean) {
    if (!service) return
    setIsSaving(true)
    setAckError(null)
    setSyncNotice(null)
    try {
      let result: NagiosSyncResult | undefined
      if (acknowledge) {
        result = await apiPost<NagiosSyncResult>('/api/system/network-health/services/acknowledge', {
          hostname,
          service_name: service,
          comment: comment.trim(),
        })
      } else {
        result = await apiDelete<NagiosSyncResult>('/api/system/network-health/services/acknowledge', {
          hostname,
          service_name: service,
        })
      }
      setComment('')
      setSyncNotice(nagiosSyncNotice(result))
      setReloadKey((k) => k + 1)
    } catch (err) {
      setAckError(errorMessage(err, acknowledge ? 'Unable to acknowledge service.' : 'Unable to remove acknowledgement.'))
    } finally {
      setIsSaving(false)
    }
  }

  const timestamps = detail
    ? Object.keys(TIMESTAMP_LABELS).filter((key) => key in detail)
    : []

  return (
    <DrawerShell
      title={service ? `${hostname} / ${service}` : hostname}
      onBack={service ? () => setService(null) : undefined}
      backLabel="Back to host"
      onClose={onClose}
    >
          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-red-600 dark:text-red-400">
              {error}
            </div>
          )}
          {!detail && !error && <p className="py-10 text-center text-[var(--text-muted)]">Loading…</p>}

          {detail && (
            <>
              <section className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`rounded-full px-2.5 py-0.5 text-[13px] font-medium ${stateClass(detail.state)}`}>
                    {detail.state}
                  </span>
                  <span className="text-[13px] text-[var(--text-muted)]">{detail.state_type}</span>
                  {detail.is_flapping && <span className="text-[13px] text-amber-600 dark:text-amber-400">Flapping</span>}
                  {detail.in_downtime && <span className="text-[13px] text-[var(--text-muted)]">In downtime</span>}
                </div>
                <pre className="whitespace-pre-wrap break-words font-mono text-[13px] text-[var(--text-muted)]">
                  {detail.plugin_output || '—'}
                </pre>
                <p className="text-[13px] text-[var(--text-muted)]">
                  Check latency {detail.check_latency.toFixed(3)}s · execution {detail.check_execution_time.toFixed(3)}s
                </p>
                {detail.ack && (
                  <p>
                    Acknowledged by <strong>{detail.ack.acknowledged_by}</strong> —{' '}
                    <span className="text-[var(--text-muted)]">{detail.ack.comment}</span>
                  </p>
                )}
              </section>

              <NagiosSyncNotice message={syncNotice} onDismiss={() => setSyncNotice(null)} />

              {!service && detail.device_id != null && hasPermission('system.discover') && (
                <DeviceIdentityReviews deviceId={detail.device_id} onMerged={result => {
                  setReloadKey(k => k + 1)
                  onIdentityMerged?.(result)
                  onMonitoringChanged?.()
                }} />
              )}

              <CheckNowButton hostname={hostname} service={service ?? undefined} />

              {!service && detail.device_id != null && detail.monitoring_state && (
                <DeviceMonitoringSection
                  key={detail.device_id}
                  deviceId={detail.device_id}
                  hostname={hostname}
                  state={detail.monitoring_state}
                  onChanged={() => {
                    setReloadKey((k) => k + 1)
                    onMonitoringChanged?.()
                  }}
                />
              )}

              {service && hasPermission('system.acknowledge_alerts') && (
                <section>
                  <h3 className="mb-2 text-[17px] font-semibold">Acknowledgement</h3>
                  {detail.ack ? (
                    <button
                      type="button"
                      disabled={isSaving}
                      onClick={() => changeAcknowledgement(false)}
                      className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-[13px] text-[var(--text)] hover:bg-[var(--hover)] disabled:opacity-50"
                    >
                      {isSaving ? 'Saving…' : 'Unacknowledge'}
                    </button>
                  ) : detail.state.toUpperCase() === 'OK' ? (
                    <p className="text-[var(--text-muted)]">This service is OK; there is nothing to acknowledge.</p>
                  ) : (
                    <div className="space-y-2">
                      <textarea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        rows={2}
                        placeholder="Comment explaining the acknowledgement"
                        aria-label="Acknowledgement comment"
                        className="w-full rounded-lg border border-[var(--border)] bg-[var(--input-bg)] px-3 py-2 text-[15px] text-[var(--text)] outline-none focus:border-[#ffb100]"
                      />
                      <button
                        type="button"
                        disabled={isSaving || !comment.trim()}
                        onClick={() => changeAcknowledgement(true)}
                        className="rounded-lg bg-[#ffb100] px-3 py-1.5 text-[13px] font-semibold text-black disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isSaving ? 'Saving…' : 'Acknowledge'}
                      </button>
                    </div>
                  )}
                  {ackError && <p className="mt-2 text-[13px] text-red-600 dark:text-red-400">{ackError}</p>}
                </section>
              )}

              <section>
                <h3 className="mb-2 text-[17px] font-semibold">Timestamps</h3>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
                  {timestamps.map((key) => {
                    const value = detail[key] as string | null
                    return (
                      <div key={key}>
                        <dt className="text-[13px] text-[var(--text-muted)]">{TIMESTAMP_LABELS[key]}</dt>
                        <dd>{formatDateTime(value)}</dd>
                      </div>
                    )
                  })}
                </dl>
              </section>

              <section>
                <h3 className="mb-2 text-[17px] font-semibold">Performance data</h3>
                {detail.perf_data.length === 0 ? (
                  <p className="text-[var(--text-muted)]">No performance data reported.</p>
                ) : (
                  <table className="w-full text-left text-[13px]">
                    <thead className="text-[var(--text-muted)]">
                      <tr>
                        <th className="py-1 pr-2 font-medium">Metric</th>
                        <th className="py-1 pr-2 font-medium">Value</th>
                        <th className="py-1 pr-2 font-medium">Warn</th>
                        <th className="py-1 font-medium">Crit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.perf_data.map((m) => (
                        <tr key={m.metric} className="border-t border-[var(--border)]">
                          <td className="py-1.5 pr-2">{m.metric}</td>
                          <td className="py-1.5 pr-2">{m.value}{m.unit ?? ''}</td>
                          <td className="py-1.5 pr-2">{threshold(m.warn, m.unit)}</td>
                          <td className="py-1.5">{threshold(m.crit, m.unit)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </section>

              {hasPermission('system.network_health') && (<FlapHistorySection hostname={hostname} service={service} />)}

              {!service && detail.services && (
                <section>
                  <h3 className="mb-2 text-[17px] font-semibold">Services</h3>
                  {detail.services.length === 0 ? (
                    <p className="text-[var(--text-muted)]">No services are monitored on this host.</p>
                  ) : (
                    <ul className="divide-y divide-[var(--border)]">
                      {detail.services.map((s) => (
                        <li key={s.service}>
                          <button
                            type="button"
                            onClick={() => setService(s.service)}
                            className="flex w-full items-center justify-between gap-3 py-2 text-left hover:bg-[var(--hover)]"
                          >
                            <span>{s.service}</span>
                            <span className={`rounded-full px-2.5 py-0.5 text-[13px] font-medium ${stateClass(s.state)}`}>
                              {s.state}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              )}

              {!service && detail.device_id != null && (
                <DeviceParentSection key={`parents-${detail.device_id}`} deviceId={detail.device_id} onChanged={onMonitoringChanged} />
              )}

              {!service && detail.device_id != null && hasPermission('system.hosts.alerts') && (
                <DeviceRecipientsSection key={`recipients-${detail.device_id}`} deviceId={detail.device_id} />
              )}

              {!service && detail.device_id != null && hasPermission('system.hosts') && (
                <DeviceSnmpSection key={`snmp-${detail.device_id}`} deviceId={detail.device_id} hostname={hostname} />
              )}
              {!service && detail.device_id != null && hasPermission('system.hosts') && (
                <DevicePortsSection key={detail.device_id} deviceId={detail.device_id} hostname={hostname} />
              )}

              {!service && detail.device_id != null && hasPermission('system.hosts') && (
                <DeviceInterfacesSection key={`interfaces-${detail.device_id}`} deviceId={detail.device_id} hostname={hostname} />
              )}
            </>
          )}
    </DrawerShell>
  )
}
