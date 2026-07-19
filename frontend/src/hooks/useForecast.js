/**
 * NetElixIQ AI — useForecast hook
 * Manages forecast state, loading, and caching for a session.
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { forecastApi } from '@/services/api.js'

export function useForecast(sessionId, horizon = 30, metric = 'revenue') {
  const [forecast, setForecast] = useState(null)
  const [contribution, setContribution] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const fetch = useCallback(
    async (retrain = false) => {
      if (!sessionId) return
      setLoading(true)
      setError(null)

      try {
        const [forecastData, contribData] = await Promise.all([
          forecastApi.generate(sessionId, horizon, metric, retrain),
          forecastApi.getChannelContribution(sessionId, horizon),
        ])
        setForecast(forecastData)
        setContribution(contribData)
      } catch (err) {
        setError(err.message || 'Forecast failed')
      } finally {
        setLoading(false)
      }
    },
    [sessionId, horizon, metric]
  )

  useEffect(() => {
    fetch()
  }, [fetch])

  const refetch = useCallback(() => fetch(false), [fetch])
  const retrain = useCallback(() => fetch(true), [fetch])

  return {
    forecast,
    contribution,
    loading,
    error,
    refetch,
    retrain,
    // Derived values
    forecastData: forecast?.forecast || [],
    summary: forecast?.summary || {},
    confidence: forecast?.confidence || 0,
    modelWeights: forecast?.model_weights || {},
    mape: forecast?.training_stats?.lgbm_mape || 0,
  }
}
