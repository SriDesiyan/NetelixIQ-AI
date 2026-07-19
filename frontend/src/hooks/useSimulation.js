/**
 * NetElixIQ AI — useSimulation hook
 * Debounced Monte Carlo budget simulation with auto-fire on budget changes.
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { simulateApi } from '@/services/api.js'

const DEFAULT_BUDGETS = { google: 15000, meta: 8000, microsoft: 3000 }
const DEBOUNCE_MS = 600

export function useSimulation(sessionId, initialBudgets = DEFAULT_BUDGETS, horizonDays = 30) {
  const [budgets, setBudgets] = useState(initialBudgets)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const debounceRef = useRef(null)

  const run = useCallback(async (b = budgets) => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const data = await simulateApi.runBudget({
        session_id: sessionId,
        google_budget: b.google,
        meta_budget: b.meta,
        microsoft_budget: b.microsoft,
        horizon_days: horizonDays,
      })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Simulation failed')
    } finally {
      setLoading(false)
    }
  }, [sessionId, horizonDays])

  // Debounce on budget changes
  const updateBudget = useCallback((channel, value) => {
    const next = { ...budgets, [channel]: value }
    setBudgets(next)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => run(next), DEBOUNCE_MS)
  }, [budgets, run])

  const setAllBudgets = useCallback((newBudgets) => {
    setBudgets(newBudgets)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => run(newBudgets), DEBOUNCE_MS)
  }, [run])

  // Initial run
  useEffect(() => {
    run()
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [sessionId, horizonDays])

  const totalBudget = budgets.google + budgets.meta + budgets.microsoft

  return {
    budgets,
    updateBudget,
    setAllBudgets,
    result,
    loading,
    error,
    totalBudget,
    revenue: result?.revenue || { p10: 0, p50: 0, p90: 0 },
    roas: result?.roas || { p10: 0, p50: 0, p90: 0 },
    channelMix: result?.channel_mix || {},
    confidence: result?.confidence || 0,
    histogram: result?.histogram || { counts: [], bins: [] },
  }
}
