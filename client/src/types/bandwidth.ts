// Mirrors the bandwidth routes in server/app/api/system/network_health_activity.py and the interface
// routes in server/app/api/system/device_interfaces.py. Wire records (snake_case) are converted here;
// the behaviour they drive is in spec files/Display_Requirements.md (Interface Bandwidth).

// --- GET /network-health/bandwidth/interfaces -------------------------------

export type BandwidthInterfaceChoice = {
  ifIndex: number
  name: string
  speedBps: number | null
}

export type BandwidthDevice = {
  hostname: string
  interfaces: BandwidthInterfaceChoice[]
}

type BandwidthChoicesApiResponse = {
  devices: { hostname: string; interfaces: { if_index: number; name: string; speed_bps: number | null }[] }[]
}

export function fromBandwidthChoicesResponse(data: BandwidthChoicesApiResponse | null): BandwidthDevice[] {
  return (data?.devices ?? []).map((device) => ({
    hostname: device.hostname,
    interfaces: device.interfaces.map((i) => ({ ifIndex: i.if_index, name: i.name, speedBps: i.speed_bps })),
  }))
}

// --- GET /network-health/bandwidth ------------------------------------------

export type BandwidthPoint = { bucketStart: string; bps: number | null }

export type Bandwidth = {
  hostname: string
  interface: { ifIndex: number; name: string | null; speedBps: number | null }
  hours: number
  // "insufficient_data": fewer than two valid counter samples in the window.
  status: 'ok' | 'insufficient_data'
  inPoints: BandwidthPoint[]
  outPoints: BandwidthPoint[]
  latest: {
    timestamp: string
    inBps: number | null
    outBps: number | null
    inUtilisationPct: number | null
    outUtilisationPct: number | null
  } | null
}

type PointApi = { bucket_start: string; bps: number | null }

export type BandwidthApiResponse = {
  hostname: string
  interface: { if_index: number; name: string | null; speed_bps: number | null }
  hours: number
  status: 'ok' | 'insufficient_data'
  in_points: PointApi[]
  out_points: PointApi[]
  latest: {
    timestamp: string
    in_bps: number | null
    out_bps: number | null
    in_utilisation_pct: number | null
    out_utilisation_pct: number | null
  } | null
}

const toPoint = (p: PointApi): BandwidthPoint => ({ bucketStart: p.bucket_start, bps: p.bps })

export function fromBandwidthResponse(data: BandwidthApiResponse): Bandwidth {
  return {
    hostname: data.hostname,
    interface: { ifIndex: data.interface.if_index, name: data.interface.name, speedBps: data.interface.speed_bps },
    hours: data.hours,
    status: data.status,
    inPoints: data.in_points.map(toPoint),
    outPoints: data.out_points.map(toPoint),
    latest: data.latest && {
      timestamp: data.latest.timestamp,
      inBps: data.latest.in_bps,
      outBps: data.latest.out_bps,
      inUtilisationPct: data.latest.in_utilisation_pct,
      outUtilisationPct: data.latest.out_utilisation_pct,
    },
  }
}

// --- /hosts/<id>/interfaces (Device Inventory drawer) -----------------------

export type DeviceInterface = {
  if_index: number
  name: string
  speed_bps: number | null
  admin_status: string | null
  oper_status: string | null
  monitored: boolean
  // False once a refresh no longer finds the interface on the device.
  present: boolean
  last_seen_at: string | null
}

export type DeviceInterfacesResponse = {
  device: { id: number; nagios_host_name: string }
  // SNMP is monitored on the device, so a refresh can work.
  snmp: boolean
  max_monitored: number
  interfaces: DeviceInterface[]
}

// Like the port-edit route: the change is saved, and config_ok says whether Nagios was brought up to date.
export type InterfaceChangeResult = DeviceInterfacesResponse & {
  config_applied: boolean
  config_ok: boolean
  config_message: string
}
