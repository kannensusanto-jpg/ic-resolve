import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Loader2, ChevronDown, ChevronRight, Settings } from 'lucide-react'
import { api } from '../api'
import type { ReconciliationMatch } from '../types'
import clsx from 'clsx'
import { useDataStatus } from '../hooks/useDataStatus'


const MATCH_COLORS: Record<string, string> = {
  exact:              'bg-green-100 text-green-700',
  within_tolerance:   'bg-emerald-100 text-emerald-700',
  timing_difference:  'bg-amber-100 text-amber-700',
  fx_difference:      'bg-orange-100 text-orange-700',
  missing_posting:    'bg-purple-100 text-purple-700',
  amount_difference:  'bg-red-100 text-red-700',
  no_data:            'bg-gray-100 text-gray-600',
}

const MATCH_LABELS: Record<string, string> = {
  exact:              'Exact Match',
  within_tolerance:   'Within Tolerance',
  timing_difference:  'Timing Difference',
  fx_difference:      'FX Difference',
  missing_posting:    'Missing Posting',
  amount_difference:  'Amount Difference',
}

function fmt(n: number | null | undefined) {
  if (n == null) return '—'
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 }).format(n)
}

function MatchRow({ match }: { match: ReconciliationMatch }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr
        className="hover:bg-gray-50 cursor-pointer"
        onClick={() => setExpanded(v => !v)}
      >
        <td className="px-4 py-3 text-gray-400 w-6">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </td>
        <td className="px-4 py-3">
          <div className="font-medium text-gray-800">{match.entity_a?.name ?? match.entity_a_id}</div>
          <div className="text-xs text-gray-400">{match.entity_a?.functional_currency}</div>
        </td>
        <td className="px-4 py-3">
          <div className="text-gray-600">{match.entity_b?.name ?? match.entity_b_id}</div>
          <div className="text-xs text-gray-400">{match.entity_b?.functional_currency}</div>
        </td>
        <td className="px-4 py-3 text-right font-mono text-xs text-gray-700">{fmt(match.amount_a_gbp)}</td>
        <td className="px-4 py-3 text-right font-mono text-xs text-gray-700">
          {fmt(match.amount_b_gbp != null ? Math.abs(match.amount_b_gbp) : null)}
        </td>
        <td className={clsx(
          'px-4 py-3 text-right font-mono text-xs font-semibold',
          match.status === 'matched' ? 'text-green-600' : 'text-red-600',
        )}>
          {fmt(match.difference_gbp)}
        </td>
        <td className="px-4 py-3">
          <span className={clsx(
            'inline-flex px-2 py-0.5 rounded-full text-xs font-medium',
            MATCH_COLORS[match.match_type ?? ''] ?? 'bg-gray-100 text-gray-600',
          )}>
            {MATCH_LABELS[match.match_type ?? ''] ?? match.match_type ?? '—'}
          </span>
          {match.has_timing_difference && (
            <span className="ml-1 inline-flex px-1.5 py-0.5 rounded text-xs bg-yellow-100 text-yellow-700">
              ⏱ timing
            </span>
          )}
        </td>
        <td className="px-4 py-3">
          <span className={clsx(
            'inline-flex px-2 py-0.5 rounded-full text-xs font-semibold',
            match.status === 'matched'
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-600',
          )}>
            {match.status}
          </span>
        </td>
      </tr>

      {expanded && (
        <tr className="bg-indigo-50/40">
          <td colSpan={8} className="px-8 py-4">
            <div className="grid grid-cols-2 gap-6 text-sm">
              <div>
                <div className="font-semibold text-gray-700 mb-2">AI Reasoning</div>
                <p className="text-gray-600 leading-relaxed">
                  {match.ai_reasoning ?? 'No reasoning available — run matching first.'}
                </p>
              </div>
              <div className="space-y-2">
                <div className="font-semibold text-gray-700 mb-2">Match Detail</div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                  <span className="text-gray-500">Tolerance (GBP):</span>
                  <span className="font-mono">{fmt(match.tolerance_threshold_gbp)}</span>
                  <span className="text-gray-500">Tolerance (%):</span>
                  <span className="font-mono">{((match.tolerance_pct ?? 0) * 100).toFixed(2)}%</span>
                  <span className="text-gray-500">Period:</span>
                  <span>{match.period}</span>
                  <span className="text-gray-500">Match ID:</span>
                  <span className="font-mono text-gray-400">{match.id}</span>
                </div>
                {match.dispute && (
                  <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-100">
                    <div className="text-xs font-semibold text-red-700 mb-1">Open Dispute</div>
                    <div className="text-xs text-red-600">{match.dispute.ai_description}</div>
                    <div className="text-xs text-red-400 mt-1">
                      SLA: {match.dispute.sla_deadline} · Owner: {match.dispute.owning_entity?.name}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function ReconciliationWorkbench() {
  const qc = useQueryClient()
  const { hasData, latestPeriod: PERIOD } = useDataStatus()
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showTolerance, setShowTolerance] = useState(false)
  const [toleranceAbsolute, setToleranceAbsolute] = useState(1000)
  const [tolerancePct, setTolerancePct] = useState(0.1)

  const { data: pairs, isLoading } = useQuery({
    queryKey: ['pairs', PERIOD, statusFilter],
    queryFn: () => api.getPairs(PERIOD, statusFilter || undefined).then(r => r.data),
    enabled: hasData,
  })

  const { data: configs } = useQuery({
    queryKey: ['tolerance-configs'],
    queryFn: () => api.getToleranceConfigs().then(r => r.data),
  })

  const normMut = useMutation({
    mutationFn: () => api.normalise(PERIOD),
    onSuccess: () => { qc.invalidateQueries(); },
  })

  const matchMut = useMutation({
    mutationFn: () => api.match(PERIOD),
    onSuccess: () => qc.invalidateQueries(),
  })

  const runAllMut = useMutation({
    mutationFn: () => api.runAll(PERIOD, false),
    onSuccess: () => qc.invalidateQueries(),
  })

  const toleranceMut = useMutation({
    mutationFn: () => api.upsertTolerance({
      entity_a_id: 'DEFAULT',
      entity_b_id: 'DEFAULT',
      absolute_threshold_gbp: toleranceAbsolute,
      percentage_threshold: tolerancePct / 100,
    }),
    onSuccess: () => { qc.invalidateQueries(); setShowTolerance(false) },
  })

  const matched = pairs?.filter(p => p.status === 'matched').length ?? 0
  const total = pairs?.length ?? 0

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reconciliation Workbench</h1>
          <p className="text-sm text-gray-500 mt-1">
            {hasData ? `Period ${PERIOD} · ${matched}/${total} pairs matched` : 'No data — upload a trial balance first'}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          <button
            onClick={() => setShowTolerance(v => !v)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-1.5"
          >
            <Settings size={14} /> Tolerance
          </button>
          <button
            onClick={() => normMut.mutate()}
            disabled={normMut.isPending || !hasData}
            title={!hasData ? 'Upload a trial balance first' : undefined}
            className="px-3 py-2 text-sm border border-brand-300 text-brand-700 rounded-lg hover:bg-brand-50 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            {normMut.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Normalise
          </button>
          <button
            onClick={() => matchMut.mutate()}
            disabled={matchMut.isPending || !hasData}
            title={!hasData ? 'Upload a trial balance first' : undefined}
            className="px-3 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            {matchMut.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Run Matching
          </button>
          <button
            onClick={() => runAllMut.mutate()}
            disabled={runAllMut.isPending || !hasData}
            title={!hasData ? 'Upload a trial balance first' : undefined}
            className="px-3 py-2 text-sm bg-indigo-700 text-white rounded-lg hover:bg-indigo-800 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            {runAllMut.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Run All Steps
          </button>
        </div>
      </div>

      {/* Tolerance panel */}
      {showTolerance && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-indigo-800 mb-3">
            Default Tolerance Configuration
          </h3>
          <div className="flex items-end gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Absolute Threshold (£)</label>
              <input
                type="number"
                value={toleranceAbsolute}
                onChange={e => setToleranceAbsolute(Number(e.target.value))}
                className="w-32 border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Percentage Threshold (%)</label>
              <input
                type="number"
                step="0.01"
                value={tolerancePct}
                onChange={e => setTolerancePct(Number(e.target.value))}
                className="w-24 border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              />
            </div>
            <button
              onClick={() => toleranceMut.mutate()}
              className="px-4 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Save
            </button>
          </div>
          <p className="text-xs text-indigo-600 mt-2">
            Pairs auto-match if difference ≤ £{toleranceAbsolute.toLocaleString()} OR ≤ {tolerancePct}%
          </p>
          {configs && (
            <div className="mt-3 text-xs text-gray-500">
              <strong>Pair-specific overrides:</strong>{' '}
              {configs.filter(c => c.entity_a_id !== 'DEFAULT').map(c =>
                `${c.entity_a_id}↔${c.entity_b_id}: £${c.absolute_threshold_gbp.toLocaleString()} / ${(c.percentage_threshold * 100).toFixed(2)}%`
              ).join(', ') || 'None'}
            </div>
          )}
        </div>
      )}

      {/* Normalisation result */}
      {normMut.isSuccess && normMut.data && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">
          ✓ Normalisation complete: {normMut.data.data.aliases_resolved} aliases resolved,{' '}
          {normMut.data.data.fx_applied} FX conversions, {normMut.data.data.entries_processed} entries processed.
          {normMut.data.data.warnings.length > 0 && (
            <div className="mt-1 text-amber-600">
              ⚠ {normMut.data.data.warnings.length} warning(s): {normMut.data.data.warnings[0]}
              {normMut.data.data.warnings.length > 1 ? ` (+${normMut.data.data.warnings.length - 1} more)` : ''}
            </div>
          )}
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2">
        {['', 'matched', 'unmatched'].map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={clsx(
              'px-3 py-1.5 text-xs rounded-full font-medium border transition-colors',
              statusFilter === s
                ? 'bg-brand-600 text-white border-brand-600'
                : 'border-gray-300 text-gray-600 hover:bg-gray-50',
            )}
          >
            {s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th className="px-4 py-3 w-6" />
              <th className="px-4 py-3 text-left">Entity A</th>
              <th className="px-4 py-3 text-left">Entity B</th>
              <th className="px-4 py-3 text-right">A Balance (GBP)</th>
              <th className="px-4 py-3 text-right">B Balance (GBP)</th>
              <th className="px-4 py-3 text-right">Difference</th>
              <th className="px-4 py-3 text-left">Match Type</th>
              <th className="px-4 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="py-12 text-center">
                  <Loader2 className="inline animate-spin text-brand-500 w-6 h-6" />
                </td>
              </tr>
            ) : (pairs ?? []).length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-gray-400">
                  No reconciliation pairs yet — upload your trial balance then click Run All Steps
                </td>
              </tr>
            ) : (
              (pairs ?? []).map(p => <MatchRow key={p.id} match={p} />)
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
