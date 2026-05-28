import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  FileCheck,
  Mail,
  RefreshCw,
  Send,
  Upload,
} from 'lucide-react'
import {
  fetchCandidate,
  requestDocuments,
  submitDocuments,
} from '../api/candidates'
import { getErrorMessage } from '../api/client'
import Alert from '../components/Alert'
import LoadingSpinner from '../components/LoadingSpinner'
import RequestLogCard from '../components/RequestLogCard'
import StatusBadge from '../components/StatusBadge'
import type { Candidate } from '../types/candidate'
import { cleanResumePreviewText } from '../utils/resumePreview'

const DOC_EXT = ['.pdf', '.png', '.jpg', '.jpeg', '.webp']

function isDocFile(file: File) {
  const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))
  return DOC_EXT.includes(ext)
}

const CONFIDENCE_FIELDS = [
  'name',
  'email',
  'phone',
  'company',
  'designation',
  'skills',
] as const

export default function ProfilePage() {
  const { id } = useParams<{ id: string }>()
  const candidateId = Number(id)

  const [candidate, setCandidate] = useState<Candidate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [requestLoading, setRequestLoading] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)
  const [requestSuccess, setRequestSuccess] = useState<string | null>(null)

  const [panFile, setPanFile] = useState<File | null>(null)
  const [aadhaarFile, setAadhaarFile] = useState<File | null>(null)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null)

  const loadCandidate = useCallback(async () => {
    if (!candidateId || Number.isNaN(candidateId)) {
      setError('Invalid candidate ID')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await fetchCandidate(candidateId)
      if (!response.success || !response.data) {
        throw new Error(response.message || 'Candidate not found')
      }
      setCandidate(response.data)
    } catch (err) {
      setCandidate(null)
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [candidateId])

  useEffect(() => {
    loadCandidate()
  }, [loadCandidate])

  const documents = candidate?.documents ?? []
  const hasPan = documents.some((d) => d.document_type === 'pan')
  const hasAadhaar = documents.some((d) => d.document_type === 'aadhaar')
  const documentsComplete = candidate?.document_status === 'complete'

  const hasDeliverableEmail = Boolean(
    candidate?.email && !candidate.email.toLowerCase().includes('@extract.pending'),
  )

  const hasAiRequest = useMemo(
    () =>
      (candidate?.request_logs ?? []).some(
        (log) => log.status === 'success' && log.source === 'ai' && log.message,
      ),
    [candidate?.request_logs],
  )

  const handleRequestDocuments = async () => {
    if (!candidate) return
    setRequestLoading(true)
    setRequestError(null)
    setRequestSuccess(null)
    try {
      const response = await requestDocuments(candidate.id)
      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to generate request')
      }
      setRequestSuccess(
        response.message ||
          'Document request generated and email simulated successfully',
      )
      await loadCandidate()
    } catch (err) {
      setRequestError(getErrorMessage(err))
    } finally {
      setRequestLoading(false)
    }
  }

  const handleSubmitDocuments = async () => {
    if (!candidate) return
    if (!panFile && !aadhaarFile) {
      setSubmitError('Select at least one document to upload.')
      return
    }
    if (panFile && hasPan) {
      setSubmitError('PAN document is already uploaded.')
      return
    }
    if (aadhaarFile && hasAadhaar) {
      setSubmitError('Aadhaar document is already uploaded.')
      return
    }
    if (panFile && !isDocFile(panFile)) {
      setSubmitError('Invalid PAN file type. Use PDF or image formats.')
      return
    }
    if (aadhaarFile && !isDocFile(aadhaarFile)) {
      setSubmitError('Invalid Aadhaar file type. Use PDF or image formats.')
      return
    }

    setSubmitLoading(true)
    setSubmitError(null)
    setSubmitSuccess(null)
    try {
      const response = await submitDocuments(
        candidate.id,
        panFile && !hasPan ? panFile : undefined,
        aadhaarFile && !hasAadhaar ? aadhaarFile : undefined,
      )
      if (!response.success) {
        throw new Error(response.message || 'Upload failed')
      }
      setSubmitSuccess(response.message || 'Documents uploaded successfully')
      setPanFile(null)
      setAadhaarFile(null)
      await loadCandidate()
    } catch (err) {
      setSubmitError(getErrorMessage(err))
    } finally {
      setSubmitLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner label="Loading candidate profile…" />
  }

  if (error || !candidate) {
    return (
      <div className="mx-auto max-w-lg">
        <Alert
          variant="error"
          title="Profile unavailable"
          message={error || 'Candidate not found'}
        />
        <Link
          to="/dashboard"
          className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-800"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>
    )
  }

  const resumePreviewRaw = candidate.resume_text || candidate.resume_text_preview
  const resumePreview = cleanResumePreviewText(resumePreviewRaw, candidate.email)

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link
            to="/dashboard"
            className="mb-3 inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
            {candidate.name || 'Unnamed Candidate'}
          </h1>
          <p className="mt-1 text-slate-600">{candidate.email}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <StatusBadge label={candidate.extraction_status} variant="extraction" />
            <StatusBadge label={candidate.document_status} variant="document" />
          </div>
        </div>
        <button
          type="button"
          onClick={loadCandidate}
          className="inline-flex items-center gap-2 self-start rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Extracted details</h2>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            {[
              ['Name', candidate.name],
              ['Email', candidate.email],
              ['Phone', candidate.phone],
              ['Company', candidate.company],
              ['Designation', candidate.designation],
              [
                'Overall confidence',
                candidate.overall_confidence != null
                  ? `${Math.round(candidate.overall_confidence * 100)}%`
                  : '—',
              ],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  {label}
                </dt>
                <dd className="mt-1 text-sm font-medium text-slate-900">{value || '—'}</dd>
              </div>
            ))}
          </dl>
          {candidate.skills?.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Skills
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {candidate.skills.map((skill) => (
                  <span
                    key={skill}
                    className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-800"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Field confidence scores</h2>
          <ul className="mt-4 space-y-3">
            {CONFIDENCE_FIELDS.map((field) => {
              const score = candidate.confidence_scores?.[field] ?? 0
              const pct = Math.round(score * 100)
              return (
                <li key={field}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="capitalize text-slate-700">{field}</span>
                    <span className="font-medium text-slate-900">{pct}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-indigo-500 transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Resume text preview</h2>
        <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-xs leading-relaxed text-slate-700">
          {resumePreview || 'No resume text available.'}
        </pre>
        {candidate.resume_filename && (
          <p className="mt-2 text-xs text-slate-500">File: {candidate.resume_filename}</p>
        )}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Document request</h2>
            <p className="mt-1 text-sm text-slate-500">
              Generate a personalized PAN/Aadhaar message and simulate sending it via
              email to the candidate (no real email is sent yet).
            </p>
          </div>
          <button
            type="button"
            onClick={handleRequestDocuments}
            disabled={
              requestLoading ||
              hasAiRequest ||
              documentsComplete ||
              !hasDeliverableEmail
            }
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
            {requestLoading
              ? 'Sending…'
              : hasAiRequest
                ? 'Request already sent'
                : 'Generate & Send Request'}
          </button>
        </div>
        {!hasDeliverableEmail && (
          <p className="mt-3 text-sm text-amber-700">
            A valid candidate email is required before a document request can be sent.
          </p>
        )}
        {hasAiRequest && (
          <p className="mt-3 text-sm text-slate-500">
            A document request has already been generated. See request logs below.
          </p>
        )}
        {requestError && (
          <div className="mt-4">
            <Alert variant="error" message={requestError} />
          </div>
        )}
        {requestSuccess && (
          <div className="mt-4">
            <Alert variant="success" message={requestSuccess} />
          </div>
        )}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Upload PAN & Aadhaar</h2>
        <p className="mt-1 text-sm text-slate-500">
          Accepted formats: PDF, PNG, JPG, WEBP. Each document can only be uploaded once.
        </p>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">
              PAN {hasPan && '(uploaded)'}
            </label>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp"
              disabled={hasPan || documentsComplete}
              onChange={(e) => setPanFile(e.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-indigo-700 disabled:opacity-50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Aadhaar {hasAadhaar && '(uploaded)'}
            </label>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp"
              disabled={hasAadhaar || documentsComplete}
              onChange={(e) => setAadhaarFile(e.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-indigo-700 disabled:opacity-50"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={handleSubmitDocuments}
          disabled={
            submitLoading ||
            documentsComplete ||
            ((!panFile || hasPan) && (!aadhaarFile || hasAadhaar))
          }
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Upload className="h-4 w-4" />
          {submitLoading ? 'Uploading…' : 'Submit Documents'}
        </button>

        {documentsComplete && (
          <p className="mt-3 flex items-center gap-2 text-sm text-emerald-700">
            <FileCheck className="h-4 w-4" />
            All required documents have been uploaded.
          </p>
        )}

        {submitError && (
          <div className="mt-4">
            <Alert variant="error" message={submitError} />
          </div>
        )}
        {submitSuccess && (
          <div className="mt-4">
            <Alert variant="success" message={submitSuccess} />
          </div>
        )}

        <div className="mt-6">
          <h3 className="text-sm font-semibold text-slate-800">Uploaded documents</h3>
          {documents.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">No documents uploaded yet.</p>
          ) : (
            <ul className="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-200">
              {documents.map((doc) => (
                <li
                  key={doc.id}
                  className="flex items-center justify-between px-4 py-3 text-sm"
                >
                  <span className="font-medium capitalize text-slate-800">
                    {doc.document_type}
                  </span>
                  <span className="text-slate-500">{doc.original_filename}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <Mail className="h-5 w-5 text-slate-500" />
          Request logs
        </h2>
        {(candidate.request_logs ?? []).length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No request logs yet.</p>
        ) : (
          <ul className="mt-4 space-y-4">
            {(candidate.request_logs ?? []).map((log) => (
              <li key={log.id}>
                <RequestLogCard
                  log={{
                    ...log,
                    source:
                      log.source === 'ai'
                        ? 'ai'
                        : log.source === 'template'
                          ? 'template'
                          : 'template',
                  }}
                />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
