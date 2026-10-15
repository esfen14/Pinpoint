import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Bandwidth } from '../../types/bandwidth'
import { bandwidthScale, formatBandwidth } from '../../utils/formatBandwidth'
import { formatBucketLabel } from '../../utils/formatBucketLabel'
import { useDisplayTime } from '../../hooks/useDisplayTime'

const IN_COLOR = '#38BDF8'
const OUT_COLOR = '#F4A90B'

type BandwidthChartProps = {
  data: Bandwidth
}

// In and out bandwidth as two lines. The whole chart shares one unit (bit/s up to Tbit/s), chosen
// from its largest value, so the axis stays readable and its label names the unit.
export function BandwidthChart({ data }: BandwidthChartProps) {
  const { timeZone } = useDisplayTime()
  const rows = data.inPoints.map((point, index) => ({
    time: formatBucketLabel(point.bucketStart, data.hours, timeZone),
    in: point.bps,
    out: data.outPoints[index]?.bps ?? null,
  }))

  const peak = Math.max(0, ...rows.flatMap((row) => [row.in ?? 0, row.out ?? 0]))
  const { unit, divisor } = bandwidthScale(peak)
  const scaled = rows.map((row) => ({
    time: row.time,
    in: row.in == null ? null : row.in / divisor,
    out: row.out == null ? null : row.out / divisor,
  }))

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={scaled} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: 'var(--chart-text)', fontSize: 11 }} />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--chart-text)', fontSize: 11 }}
            width={56}
            label={{ value: unit, angle: -90, position: 'insideLeft', fill: 'var(--chart-text)', fontSize: 11 }}
          />
          <Tooltip
            formatter={(value) => formatBandwidth(typeof value === 'number' ? value * divisor : null)}
            contentStyle={{ background: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: 12, color: 'var(--tooltip-text)' }}
            labelStyle={{ color: 'var(--tooltip-text)' }}
          />
          <Legend />
          <Line type="monotone" dataKey="in" name="In" stroke={IN_COLOR} strokeWidth={2} dot={false} connectNulls />
          <Line type="monotone" dataKey="out" name="Out" stroke={OUT_COLOR} strokeWidth={2} dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
