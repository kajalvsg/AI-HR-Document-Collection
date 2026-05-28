from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Document(db.Model):
    __tablename__ = "documents"
    __table_args__ = (
        db.UniqueConstraint(
            "candidate_id", "document_type", name="uq_candidate_document_type"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    document_type = db.Column(db.String(32), nullable=False)  # pan | aadhaar
    file_path = db.Column(db.String(1024), nullable=False)
    original_filename = db.Column(db.String(512), nullable=False)
    mime_type = db.Column(db.String(128), nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    candidate = db.relationship("Candidate", back_populates="documents")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "document_type": self.document_type,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
