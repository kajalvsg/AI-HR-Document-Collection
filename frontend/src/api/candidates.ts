import type {
  ApiResponse,
  Candidate,
  CandidatesListData,
  RequestDocumentsData,
  SubmitDocumentsData,
  UploadCandidateData,
} from '../types/candidate'
import { apiClient } from './client'

export async function uploadResume(
  file: File,
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData()
  formData.append('resume', file)

  const { data } = await apiClient.post<ApiResponse<UploadCandidateData>>(
    '/candidates/upload',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (!event.total || !onProgress) return
        onProgress(Math.round((event.loaded * 100) / event.total))
      },
    },
  )
  return data
}

export async function fetchCandidates() {
  const { data } = await apiClient.get<ApiResponse<CandidatesListData>>('/candidates')
  return data
}

export async function fetchCandidate(id: number) {
  const { data } = await apiClient.get<ApiResponse<Candidate>>(`/candidates/${id}`)
  return data
}

export async function requestDocuments(id: number) {
  const { data } = await apiClient.post<ApiResponse<RequestDocumentsData>>(
    `/candidates/${id}/request-documents`,
  )
  return data
}

export async function deleteCandidate(id: number) {
  const { data } = await apiClient.delete<ApiResponse<{ id: number; email: string; deleted: boolean }>>(
    `/candidates/${id}`,
  )
  return data
}

export async function submitDocuments(id: number, pan?: File, aadhaar?: File) {
  const formData = new FormData()
  if (pan) formData.append('pan', pan)
  if (aadhaar) formData.append('aadhaar', aadhaar)

  const { data } = await apiClient.post<ApiResponse<SubmitDocumentsData>>(
    `/candidates/${id}/submit-documents`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}
