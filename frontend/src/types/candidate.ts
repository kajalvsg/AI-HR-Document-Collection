export interface ApiResponse<T> {
  success: boolean
  message?: string
  data?: T
  error?: string
}

export interface CandidateListItem {
  id: number
  name: string | null
  email: string
  company: string | null
  designation: string | null
  extraction_status: string
  overall_confidence: number | null
  document_status: string
}

export interface DocumentRecord {
  id: number
  candidate_id: number
  document_type: string
  original_filename: string
  mime_type: string | null
  uploaded_at: string | null
}

export interface RequestLog {
  id: number
  candidate_id: number
  message: string | null
  status: string
  source: 'ai' | 'template' | 'fallback'
  created_at: string | null
}

export interface Candidate extends CandidateListItem {
  phone: string | null
  skills: string[]
  confidence_scores: Record<string, number>
  resume_filename: string | null
  resume_text_preview: string
  resume_text?: string
  documents?: DocumentRecord[]
  request_logs?: RequestLog[]
  created_at: string | null
  updated_at: string | null
}

export interface CandidatesListData {
  candidates: CandidateListItem[]
  count: number
}

export interface UploadCandidateData extends Candidate {}

export interface RequestDocumentsData {
  candidate_id: number
  message: string
  status: string
  source: 'ai' | 'template' | 'fallback'
  request_log: RequestLog
}

export interface SubmitDocumentsData {
  candidate_id: number
  document_status: string
  uploaded_documents: DocumentRecord[]
  documents: DocumentRecord[]
}
