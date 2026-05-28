import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Trash2 } from 'lucide-react'
import { deleteCandidate, fetchCandidates } from '../api/candidates'
import { getErrorMessage } from '../api/client'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import StatusBadge from '../components/StatusBadge'
import type { CandidateListItem } from '../types/candidate'

const STATUS_FILTERS = ['All', 'Parsed', 'Partial', 'Failed', 'Pending']

export default function DashboardPage() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const loadCandidates = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchCandidates()
      if (!response.success) {
        throw new Error(response.message || 'Failed to load candidates')
      }
      setCandidates(response.data?.candidates ?? [])
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCandidates()
  }, [loadCandidates])

  const handleDelete = async (candidate: CandidateListItem) => {
    const label = candidate.name || candidate.email
    const confirmed = window.confirm(
      `Delete candidate "${label}"?\n\nThis will permanently remove their resume, documents, and request logs.`,
    )
    if (!confirmed) return

    setDeletingId(candidate.id)
    setActionMessage(null)
    setActionError(null)
    try {
      const response = await deleteCandidate(candidate.id)
      if (!response.success) {
        throw new Error(response.message || 'Failed to delete candidate')
      }
      setCandidates((prev) => prev.filter((c) => c.id !== candidate.id))
      setActionMessage(response.message || `Deleted ${label} successfully.`)
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setDeletingId(null)
    }
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return candidates.filter((c) => {
      const matchesSearch =
        !q ||
        (c.name?.toLowerCase().includes(q) ?? false) ||
        c.email.toLowerCase().includes(q) ||
        (c.company?.toLowerCase().includes(q) ?? false)

      const matchesStatus =
        statusFilter === 'All' ||
        c.extraction_status.toLowerCase() === statusFilter.toLowerCase()

      return matchesSearch && matchesStatus
    })
  }, [candidates, search, statusFilter])

  if (loading) {
    return <LoadingSpinner label="Loading candidates…" />
  }

  return (
    <div>
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Candidate Dashboard</h1>
          <p className="mt-2 text-slate-600">
            Review extracted profiles and manage document collection.
          </p>
        </div>
        <Link
          to="/"
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Upload Resume
        </Link>
      </div>

      {actionMessage && (
        <div className="mb-6">
          <Alert variant="success" message={actionMessage} />
        </div>
      )}
      {actionError && (
        <div className="mb-6">
          <Alert variant="error" title="Delete failed" message={actionError} />
        </div>
      )}
      {error && (
        <div className="mb-6">
          <Alert variant="error" title="Could not load candidates" message={error} />
        </div>
      )}

      <div className="mb-6 flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Search by name, email, or company…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-10 pr-4 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 sm:w-48"
        >
          {STATUS_FILTERS.map((s) => (
            <option key={s} value={s}>
              {s === 'All' ? 'All statuses' : s}
            </option>
          ))}
        </select>
      </div>

      {!error && candidates.length === 0 ? (
        <EmptyState
          title="No candidates yet"
          description="Upload a resume to create your first candidate profile and start collecting documents."
          action={
            <Link
              to="/"
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
            >
              Upload Resume
            </Link>
          }
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 font-semibold text-slate-700">Name</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Email</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Company</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Designation</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Extraction</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Confidence</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Documents</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-slate-500">
                      No candidates match your search or filter.
                    </td>
                  </tr>
                ) : (
                  filtered.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/80">
                      <td className="px-4 py-3 font-medium text-slate-900">
                        {c.name || '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{c.email}</td>
                      <td className="px-4 py-3 text-slate-600">{c.company || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{c.designation || '—'}</td>
                      <td className="px-4 py-3">
                        <StatusBadge label={c.extraction_status} variant="extraction" />
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {c.overall_confidence != null
                          ? `${Math.round(c.overall_confidence * 100)}%`
                          : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge label={c.document_status} variant="document" />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap items-center gap-3">
                          <Link
                            to={`/candidates/${c.id}`}
                            className="font-semibold text-indigo-600 hover:text-indigo-800"
                          >
                            View Profile
                          </Link>
                          <button
                            type="button"
                            onClick={() => handleDelete(c)}
                            disabled={deletingId === c.id}
                            className="inline-flex items-center gap-1 font-semibold text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <Trash2 className="h-4 w-4" />
                            {deletingId === c.id ? 'Deleting…' : 'Delete'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="border-t border-slate-100 bg-slate-50 px-4 py-2 text-xs text-slate-500">
            Showing {filtered.length} of {candidates.length} candidates
          </div>
        </div>
      )}
    </div>
  )
}
