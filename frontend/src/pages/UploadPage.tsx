import { useCallback, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileUp, Upload } from 'lucide-react'
import { uploadResume } from '../api/candidates'
import { getErrorMessage } from '../api/client'
import Alert from '../components/Alert'
import type { UploadCandidateData } from '../types/candidate'

const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]
const ALLOWED_EXT = ['.pdf', '.docx']

function isValidFile(file: File) {
  const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))
  return ALLOWED_EXT.includes(ext) || ALLOWED_TYPES.includes(file.type)
}

export default function UploadPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<UploadCandidateData | null>(null)

  const selectFile = useCallback((selected: File | null) => {
    setError(null)
    setResult(null)
    if (!selected) {
      setFile(null)
      return
    }
    if (!isValidFile(selected)) {
      setError('Only PDF and DOCX files are allowed.')
      setFile(null)
      return
    }
    setFile(selected)
  }, [])

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const dropped = e.dataTransfer.files?.[0]
      if (dropped) selectFile(dropped)
    },
    [selectFile],
  )

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a resume file first.')
      return
    }
    setLoading(true)
    setProgress(0)
    setError(null)
    setResult(null)
    try {
      const response = await uploadResume(file, setProgress)
      if (!response.success || !response.data) {
        throw new Error(response.message || 'Upload failed')
      }
      setResult(response.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Upload Resume</h1>
        <p className="mt-2 text-slate-600">
          Upload a candidate resume (PDF or DOCX). We will extract profile details automatically.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors ${
          dragOver
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={(e) => selectFile(e.target.files?.[0] ?? null)}
        />
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <FileUp className="h-7 w-7" />
        </div>
        <p className="mt-4 text-base font-medium text-slate-800">
          Drag and drop your resume here
        </p>
        <p className="mt-1 text-sm text-slate-500">or click to browse — PDF, DOCX only</p>
        {file && (
          <p className="mt-4 inline-flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700">
            <Upload className="h-4 w-4" />
            {file.name}
          </p>
        )}
      </div>

      {loading && (
        <div className="mt-6">
          <div className="mb-2 flex justify-between text-sm text-slate-600">
            <span>Uploading and processing…</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full rounded-full bg-indigo-600 transition-all duration-300"
              style={{ width: `${Math.max(progress, 8)}%` }}
            />
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={handleUpload}
        disabled={!file || loading}
        className="mt-6 w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:min-w-[200px]"
      >
        {loading ? 'Processing…' : 'Upload Resume'}
      </button>

      {error && (
        <div className="mt-6">
          <Alert variant="error" title="Upload failed" message={error} />
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <Alert
            variant="success"
            title="Resume processed successfully"
            message={`Candidate ${result.name || result.email} was created with status ${result.extraction_status}.`}
          />
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="font-semibold text-slate-900">Extracted summary</h3>
            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-500">Name</dt>
                <dd className="font-medium text-slate-900">{result.name || '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Email</dt>
                <dd className="font-medium text-slate-900">{result.email}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Company</dt>
                <dd className="font-medium text-slate-900">{result.company || '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Confidence</dt>
                <dd className="font-medium text-slate-900">
                  {result.overall_confidence != null
                    ? `${Math.round(result.overall_confidence * 100)}%`
                    : '—'}
                </dd>
              </div>
            </dl>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                to="/dashboard"
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
              >
                Go to Dashboard
              </Link>
              <Link
                to={`/candidates/${result.id}`}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                View Profile
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
