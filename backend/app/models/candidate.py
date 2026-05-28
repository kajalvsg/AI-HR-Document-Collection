import json
from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    designation = db.Column(db.String(255), nullable=True)
    skills = db.Column(db.Text, nullable=True)  # JSON array

    extraction_status = db.Column(
        db.String(32), nullable=False, default="Failed"
    )  # Parsed | Partial | Failed
    confidence_scores = db.Column(db.Text, nullable=True)  # JSON object field -> score
    overall_confidence = db.Column(db.Float, nullable=True)

    document_status = db.Column(
        db.String(32), nullable=False, default="none"
    )  # none | partial | complete

    resume_text = db.Column(db.Text, nullable=True)
    resume_filename = db.Column(db.String(512), nullable=True)
    resume_file_path = db.Column(db.String(1024), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    documents = db.relationship(
        "Document",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    request_logs = db.relationship(
        "RequestLog",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="RequestLog.created_at.desc()",
    )

    def set_skills(self, skills_list: list | None) -> None:
        self.skills = json.dumps(skills_list or [])

    def get_skills(self) -> list:
        if not self.skills:
            return []
        try:
            return json.loads(self.skills)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_confidence_scores(self, scores: dict | None) -> None:
        self.confidence_scores = json.dumps(scores or {})

    def get_confidence_scores(self) -> dict:
        if not self.confidence_scores:
            return {}
        try:
            return json.loads(self.confidence_scores)
        except (json.JSONDecodeError, TypeError):
            return {}

    def refresh_document_status(self) -> None:
        types = {doc.document_type for doc in self.documents.all()}
        if "pan" in types and "aadhaar" in types:
            self.document_status = "complete"
        elif types:
            self.document_status = "partial"
        else:
            self.document_status = "none"

    def to_dict(self, include_relations: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "designation": self.designation,
            "skills": self.get_skills(),
            "extraction_status": self.extraction_status,
            "confidence_scores": self.get_confidence_scores(),
            "overall_confidence": self.overall_confidence,
            "document_status": self.document_status,
            "resume_filename": self.resume_filename,
            "resume_text_preview": (self.resume_text or "")[:500],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            data["documents"] = [d.to_dict() for d in self.documents.all()]
            data["request_logs"] = [r.to_public_dict() for r in self.request_logs.all()]
            data["resume_text"] = self.resume_text
        return data

    def to_list_item(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "designation": self.designation,
            "extraction_status": self.extraction_status,
            "overall_confidence": self.overall_confidence,
            "document_status": self.document_status,
        }
