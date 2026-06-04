import { useState, useRef } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Upload, FileSpreadsheet, CheckCircle, Loader2, AlertCircle } from 'lucide-react'
import axios from 'axios'
import clsx from 'clsx'

interface Props {
  onClose: () => void
}

function FileDropZone({
  label, accept, file, onChange,
}: {
  label: string; accept: string; file: File | null
  onChange: (f: File | null) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)

  return (
    <div
      className={clsx(
        'border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors',
        file ? 'border-green-400 bg-green-50' : 'border-gray-300 hover:border-brand-400 hover:bg-brand-50',
      )}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={e => onChange(e.target.files?.[0] ?? null)}
      />
      {file ? (
        <div className="flex items-center justify-center gap-2 text-green-700">
          <CheckCircle size={18} />
          <span className="text-sm font-medium">{file.name}</span>
        </div>
      ) : (
        <div className="text-gray-400">
          <FileSpreadsheet size={28} className="mx-auto mb-2" />
          <div className="text-sm font-medium text-gray-600">{label}</div>
          <div className="text-xs mt-0.5">Click to browse or drag & drop (.xlsx)</div>
        </div>
      )}
    </div>
  )
}

export default function UploadModal({ onClose }: Props) {
  const qc = useQueryClient()
  const [tbFile, setTbFile] = useState<File | null>(null)
  const [txFile, setTxFile] = useState<File | null>(null)
  const [fxFile, setFxFile] = useState<File | null>(null)

  const uploadMut = useMutation({
    mutationFn: async () => {
      const form = new FormData()
      if (tbFile) form.append('trial_balance', tbFile)
      if (txFile) form.append('ic_transactions', txFile)
      if (fxFile) form.append('fx_rates', fxFile)
      const res = await axios.post('/api/data/upload/both', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return res.data
    },
    onSuccess: () => {
      qc.invalidateQueries()
      qc.invalidateQueries({ queryKey: ['data-status'] })
    },
  })

  const canUpload = !!tbFile

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Upload size={18} className="text-brand-600" />
            <h2 className="text-base font-semibold text-gray-900">Import Excel Data</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          <p className="text-sm text-gray-500">
            Upload both files together. The period is auto-detected from the file header.
            Existing data for that period will be replaced.
          </p>

          <FileDropZone
            label="Trial Balance IC Upload"
            accept=".xlsx,.xls"
            file={tbFile}
            onChange={setTbFile}
          />
          <FileDropZone
            label="IC Transaction Detail (optional)"
            accept=".xlsx,.xls"
            file={txFile}
            onChange={setTxFile}
          />
          {!txFile && (
            <p className="text-xs text-gray-400 -mt-2 px-1">
              If omitted, balances are derived directly from the trial balance.
              Upload for timing difference detection and richer AI dispute context.
            </p>
          )}
          <FileDropZone
            label="FX Rates Table (optional)"
            accept=".xlsx,.xls"
            file={fxFile}
            onChange={setFxFile}
          />
          {!fxFile && (
            <p className="text-xs text-gray-400 -mt-2 px-1">
              If omitted, FX is taken from the USD Amount column in the files above.
              Upload to enable local-currency normalisation and GBP conversion.
            </p>
          )}

          {/* Result */}
          {uploadMut.isSuccess && uploadMut.data && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm">
              <div className="font-semibold text-green-800 mb-2">
                ✓ Imported — Period {uploadMut.data.period}
              </div>
              <div className="text-green-700 space-y-0.5">
                <div>Trial Balance: {uploadMut.data.trial_balance.rows_imported} IC rows imported</div>
                <div>
                  {uploadMut.data.ic_transactions?.source === 'trial_balance'
                    ? `IC Entries: ${uploadMut.data.ic_transactions.rows_derived} entries derived from TB`
                    : `IC Transactions: ${uploadMut.data.ic_transactions?.rows_imported ?? 0} rows imported`}
                </div>
                {uploadMut.data.fx_rates && (
                  <div>
                    FX Rates: {uploadMut.data.fx_rates.rows_imported} rates imported
                    {uploadMut.data.fx_rates.warnings?.length > 0 && (
                      <span className="ml-1 text-amber-600">
                        ({uploadMut.data.fx_rates.warnings.length} warning{uploadMut.data.fx_rates.warnings.length > 1 ? 's' : ''})
                      </span>
                    )}
                  </div>
                )}
                {!uploadMut.data.fx_rates && (
                  <div className="text-green-500 text-xs">FX: using USD amounts from file (no FX table uploaded)</div>
                )}
              </div>
              <div className="mt-3 text-green-600 text-xs">
                Close the modal and click <strong>Run Matching</strong> on the Recon Workbench
                (set the period to <strong>{uploadMut.data.period}</strong> first).
              </div>
            </div>
          )}

          {uploadMut.isError && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 flex items-start gap-2 text-sm text-red-700">
              <AlertCircle size={15} className="shrink-0 mt-0.5" />
              Upload failed. Check the backend console for details.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => uploadMut.mutate()}
            disabled={!canUpload || uploadMut.isPending}
            className="px-4 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 flex items-center gap-2"
          >
            {uploadMut.isPending ? (
              <><Loader2 size={14} className="animate-spin" /> Importing…</>
            ) : (
              <><Upload size={14} /> Import Files</>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
