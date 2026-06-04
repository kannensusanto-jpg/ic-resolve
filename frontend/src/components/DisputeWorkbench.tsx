import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Loader2, ChevronDown, ChevronRight, AlertTriangle } from 'lucide-react'
import { api } from '../api'
import type { Dispute } from '../types'
import clsx from 'clsx'
import { useDataStatus } from '../hooks/useDataStatus'


const TYPE_COLORS: Record<string, string> = {
  timing:             'bg-amber-100 text-amber-700 border-amber-200',
  fx:                 'bg-orange-100 text-orange-700 border-orange-200',
  missing_posting:    'bg-purple-100 text-purple-700 border-purple-200',
  amount_difference:  'bg-red-100 text-red-700 border-red-200',
}

const TYPE_LABELS: Record<string, string> = {
  timing:             'Timing Difference',
  fx:                 'FX Difference',
  missing_posting:    'Missing Posting',
  amount_difference:  'Amount Difference',
}

const STATUS_COLORS: Record<string, string> = {
  open:       'bg-red-100 text-red-700',
  in_review:  'bg-amber-100 text-amber-700',
  resolved:   'bg-green-100 text-green-700',
  escalated:  'bg-purple-100 text-purple-700',
}

function fmt(n: number | null | undefined) {
  if (n == null) return '—'
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 }).format(n)
}

function slaClass(deadline: string | null, status: string) {
  if (!deadline || status === 'resolved') return 'text-gray-500'
  const d = new Date(deadline)
  const today = new Date()
  if (d < today) return 'text-red-600 font-semibold'
  const daysLeft = Math.ceil((d.getTime() - today.getTime()) / 86400000)
  if (daysLeft <= 2) return 'text-orange-500 font-semibold'
  return 'text-gray-600'
}

function DisputeRow({ dispute }: { dispute: Dispute }) {
  const qc = useQueryClient()
  const [expanded, setExpanded] = useState(false)
  const [notes, setNotes] = useState(dispute.resolution_notes ?? '')

  const updateMut = useMutation({
    mutationFn: (update: { status?: string; resolution_notes?: string }) =>
      api.updateDispute(dispute.id, update),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['disputes'] }),
  })

  const nextStatus: Record<string, string> = {
    open: 'in_review',
    in_review: 'resolved',
    resolved: 'open',
    escalated: 'open',
  }

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
          <div className="font-medium text-gray-800 text-sm">
            {dispute.entity_a?.name ?? dispute.entity_a_id}
          </div>
          <div className="text-xs text-gray-400">
            ↔ {dispute.entity_b?.name ?? dispute.entity_b_id}
          </div>
        </td>
        <td className="px-4 py-3">
          <span className={clsx(
            'inline-flex px-2 py-0.5 rounded-full text-xs font-medium border',
            TYPE_COLORS[dispute.dispute_type] ?? 'bg-gray-100 text-gray-600 border-gray-200',
          )}>
            {TYPE_LABELS[dispute.dispute_type] ?? dispute.dispute_type}
          </span>
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm font-semibold text-red-600">
          {fmt(dispute.amount_gbp)}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {dispute.owning_entity?.name ?? dispute.owning_entity_id}
        </td>
        <td className={clsx('px-4 py-3 text-sm', slaClass(dispute.sla_deadline, dispute.status))}>
          {dispute.sla_deadline ?? '—'}
          {dispute.sla_deadline && new Date(dispute.sla_deadline) < new Date() && dispute.status !== 'resolved' && (
            <span className="ml-1 text-xs">⚠ Breached</span>
          )}
        </td>
        <td className="px-4 py-3">
          <span className={clsx(
            'inline-flex px-2 py-0.5 rounded-full text-xs font-semibold',
            STATUS_COLORS[dispute.status] ?? 'bg-gray-100 text-gray-600',
          )}>
            {dispute.status}
          </span>
        </td>
        <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
          <button
            onClick={() => updateMut.mutate({ status: nextStatus[dispute.status] })}
            disabled={updateMut.isPending}
            className="px-2.5 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            {updateMut.isPending ? <Loader2 size={12} className="animate-spin" /> : '→ ' + nextStatus[dispute.status]}
          </button>
        </td>
      </tr>

      {expanded && (
        <tr className="bg-amber-50/30">
          <td colSpan={8} className="px-8 py-4">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <div className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
                  <AlertTriangle size={14} className="text-amber-500" />
                  AI-Drafted Dispute Description
                </div>
                <p className="text-sm text-gray-700 bg-white border border-gray-200 rounded-lg p-3 leading-relaxed">
                  {dispute.ai_description ?? 'No AI description available.'}
                </p>
                <div className="mt-2 text-xs text-gray-400">
                  Dispute ID: {dispute.id} · Created: {new Date(dispute.created_at).toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-sm font-semibold text-gray-700 mb-2">Resolution Notes</div>
                <textarea
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                  onClick={e => e.stopPropagation()}
                  rows={4}
                  placeholder="Add resolution notes..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none"
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    updateMut.mutate({ resolution_notes: notes })
                  }}
                  className="mt-2 px-3 py-1.5 text-xs bg-brand-600 text-white rounded-lg hover:bg-brand-700"
                >
                  Save Notes
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function DisputeWorkbench() {
  const qc = useQueryClient()
  const { hasData, latestPeriod: PERIOD } = useDataStatus()
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  const { data: disputes, isLoading } = useQuery({
    queryKey: ['disputes', PERIOD, statusFilter, typeFilter],
    queryFn: () => api.getDisputes(PERIOD, statusFilter || undefined, typeFilter || undefined).then(r => r.data),
    enabled: hasData,
  })

  const genMut = useMutation({
    mutationFn: (useAi: boolean) => api.generateDisputes(PERIOD, useAi),
    onSuccess: () => qc.invalidateQueries(),
  })

  const totalExposure = (disputes ?? []).filter(d => d.status !== 'resolved')
    .reduce((s, d) => s + (d.amount_gbp ?? 0), 0)

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dispute Workbench</h1>
          <p className="text-sm text-gray-500 mt-1">
            {!hasData ? 'No data — upload a trial balance first' : (
              <>
                Period {PERIOD} ·{' '}
                {(disputes ?? []).filter(d => d.status === 'open').length} open ·{' '}
                Total exposure: {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(totalExposure)}
              </>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => genMut.mutate(true)}
            disabled={genMut.isPending || !hasData}
            title={!hasData ? 'Upload a trial balance first' : undefined}
            className="px-3 py-2 text-sm bg-indigo-700 text-white rounded-lg hover:bg-indigo-800 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            {genMut.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Generate Disputes
          </button>
        </div>
      </div>

      {genMut.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">
          ✓ {genMut.data.data.disputes_created} disputes created, {genMut.data.data.disputes_updated} updated,{' '}
          {genMut.data.data.ai_descriptions_generated} AI descriptions generated.
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex gap-1.5">
          {['', 'open', 'in_review', 'resolved', 'escalated'].map(s => (
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
              {s === '' ? 'All Status' : s.replace('_', ' ')}
            </button>
          ))}
        </div>
        <div className="flex gap-1.5">
          {['', 'timing', 'fx', 'missing_posting', 'amount_difference'].map(t => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={clsx(
                'px-3 py-1.5 text-xs rounded-full font-medium border transition-colors',
                typeFilter === t
                  ? 'bg-amber-600 text-white border-amber-600'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50',
              )}
            >
              {t === '' ? 'All Types' : TYPE_LABELS[t] ?? t}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th className="px-4 py-3 w-6" />
              <th className="px-4 py-3 text-left">Entity Pair</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-right">Amount (GBP)</th>
              <th className="px-4 py-3 text-left">Owner</th>
              <th className="px-4 py-3 text-left">SLA Deadline</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="py-12 text-center">
                  <Loader2 className="inline animate-spin text-brand-500 w-6 h-6" />
                </td>
              </tr>
            ) : (disputes ?? []).length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-gray-400">
                  {hasData ? 'No disputes yet — run reconciliation first' : 'No data — upload a trial balance to get started'}
                </td>
              </tr>
            ) : (
              (disputes ?? []).map(d => <DisputeRow key={d.id} dispute={d} />)
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
