import uuid

from flask import current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models import Candidate, Document, RequestLog
from app.services.ai_service import AIService
from app.services.extraction_service import CandidateExtractionService
from app.services.resume_parser import ResumeParserService
from app.utils.errors import AppError
from app.utils.files import (
    document_upload_folder,
    remove_directory,
    remove_file,
    resume_upload_folder,
    save_upload_with_allowed,
)


class CandidateService:
    @staticmethod
    def upload_resume(file: FileStorage) -> Candidate:
        allowed = current_app.config["ALLOWED_RESUME_EXTENSIONS"]
        folder = resume_upload_folder()

        file_path, stored_name, extension, _mime = save_upload_with_allowed(
            file,
            folder,
            allowed,
            prefix="resume",
            field_name="resume",
        )

        try:
            resume_text = ResumeParserService.parse(file_path, extension)
        except AppError:
            raise
        except Exception as exc:
            raise AppError(
                f"Resume parsing failed: {exc}",
                422,
                "parsing_failure",
            ) from exc

        if not resume_text:
            raise AppError(
                "Resume appears empty or contains no extractable text",
                422,
                "empty_resume",
            )

        extraction = CandidateExtractionService.extract(resume_text)

        email = extraction.email
        if email:
            email = (
                CandidateExtractionService.normalize_email(email, resume_text) or email
            )
            extraction.email = email
        if not email:
            email = f"pending.{uuid.uuid4().hex[:10]}@extract.pending"
            extraction.extraction_status = (
                "Partial" if extraction.extraction_status != "Failed" else "Failed"
            )
            extraction.confidence_scores["email"] = 0.0
        elif not email.endswith("@extract.pending"):
            existing = Candidate.query.filter_by(email=email).first()
            if existing:
                raise AppError(
                    f"A candidate with email {email} already exists",
                    409,
                    "duplicate_email",
                )

        candidate = Candidate(
            name=extraction.name,
            email=email,
            phone=extraction.phone,
            company=extraction.company,
            designation=extraction.designation,
            extraction_status=extraction.extraction_status,
            overall_confidence=extraction.overall_confidence,
            resume_text=resume_text,
            resume_filename=file.filename,
            resume_file_path=file_path,
        )
        candidate.set_skills(extraction.skills)
        candidate.set_confidence_scores(extraction.confidence_scores)

        db.session.add(candidate)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise AppError(
                "A candidate with this email already exists",
                409,
                "duplicate_email",
            ) from None

        return candidate

    @staticmethod
    def list_candidates() -> list[dict]:
        candidates = Candidate.query.order_by(Candidate.created_at.desc()).all()
        return [c.to_list_item() for c in candidates]

    @staticmethod
    def get_candidate(candidate_id: int, detailed: bool = True) -> Candidate:
        candidate = db.session.get(Candidate, candidate_id)
        if not candidate:
            raise AppError("Candidate not found", 404, "candidate_not_found")
        return candidate

    @staticmethod
    def _has_deliverable_email(candidate: Candidate) -> bool:
        email = (candidate.email or "").strip().lower()
        if not email:
            return False
        return "@extract.pending" not in email

    @staticmethod
    def request_documents(candidate_id: int) -> dict:
        candidate = CandidateService.get_candidate(candidate_id)
        if not CandidateService._has_deliverable_email(candidate):
            raise AppError(
                "Candidate email is required to send a document request",
                400,
                "missing_email",
            )

        recipient = candidate.email.strip()
        message, status, message_source = (
            AIService.generate_document_request_message(candidate)
        )

        log = RequestLog(
            candidate_id=candidate.id,
            request_type="document_request",
            message=message,
            status=status,
            message_source=message_source,
            channel="email",
            recipient=recipient,
            delivery_status="sent_simulated",
            error_detail=None,
        )
        db.session.add(log)
        db.session.commit()

        return {
            "candidate_id": candidate.id,
            "message": message,
            "status": status,
            "source": message_source,
            "channel": log.channel,
            "recipient": log.recipient,
            "delivery_status": log.delivery_status,
            "request_log": log.to_public_dict(),
        }

    @staticmethod
    def submit_documents(
        candidate_id: int,
        pan_file: FileStorage | None,
        aadhaar_file: FileStorage | None,
    ) -> dict:
        if not pan_file and not aadhaar_file:
            raise AppError(
                "At least one document is required (pan or aadhaar)",
                400,
                "missing_file",
            )

        candidate = CandidateService.get_candidate(candidate_id)
        allowed = current_app.config["ALLOWED_DOCUMENT_EXTENSIONS"]
        folder = document_upload_folder()
        uploaded = []

        for doc_type, upload in (("pan", pan_file), ("aadhaar", aadhaar_file)):
            if not upload or not upload.filename:
                continue

            existing = Document.query.filter_by(
                candidate_id=candidate.id, document_type=doc_type
            ).first()
            if existing:
                raise AppError(
                    f"{doc_type.upper()} document already uploaded for this candidate",
                    409,
                    "duplicate_document",
                )

            file_path, stored_name, _ext, mime = save_upload_with_allowed(
                upload,
                folder / str(candidate.id),
                allowed,
                prefix=doc_type,
                field_name=doc_type,
            )

            document = Document(
                candidate_id=candidate.id,
                document_type=doc_type,
                file_path=file_path,
                original_filename=upload.filename,
                mime_type=mime,
            )
            db.session.add(document)
            uploaded.append(document)

        candidate.refresh_document_status()
        db.session.commit()

        return {
            "candidate_id": candidate.id,
            "document_status": candidate.document_status,
            "uploaded_documents": [d.to_dict() for d in uploaded],
            "documents": [d.to_dict() for d in candidate.documents.all()],
        }

    @staticmethod
    def delete_candidate(candidate_id: int) -> dict:
        candidate = CandidateService.get_candidate(candidate_id)

        resume_path = candidate.resume_file_path
        document_paths = [doc.file_path for doc in candidate.documents.all()]
        documents_dir = document_upload_folder() / str(candidate.id)
        candidate_email = candidate.email

        db.session.delete(candidate)
        db.session.commit()

        remove_file(resume_path)
        for path in document_paths:
            remove_file(path)
        remove_directory(documents_dir)

        return {
            "id": candidate_id,
            "email": candidate_email,
            "deleted": True,
        }
