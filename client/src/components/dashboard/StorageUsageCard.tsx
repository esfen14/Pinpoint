import { useCurrentUser } from '../../contexts/CurrentUserContext'
import type { StorageUsage } from '../../types/dashboard'

function formatBytes(bytes: number | null): string {
  if (bytes == null) return 'Unavailable'
  const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
  const index = bytes > 0 ? Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1) : 0
  return `${Number((bytes / 1024 ** index).toFixed(1))} ${units[index]}`
}

export function StorageUsageCard({ usage, isLoading, error }: {
  usage: StorageUsage | null; isLoading: boolean; error: string | null
}) {
  const { hasPermission } = useCurrentUser()
  if (!hasPermission('system.dashboard')) return null
  const rows = usage ? [
    ...usage.databases.map((item) => ({ ...item, label: item.name, complete: true })),
    { ...usage.backups, label: 'Database backups' },
    { ...usage.archives, label: 'Nagios archives' },
  ] : []
  const low = rows.some(({ filesystem: fs }) => fs && fs.total_bytes > 0 && fs.free_bytes / fs.total_bytes < 0.1)
  return (
    <section aria-label="Appliance storage" className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-[var(--dash-card-padding)] text-[var(--text)]">
      <h2 className="text-base font-semibold">Appliance storage</h2>
      <p className="mt-1 text-xs text-[var(--text-muted)]">Database, backup and Nagios archive sizes. A warning appears below 10% free disk space.</p>
      {isLoading ? <p className="mt-3 text-sm">Loading storage usage…</p>
        : error ? <p role="alert" className="mt-3 text-sm text-red-600">{error}</p>
        : !usage ? <p className="mt-3 text-sm">Storage usage is unavailable.</p>
        : <>
          {low && <p role="alert" className="mt-3 rounded-lg bg-amber-100 p-2 text-sm text-amber-900">Low disk space: a storage location is below 10% free. Review backups and log retention.</p>}
          <dl className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {rows.map((item, index) => (
              <div key={`${item.label}-${index}`} className="rounded-lg bg-[var(--hover)] p-3">
                <dt className="text-xs text-[var(--text-muted)]">{item.label}</dt>
                <dd className="mt-1 text-sm font-medium">{!item.complete && item.bytes != null ? 'At least ' : ''}{formatBytes(item.bytes)}</dd>
                <dd className="mt-1 text-xs text-[var(--text-muted)]">{item.filesystem ? `${formatBytes(item.filesystem.free_bytes)} free of ${formatBytes(item.filesystem.total_bytes)} on its disk` : 'Disk space unavailable'}</dd>
                {!item.complete && item.bytes != null && <dd className="text-xs text-[var(--text-muted)]">Partial folder scan</dd>}
              </div>
            ))}
          </dl>
          {usage.databases.length === 0 && <p className="mt-2 text-xs text-[var(--text-muted)]">No database files are configured.</p>}
        </>}
    </section>
  )
}
