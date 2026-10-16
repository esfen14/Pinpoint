import { useEffect, useState } from 'react'
import { apiGet, errorMessage } from '../lib/api'
import { fromForecastResponse, type ForecastApiResponse, type ForecastData } from '../types/forecast'

// Forecasts are recomputed on the server every half hour, so there is no need to poll quickly.
const REFRESH_MS = 5 * 60 * 1000

/** Load the stored forecasts once and refresh them every few minutes. */
export function useForecasts() {
  const [data, setData] = useState<ForecastData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const response = await apiGet<ForecastApiResponse>('/api/system/forecast')
        if (!active) return
        setData(fromForecastResponse(response))
        setError(null)
      } catch (err) {
        if (active) setError(errorMessage(err, 'Unable to load forecasts.'))
      } finally {
        if (active) setIsLoading(false)
      }
    }
    load()
    const id = window.setInterval(load, REFRESH_MS)
    return () => {
      active = false
      window.clearInterval(id)
    }
  }, [])

  return { data, isLoading, error }
}
