import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { CheckCircle, XCircle, AlertTriangle, Clock, Building2, Play, Loader2, Upload, Trash2 } from 'lucide-react'
import { api } from '../api'
import type { ReconciliationSummary, ReconciliationMatch } from '../types'
import clsx from 'clsx'
import UploadModal from './UploadModal'
import { useState } from 'react'
import { useDataStatus } from '../hooks/useDataStatus'


const MATCH_COLORS: Record<string, string> = {
  exact:              '#10b981',
  within_tolerance:   '#34d399',
  timing_difference:  '#f59e0b',
  fx_difference:      '#f97316',
  missing_posting:    '#8b5cf6',
  amount_difference:  '#ef4444',
  no_data:            '#9ca3af',
}

const MATCH_LABELS: Record<string, string> = {
  exact:              'Exact',
  within_tolerance:   'Within Tolerance',
  timing_difference:  'Timing Diff',
  fx_difference:      'FX Difference',
  missing_posting:    'Missing Posting',
  amount_difference:  'Amount Difference',
}

function KpiCard({
  label, value, sub, icon: Icon, color,
}: {
  label: string; value: string | number; sub?: string
  icon: React.ElementType; color: string
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-start gap-4">
      <div className={clsx('p-2.5 rounded-lg', color)}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="text-2xl font-bold text-gray-900">{value}</div>
        <div className="text-sm text-gray-500 mt-0.5">{label}</div>
        {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

function fmt(n: number | null | undefined) {
  if (n == null) return '—'
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 }).format(n)
}

function StatusBadge({ type }: { type: string | null }) {
  const color = MATCH_COLORS[type ?? ''] ?? '#9ca3af'
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium text-white"
      style={{ backgroundColor: color }}
    >
      {MATCH_LABELS[type ?? ''] ?? type ?? 'Unknown'}
    </span>
  )
}

export default function Dashboard() {
  const qc = useQueryClient()
  const [showUpload, setShowUpload] = useState(false)
  const { hasData, latestPeriod } = useDataStatus()
  const period = latestPeriod

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['summary', period],
    queryFn: () => api.getSummary(period).then(r => r.data),
    enabled: hasData,
  })

  const { data: pairs } = useQuery({
    queryKey: ['pairs', period],
    queryFn: () => api.getPairs(period).then(r => r.data),
    enabled: hasData,
  })

  const runAiMut = useMutation({
    mutationFn: () => api.runAll(period, true),
    onSuccess: () => qc.invalidateQueries(),
  })

  const clearMut = useMutation({
    mutationFn: () => api.clearData(),
    onSuccess: () => qc.invalidateQueries(),
  })

  const pieData = summary
    ? Object.entries(summary.by_match_type).map(([k, v]) => ({
        name: MATCH_LABELS[k] ?? k,
        value: v,
        color: MATCH_COLORS[k] ?? '#9ca3af',
      }))
    : []

  const barData = (pairs ?? [])
    .filter(p => p.status === 'unmatched')
    .map(p => ({
      name: `${p.entity_a?.name?.replace('Nexora ', '') ?? p.entity_a_id} ↔ ${p.entity_b?.name?.replace('Nexora ', '') ?? p.entity_b_id}`,
      difference: Math.round(p.difference_gbp ?? 0),
      color: MATCH_COLORS[p.match_type ?? ''] ?? '#ef4444',
    }))
    .sort((a, b) => b.difference - a.difference)

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-brand-600 w-8 h-8" />
      </div>
    )
  }

  return (
    <>
    {showUpload && <UploadModal onClose={() => setShowUpload(false)} />}
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reconciliation Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            {hasData ? `Period: ${period}` : 'Upload your data to begin'}
          </p>
        </div>
        <div className="flex gap-2">
          {hasData && (
            <button
              onClick={() => {
                if (window.confirm('Clear all uploaded data, matches, and disputes? This cannot be undone.')) {
                  clearMut.mutate()
                }
              }}
              disabled={clearMut.isPending}
              className="px-4 py-2 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {clearMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 size={14} />}
              Clear Data
            </button>
          )}
          <button
            onClick={() => setShowUpload(true)}
            className="px-4 py-2 text-sm border border-brand-300 text-brand-700 rounded-lg hover:bg-brand-50 flex items-center gap-2"
          >
            <Upload size={14} /> Upload Excel
          </button>
          <button
            onClick={() => runAiMut.mutate()}
            disabled={runAiMut.isPending || !hasData}
            title={!hasData ? 'Upload a trial balance first' : undefined}
            className="px-4 py-2 text-sm bg-indigo-700 text-white rounded-lg hover:bg-indigo-800 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {runAiMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play size={14} />}
            Run with AI
          </button>
        </div>
      </div>

      {/* Status banner */}
      {runAiMut.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">
          ✓ Operation completed successfully.
        </div>
      )}

      {!summary ? (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
          <p className="text-amber-800 font-medium">No reconciliation data yet.</p>
          <p className="text-amber-600 text-sm mt-1">Click <strong>Upload Excel</strong> to import your trial balance, then <strong>Run with AI</strong>.</p>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <KpiCard label="IC Pairs" value={summary.total_pairs}
              icon={Building2} color="bg-blue-50 text-blue-600" />
            <KpiCard label="Matched" value={`${summary.matched_pct}%`}
              sub={`${summary.matched_pairs} of ${summary.total_pairs}`}
              icon={CheckCircle}
              color={summary.matched_pct >= 75 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'} />
            <KpiCard label="Open Disputes" value={summary.open_disputes}
              sub={`£${(summary.total_difference_gbp / 1000).toFixed(0)}k exposure`}
              icon={XCircle} color="bg-red-50 text-red-600" />
            <KpiCard label="SLA Breached" value={summary.sla_breached}
              icon={AlertTriangle}
              color={summary.sla_breached > 0 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'} />
            <KpiCard
              label="Entities Confirmed"
              value={`${summary.entities_confirmed}/${summary.entities_confirmed + summary.entities_pending}`}
              icon={Clock} color="bg-amber-50 text-amber-600" />
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pie chart */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Match Status Breakdown</h2>
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: number) => [`${v} pairs`, '']} />
                    <Legend
                      formatter={(value) => <span className="text-xs text-gray-600">{value}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-60 flex items-center justify-center text-gray-400 text-sm">
                  Run reconciliation to see results
                </div>
              )}
            </div>

            {/* Bar chart — unmatched differences */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Unmatched Exposure by Pair (GBP)</h2>
              {barData.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={barData} layout="vertical" margin={{ left: 8, right: 16 }}>
                    <XAxis type="number" tick={{ fontSize: 11 }}
                      tickFormatter={(v) => `£${(v / 1000).toFixed(0)}k`} />
                    <YAxis type="category" dataKey="name" width={120}
                      tick={{ fontSize: 10 }} />
                    <Tooltip formatter={(v: number) => [`£${v.toLocaleString()}`, 'Difference']} />
                    <Bar dataKey="difference" radius={[0, 4, 4, 0]}>
                      {barData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-60 flex items-center justify-center text-gray-400 text-sm">
                  No unmatched pairs
                </div>
              )}
            </div>
          </div>

          {/* Pairs table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-700">All IC Pairs — {period}</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                  <tr>
                    <th className="px-4 py-3 text-left">Entity A</th>
                    <th className="px-4 py-3 text-left">Entity B</th>
                    <th className="px-4 py-3 text-right">A Balance</th>
                    <th className="px-4 py-3 text-right">B Balance</th>
                    <th className="px-4 py-3 text-right">Difference</th>
                    <th className="px-4 py-3 text-left">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {(pairs ?? []).map(p => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-800">
                        {p.entity_a?.name ?? p.entity_a_id}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {p.entity_b?.name ?? p.entity_b_id}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700 font-mono text-xs">
                        {fmt(p.amount_a_gbp)}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700 font-mono text-xs">
                        {fmt(p.amount_b_gbp != null ? Math.abs(p.amount_b_gbp) : null)}
                      </td>
                      <td className={clsx('px-4 py-3 text-right font-mono text-xs font-semibold',
                        p.status === 'matched' ? 'text-green-600' : 'text-red-600')}>
                        {fmt(p.difference_gbp)}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge type={p.match_type} />
                      </td>
                    </tr>
                  ))}
                  {(pairs ?? []).length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                        No data yet — upload your trial balance and run reconciliation
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
    </>

  )
}
