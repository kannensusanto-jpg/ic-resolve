import { useQuery } from '@tanstack/react-query'
import { api } from '../api'

export function useDataStatus() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['data-status'],
    queryFn: () => api.getDataStatus().then(r => r.data),
    refetchOnWindowFocus: true,
    staleTime: 0,        // always re-check — never serve a cached "has data" answer
    retry: 1,
  })

  // Only true when the API explicitly confirms data exists
  // Any other state (loading, error, no response) → false
  const hasData = !isLoading && !isError && (data?.has_data === true)

  return {
    hasData,
    latestPeriod: data?.latest_period ?? '2026-03',
    periods: data?.periods ?? [],
    isLoading,
  }
}
