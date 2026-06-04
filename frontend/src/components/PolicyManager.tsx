import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, CheckCircle, XCircle, Trash2, Loader2, ShieldCheck } from 'lucide-react'
import axios from 'axios'
import clsx from 'clsx'

interface PolicyDoc {
  id: number
  label: string
  filename: string
  content_type: string | null
  char_count: number | null
  is_active: boolean
  uploaded_at: string
  preview: string | null
}

function fmt_size(chars: number | null) {
  if (!chars) return '—'
  if (chars < 1000) return `${chars} chars`
  return `${(chars / 1000).toFixed(1)}k chars`
}

export default function PolicyManager() {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [label, setLabel] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const { data: policies, isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: () => axios.get<PolicyDoc[]>('/api/policy').then(r => r.data),
  })

  const { data: active } = useQuery({
    queryKey: ['policy-active'],
    queryFn: () => axios.get<PolicyDoc | null>('/api/policy/active').then(r => r.data),
  })

  const uploadMut = useMutation({
    mutationFn: async () => {
      const form = new FormData()
      form.append('file', file!)
      form.append('label', label)
      return axios.post('/api/policy/upload', form).then(r => r.data)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['policies'] })
      qc.invalidateQueries({ queryKey: ['policy-active'] })
      setFile(null)
      setLabel('')
    },
  })

  const activateMut = useMutation({
    mutationFn: (id: number) => axios.patch(`/api/policy/${id}/activate`).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['policies'] })
      qc.invalidateQueries({ queryKey: ['policy-active'] })
    },
  })

  const deactivateMut = useMutation({
    mutationFn: (id: number) => axios.patch(`/api/policy/${id}/deactivate`).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['policies'] })
      qc.invalidateQueries({ queryKey: ['policy-active'] })
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => axios.delete(`/api/policy/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['policies'] })
      qc.invalidateQueries({ queryKey: ['policy-active'] })
    },
  })

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">IC Policy Documents</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload your intercompany reconciliation policy. The active policy is automatically
          injected into every AI call — dispute descriptions, close summaries, and query responses
          will all apply your policy rules.
        </p>
      </div>

      {/* Active policy banner */}
      {active ? (
        <div className="flex items-start gap-3 bg-green-50 border border-green-200 rounded-xl p-4">
          <ShieldCheck className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-semibold text-green-800">
              Active policy: {active.label}
            </div>
            <div className="text-xs text-green-600 mt-0.5">
              {active.filename} · {fmt_size(active.char_count)} · uploaded {new Date(active.uploaded_at).toLocaleDateString()}
            </div>
            <div className="text-xs text-green-600 mt-1">
              This policy is being injected into all AI calls for dispute drafting, close summaries, and queries.
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          <ShieldCheck className="w-4 h-4 shrink-0 text-amber-500" />
          No active policy — AI responses use general best practice only. Upload your policy to ground responses in your specific rules.
        </div>
      )}

      {/* Upload form */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Upload New Policy</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Policy label</label>
            <input
              type="text"
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="e.g. IC Recon Policy v3.2 — FY26"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">File (PDF, DOCX, TXT, MD)</label>
            <div
              className={clsx(
                'flex items-center gap-2 border rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors',
                file
                  ? 'border-green-400 bg-green-50 text-green-700'
                  : 'border-gray-300 hover:border-brand-400 text-gray-500',
              )}
              onClick={() => fileRef.current?.click()}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.docx,.doc,.txt,.md"
                className="hidden"
                onChange={e => setFile(e.target.files?.[0] ?? null)}
              />
              {file ? (
                <><CheckCircle size={14} /> {file.name}</>
              ) : (
                <><Upload size={14} /> Click to browse</>
              )}
            </div>
          </div>
        </div>

        {uploadMut.isError && (
          <div className="text-sm text-red-600 bg-red-50 rounded-lg p-2 border border-red-100">
            Upload failed — check the file format and try again.
          </div>
        )}
        {uploadMut.isSuccess && (
          <div className="text-sm text-green-700 bg-green-50 rounded-lg p-2 border border-green-100">
            ✓ Policy uploaded and activated.
          </div>
        )}

        <button
          onClick={() => uploadMut.mutate()}
          disabled={!file || !label.trim() || uploadMut.isPending}
          className="px-4 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
        >
          {uploadMut.isPending
            ? <><Loader2 size={14} className="animate-spin" /> Uploading…</>
            : <><Upload size={14} /> Upload & Activate</>}
        </button>
      </div>

      {/* Policy list */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-700">Uploaded Policies</h2>
        {isLoading && (
          <div className="py-8 flex justify-center">
            <Loader2 className="animate-spin text-brand-500 w-5 h-5" />
          </div>
        )}
        {!isLoading && (!policies || policies.length === 0) && (
          <div className="text-center py-10 text-gray-400 text-sm border border-dashed border-gray-200 rounded-xl">
            No policies uploaded yet
          </div>
        )}
        {(policies ?? []).map(p => (
          <div
            key={p.id}
            className={clsx(
              'bg-white rounded-xl border overflow-hidden transition-colors',
              p.is_active ? 'border-green-300' : 'border-gray-200',
            )}
          >
            <div className="flex items-center gap-3 px-4 py-3">
              <FileText size={16} className={p.is_active ? 'text-green-500' : 'text-gray-400'} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-800 truncate">{p.label}</span>
                  {p.is_active && (
                    <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium shrink-0">
                      active
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {p.filename} · {fmt_size(p.char_count)} · {new Date(p.uploaded_at).toLocaleDateString()}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}
                  className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded border border-gray-200 hover:bg-gray-50"
                >
                  {expandedId === p.id ? 'Hide' : 'Preview'}
                </button>
                {p.is_active ? (
                  <button
                    onClick={() => deactivateMut.mutate(p.id)}
                    disabled={deactivateMut.isPending}
                    className="text-xs text-amber-600 hover:text-amber-700 px-2 py-1 rounded border border-amber-200 hover:bg-amber-50 flex items-center gap-1"
                  >
                    <XCircle size={12} /> Deactivate
                  </button>
                ) : (
                  <button
                    onClick={() => activateMut.mutate(p.id)}
                    disabled={activateMut.isPending}
                    className="text-xs text-green-600 hover:text-green-700 px-2 py-1 rounded border border-green-200 hover:bg-green-50 flex items-center gap-1"
                  >
                    <CheckCircle size={12} /> Activate
                  </button>
                )}
                <button
                  onClick={() => deleteMut.mutate(p.id)}
                  disabled={deleteMut.isPending}
                  className="text-gray-400 hover:text-red-500 p-1"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            {expandedId === p.id && p.preview && (
              <div className="border-t border-gray-100 bg-gray-50 px-4 py-3">
                <div className="text-xs text-gray-500 mb-1 font-medium uppercase tracking-wide">
                  Document preview (first 600 chars)
                </div>
                <pre className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed font-sans">
                  {p.preview}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
