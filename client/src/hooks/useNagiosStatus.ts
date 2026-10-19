import { useEffect, useState } from 'react'
import type { DashboardStatus } from '../types/dashboard'
import { serverDate } from '../utils/formatDateTime'

/** Interpret a recorded Nagios snapshot without treating an old PID as live proof. */
export function useNagiosStatus(status: DashboardStatus | null) {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 15_000)
    return () => window.clearInterval(id)
  }, [])
  const nagios = status?.nagios
  const updated = nagios?.lastStatusUpdate ? serverDate(nagios.lastStatusUpdate) : null
  const age = updated ? now.getTime() - updated.getTime() : NaN
  const stale = !Number.isFinite(age) || age >= 3 * 60_000 || age < -60_000
  const stopped = nagios?.running === false
  return { now, stopped, unavailable: stopped || stale, stale }
}
