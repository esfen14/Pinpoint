import type { Edge, Node } from '@xyflow/react'
import { deviceLabel, topologyNodeId, type TopologyData, type TopologyDevice } from '../types/topology'

export type DeviceNode = Node<{ label: string; device: TopologyDevice }, 'custom'>

// Longest-path layering keeps shared children below every parent. Each device
// appears once, including isolated roots. Layout is deterministic and not saved.
export function layoutTopology(data: TopologyData): { nodes: DeviceNode[]; edges: Edge[] } {
  const devices = new Map(data.devices.map(device => [topologyNodeId(device), device]))
  const incoming = new Map([...devices.keys()].map(id => [id, 0]))
  const children = new Map<string, string[]>()
  const depth = new Map([...devices.keys()].map(id => [id, 0]))
  const edges: Edge[] = []
  for (const edge of data.edges) {
    const source = `device-${edge.parent_id}`
    const target = `device-${edge.child_id}`
    if (!devices.has(source) || !devices.has(target)) continue
    incoming.set(target, incoming.get(target)! + 1)
    if (!children.has(source)) children.set(source, [])
    children.get(source)!.push(target)
    edges.push({ id: `${source}-${target}`, source, target, data: { ...edge },
      style: { stroke: edge.nagios_eligible ? '#64748b' : '#d97706', strokeDasharray: edge.nagios_eligible ? undefined : '6 4' },
      ariaLabel: `${deviceLabel(devices.get(source)!)} is a configured parent of ${deviceLabel(devices.get(target)!)}` })
  }
  const ready = [...incoming].filter(([, count]) => count === 0).map(([id]) => id).sort()
  for (let index = 0; index < ready.length; index++) {
    const id = ready[index]
    for (const child of children.get(id) ?? []) {
      depth.set(child, Math.max(depth.get(child)!, depth.get(id)! + 1))
      incoming.set(child, incoming.get(child)! - 1)
      if (incoming.get(child) === 0) ready.push(child)
    }
  }
  const layers = new Map<number, string[]>()
  for (const id of [...devices.keys()].sort()) {
    const level = depth.get(id)!
    if (!layers.has(level)) layers.set(level, [])
    layers.get(level)!.push(id)
  }
  const nodes: DeviceNode[] = []
  for (const [level, ids] of layers) {
    ids.forEach((id, column) => {
      const device = devices.get(id)!
      nodes.push({ id, type: 'custom', position: { x: (column - (ids.length - 1) / 2) * 280, y: level * 150 },
        data: { label: deviceLabel(device), device }, draggable: false, connectable: false })
    })
  }
  return { nodes, edges }
}
