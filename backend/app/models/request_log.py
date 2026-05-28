from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RequestLog(db.Model):
    __tablename__ = "request_logs"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    request_type = db.Column(db.String(64), nullable=False, default="document_request")
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="success")  # success | failed
    message_source = db.Column(db.String(16), nullable=False, default="template")  # ai | template
    channel = db.Column(db.String(32), nullable=False, default="email")
    recipient = db.Column(db.String(255), nullable=True)
    delivery_status = db.Column(db.String(32), nullable=True)
    error_detail = db.Column(db.Text, nullable=True)  # internal only — never expose via API
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    candidate = db.relationship("Candidate", back_populates="request_logs")

    def to_dict(self) -> dict:
        """Public API shape — no internal error details."""
        return self.to_public_dict()

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "message": self.message,
            "status": self.status,
            "source": self.message_source,
            "channel": self.channel,
            "recipient": self.recipient,
            "delivery_status": self.delivery_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
