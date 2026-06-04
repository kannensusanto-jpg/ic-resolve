import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, ChevronDown, ChevronRight, Shield } from 'lucide-react'
import { api } from '../api'
import type { AuditEntry } from '../types'
import clsx from 'clsx'
import { useDataStatus } from '../hooks/useDataStatus'

const ACTION_COLORS: Record<string, string> = {
  normalisation:   'bg-blue-100 text-blue-700',
  match_decision:  'bg-green-100 text-green-700',
  dispute_created: 'bg-amber-100 text-amber-700',
  query:           'bg-purple-100 text-purple-700',
}

const ACTION_LABELS: Record<string, string> = {
  normalisation:   'Normalisation',
  match_decision:  'Match Decision',
  dispute_created: 'Dispute Created',
  query:           'NL Query',
}

function AuditRow({ entry }: { entry: AuditEntry }) {
  const [expanded, setExpanded] = useState(false)

  let detail: Record<string, unknown> | null = null
  try {
    if (entry.action_detail) detail = JSON.parse(entry.action_detail)
  } catch { /* ignore */ }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center gap-3 px-4 py-3 bg-white hover:bg-gray-50 text-left"
        onClick={() => setExpanded(v => !v)}
      >
        {expanded ? <ChevronDown size={14} className="shrink-0 text-gray-400" /> : <ChevronRight size={14} className="shrink-0 text-gray-400" />}
        <span className={clsx(
          'inline-flex px-2 py-0.5 rounded-full text-xs font-medium shrink-0',
          ACTION_COLORS[entry.action_type] ?? 'bg-gray-100 text-gray-600',
        )}>
          {ACTION_LABELS[entry.action_type] ?? entry.action_type}
        </span>
        <span className="text-sm text-gray-700 flex-1 truncate">
          {entry.entity_a_id && (
            <span className="font-medium">{entry.entity_a_id}</span>
          )}
          {entry.entity_b_id && (
            <span className="text-gray-400"> ↔ {entry.entity_b_id}</span>
          )}
          {entry.ai_reasoning && (
            <span className="ml-2 text-gray-500 font-normal">{entry.ai_reasoning.slice(0, 80)}…</span>
          )}
        </span>
        <span className="text-xs text-gray-400 shrink-0">
          {new Date(entry.created_at).toLocaleString()}
        </span>
        {entry.ai_model && (
          <span className="text-xs text-indigo-400 shrink-0 ml-2">
            🤖 {entry.ai_model}
          </span>
        )}
      </button>

      {expanded && (
        <div className="border-t border-gray-100 bg-gray-50 px-6 py-4 space-y-3 text-sm">
          {entry.ai_reasoning && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                AI Reasoning / Decision
              </div>
              <p className="text-gray-700 leading-relaxed">{entry.ai_reasoning}</p>
            </div>
          )}
          {detail && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Action Detail
              </div>
              <pre className="text-xs bg-white border border-gray-200 rounded-lg p-3 overflow-x-auto text-gray-600">
                {JSON.stringify(detail, null, 2)}
              </pre>
            </div>
          )}
          <div className="grid grid-cols-3 gap-4 text-xs text-gray-500">
            <div><span className="font-medium">Period:</span> {entry.period ?? '—'}</div>
            <div><span className="font-medium">Audit ID:</span> #{entry.id}</div>
            <div><span className="font-medium">Model:</span> {entry.ai_model ?? 'rule-based'}</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AuditTrail() {
  const { latestPeriod: period } = useDataStatus()
  const [actionFilter, setActionFilter] = useState('')

  const { data: entries, isLoading } = useQuery({
    queryKey: ['audit', period, actionFilter],
    queryFn: () => api.getAuditTrail(period, actionFilter || undefined).then(r => r.data),
    refetchInterval: 10_000,
  })

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Trail</h1>
          <p className="text-sm text-gray-500 mt-1">
            Complete log of every AI decision and agent action — {entries?.length ?? 0} entries
          </p>
        </div>
        <div className="flex items-center gap-2 bg-indigo-50 border border-indigo-200 rounded-lg px-3 py-2 text-xs text-indigo-700">
          <Shield size={13} />
          Every AI reasoning step is logged
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-1.5">
        {['', 'normalisation', 'match_decision', 'dispute_created', 'query'].map(a => (
          <button
            key={a}
            onClick={() => setActionFilter(a)}
            className={clsx(
              'px-3 py-1.5 text-xs rounded-full font-medium border transition-colors',
              actionFilter === a
                ? 'bg-brand-600 text-white border-brand-600'
                : 'border-gray-300 text-gray-600 hover:bg-gray-50',
            )}
          >
            {a === '' ? 'All' : ACTION_LABELS[a] ?? a}
          </button>
        ))}
      </div>

      {/* Entries */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="animate-spin text-brand-500 w-6 h-6" />
        </div>
      ) : (entries ?? []).length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          No audit entries yet — run reconciliation to generate activity
        </div>
      ) : (
        <div className="space-y-2">
          {(entries ?? []).map(e => (
            <AuditRow key={e.id} entry={e} />
          ))}
        </div>
      )}
    </div>
  )
}
