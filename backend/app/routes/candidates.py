from flask import Blueprint, request

from app.services.candidate_service import CandidateService
from app.utils.errors import AppError
from app.utils.responses import error_response, success_response

candidates_bp = Blueprint("candidates", __name__)


@candidates_bp.errorhandler(AppError)
def handle_app_error(err: AppError):
    return error_response(err.message, err.error_code, err.status_code)


@candidates_bp.route("/upload", methods=["POST"])
def upload_resume():
    resume = request.files.get("resume") or request.files.get("file")
    candidate = CandidateService.upload_resume(resume)
    return success_response(
        data=candidate.to_dict(),
        message="Resume uploaded and processed successfully",
        status=201,
    )


@candidates_bp.route("", methods=["GET"])
def list_candidates():
    items = CandidateService.list_candidates()
    return success_response(data={"candidates": items, "count": len(items)})


@candidates_bp.route("/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id: int):
    candidate = CandidateService.get_candidate(candidate_id)
    return success_response(data=candidate.to_dict(include_relations=True))


@candidates_bp.route("/<int:candidate_id>", methods=["DELETE"])
def delete_candidate(candidate_id: int):
    result = CandidateService.delete_candidate(candidate_id)
    return success_response(
        data=result,
        message="Candidate deleted successfully",
    )


@candidates_bp.route("/<int:candidate_id>/request-documents", methods=["POST"])
def request_documents(candidate_id: int):
    result = CandidateService.request_documents(candidate_id)
    return success_response(
        data=result,
        message="Document request message generated",
    )


@candidates_bp.route("/<int:candidate_id>/submit-documents", methods=["POST"])
def submit_documents(candidate_id: int):
    pan = request.files.get("pan")
    aadhaar = request.files.get("aadhaar")
    result = CandidateService.submit_documents(candidate_id, pan, aadhaar)
    return success_response(
        data=result,
        message="Documents uploaded successfully",
    )
