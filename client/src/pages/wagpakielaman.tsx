import { useCallback, useEffect, useMemo, useState } from 'react'
import { ReactFlow, Background, Controls, Handle, Position, type NodeProps, type Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Server, X } from 'lucide-react'
import { DeviceParentSection } from '../components/device-inventory/DeviceParentSection'
import { useSystemSettings } from '../contexts/SystemSettingsContext'
import { useDisplayTime } from '../hooks/useDisplayTime'
import { errorMessage } from '../lib/api'
import { getTopology } from '../lib/topologyApi'
import { layoutTopology, type DeviceNode } from '../lib/topologyLayout'
import { deviceLabel, topologyNodeId, type TopologyData, type TopologyDevice } from '../types/topology'

function stateLabel(device: TopologyDevice): string {
  const state = device.monitoring_state
  if (state && state !== 'monitored' && state !== 'missing') return state.replaceAll('_', ' ')
  return device.host_state ?? 'Not checked yet'
}

function CustomNode({ data }: NodeProps<DeviceNode>) {
  const state = stateLabel(data.device)
  const color = state === 'UP' ? 'border-emerald-500' : state === 'DOWN' || state === 'UNREACHABLE' ? 'border-red-500' : 'border-slate-400'
  return <div className={`w-60 rounded-lg border bg-[var(--card)] px-3 py-2 text-[var(--text)] shadow ${color}`}>
    <Handle type="target" position={Position.Top} isConnectable={false} />
    <div className="flex items-center gap-2"><Server className="h-4 w-4 shrink-0" /><span className="truncate text-sm font-medium">{data.label}</span></div>
    <p className="mt-1 text-xs text-[var(--text-muted)]">{state}</p>
    <Handle type="source" position={Position.Bottom} isConnectable={false} />
  </div>
}
const nodeTypes = { custom: CustomNode }
type Selected = { type: 'device'; id: string } | { type: 'link'; id: string } | null

export function TopologyPage() {
  const { settings } = useSystemSettings()
  const { formatDateTime } = useDisplayTime()
  const [data, setData] = useState<TopologyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Selected>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const reload = useCallback(() => setReloadKey(value => value + 1), [])

  useEffect(() => {
    let cancelled = false
    let inFlight = false
    async function load() {
      if (inFlight) return
      inFlight = true
      setError(null)
      try {
        const result = await getTopology()
        if (!cancelled) setData(result)
      } catch (err) {
        if (!cancelled) setError(errorMessage(err, 'Unable to load topology.'))
      } finally {
        inFlight = false
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    const minutes = Number(settings.dashboardRefreshRate)
    const timer = Number.isFinite(minutes) && minutes > 0 ? window.setInterval(load, minutes * 60 * 1000) : null
    return () => { cancelled = true; if (timer !== null) window.clearInterval(timer) }
  }, [reloadKey, settings.dashboardRefreshRate])

  const graph = useMemo(() => layoutTopology(data ?? { devices: [], edges: [], suggested_gateway_id: null }), [data])
  const device = selected?.type === 'device' ? data?.devices.find(d => topologyNodeId(d) === selected.id) : null
  const edge = selected?.type === 'link' ? graph.edges.find(e => e.id === selected.id) : null
  const parent = edge ? data?.devices.find(d => topologyNodeId(d) === edge.source) : null
  const child = edge ? data?.devices.find(d => topologyNodeId(d) === edge.target) : null

  return <main className="ml-55 flex-1 p-6 text-[var(--text)]">
    <div className="rounded-3xl bg-[var(--card)] p-6 shadow-lg">
      <div className="flex items-center justify-between"><h1 className="text-2xl font-semibold">Network Topology</h1><button type="button" onClick={reload} className="rounded border px-3 py-2">Refresh</button></div>
      <p className="mt-2 text-sm text-[var(--text-muted)]">Inventory devices and their manually configured parents. Lines show reachability relationships. Dashed amber lines indicate parents omitted from Nagios. Layout is automatic.</p>
      {loading && <p role="status" className="mt-4">Loading topology…</p>}
      {error && <div role="alert" className="mt-4">{error} <button type="button" onClick={reload}>Retry</button></div>}
      {!loading && data?.devices.length === 0 && <p className="mt-4">No inventory devices yet.</p>}
      {!!data?.devices.length && <div className="mt-6 flex flex-wrap gap-4">
        <div className="h-[600px] min-w-0 flex-1 basis-96 overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--bg)]">
          <ReactFlow nodes={graph.nodes} edges={graph.edges} nodeTypes={nodeTypes}
            nodesDraggable={false} nodesConnectable={false} edgesReconnectable={false}
            onNodeClick={(_, node: DeviceNode) => setSelected({ type: 'device', id: node.id })}
            onEdgeClick={(_, item: Edge) => setSelected({ type: 'link', id: item.id })}
            onPaneClick={() => setSelected(null)} fitView>
            <Background color="#64748b" /><Controls showInteractive={false} />
          </ReactFlow>
        </div>
        {(device || edge) && <aside className="w-80 max-w-full shrink-0 space-y-4" aria-label="Topology selection">
          <button type="button" onClick={() => setSelected(null)} aria-label="Close details" className="float-right"><X className="h-5 w-5" /></button>
          {device && <>
            <section className="space-y-2 rounded-xl border border-[var(--border)] p-4">
              <h2 className="font-semibold">Device Information</h2>
              <dl className="space-y-2 break-words text-sm">
                <dt>Name</dt><dd>{deviceLabel(device)}</dd>
                <dt>Host name</dt><dd>{device.nagios_host_name}</dd>
                <dt>Device ID</dt><dd>{device.id ?? 'No discovery record'}</dd>
                <dt>IP address</dt><dd>{device.ip_address ?? 'Not available'}</dd>
                <dt>Operating system</dt><dd>{device.os ?? 'Not available'}</dd>
                <dt>Monitoring</dt><dd>{device.monitoring_state?.replaceAll('_', ' ') ?? 'Nagios host'}</dd>
                <dt>Host status</dt><dd>{stateLabel(device)}</dd>
                <dt>Last check</dt><dd>{device.last_check ? formatDateTime(device.last_check) : 'Not available'}</dd>
                <dt>Last seen</dt><dd>{device.last_seen_at ? formatDateTime(device.last_seen_at) : 'Not available'}</dd>
              </dl>
            </section>
            {device.id !== null && <DeviceParentSection key={device.id} deviceId={device.id} topology={data!} onChanged={reload} />}
            {device.id === null && <p className="text-sm">Parent editing requires a discovered device record.</p>}
          </>}
          {edge && parent && child && <section className="space-y-3 rounded-xl border border-[var(--border)] p-4">
            <h2 className="font-semibold">Parent Relationship</h2>
            <p>Parent: {deviceLabel(parent)}</p><p>Child: {deviceLabel(child)}</p>
            <p className="text-sm">{edge.data?.nagios_eligible ? 'This configured parent is eligible for Nagios.' : String(edge.data?.omission_reason ?? 'This parent is omitted from Nagios.')}</p>
            <button type="button" onClick={() => setSelected({ type: 'device', id: topologyNodeId(child) })} className="rounded border px-3 py-2">View child and parents</button>
          </section>}
        </aside>}
      </div>}
    </div>
  </main>
}
export default TopologyPage
