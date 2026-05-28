import shutil
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.utils.errors import AppError


def get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def validate_upload_file(
    file: FileStorage | None,
    allowed_extensions: set[str],
    field_name: str = "file",
) -> str:
    if file is None or not file.filename:
        raise AppError(f"No {field_name} provided", 400, "missing_file")

    extension = get_extension(file.filename)
    if extension not in allowed_extensions:
        raise AppError(
            f"Invalid file type for {field_name}. Allowed: {', '.join(sorted(allowed_extensions))}",
            400,
            "invalid_file_type",
        )
    return extension


def save_upload_with_allowed(
    file: FileStorage,
    destination_folder: Path,
    allowed_extensions: set[str],
    prefix: str = "file",
    field_name: str = "file",
) -> tuple[str, str, str, str]:
    extension = validate_upload_file(file, allowed_extensions, field_name=field_name)
    destination_folder.mkdir(parents=True, exist_ok=True)
    safe_base = secure_filename(file.filename.rsplit(".", 1)[0]) or prefix
    stored_name = f"{prefix}_{uuid.uuid4().hex[:12]}_{safe_base[:80]}.{extension}"
    absolute_path = destination_folder / stored_name
    file.save(str(absolute_path))
    mime = file.mimetype or "application/octet-stream"
    return str(absolute_path), stored_name, extension, mime


def resume_upload_folder() -> Path:
    return Path(current_app.config["RESUME_UPLOAD_FOLDER"])


def document_upload_folder() -> Path:
    return Path(current_app.config["DOCUMENT_UPLOAD_FOLDER"])


def remove_file(path: str | None) -> None:
    if not path:
        return
    file_path = Path(path)
    if file_path.is_file():
        file_path.unlink(missing_ok=True)


def remove_directory(path: Path | str | None) -> None:
    if not path:
        return
    dir_path = Path(path)
    if dir_path.is_dir():
        shutil.rmtree(dir_path, ignore_errors=True)
