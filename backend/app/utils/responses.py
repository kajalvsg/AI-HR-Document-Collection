from flask import jsonify


def success_response(data=None, message: str | None = None, status: int = 200):
    body = {"success": True}
    if message:
        body["message"] = message
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def error_response(
    message: str,
    error_code: str = "bad_request",
    status: int = 400,
    details: dict | None = None,
):
    body = {"success": False, "error": error_code, "message": message}
    if details:
        body["details"] = details
    return jsonify(body), status
