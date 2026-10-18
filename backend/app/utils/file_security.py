import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from contextlib import contextmanager
from fastapi import HTTPException
from app.config import settings

class FileSecurityError(Exception):
    pass

def validate_uploaded_file_size(file_size: int):
    """Enforces maximum archive upload size."""
    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds maximum allowed limit of {settings.max_upload_size_bytes // (1024 * 1024)}MB."
        )

def is_allowed_file(filename: str) -> bool:
    """Checks if file extension is supported."""
    ext = Path(filename).suffix.lower()
    return ext in settings.allowed_extensions

def safe_extract_zip(zip_path: Path, target_dir: Path) -> list[Path]:
    """
    Safely extracts a ZIP archive with strict Path Traversal (Zip Slip) protection,
    bomb protection (size/count limit), and nested archive guards.
    """
    extracted_files: list[Path] = []
    total_uncompressed_size = 0
    max_uncompressed_size = 60 * 1024 * 1024  # 60MB max uncompressed
    target_dir = target_dir.resolve()

    with zipfile.ZipFile(zip_path, 'r') as archive:
        infolist = archive.infolist()
        if len(infolist) > settings.max_extracted_files:
            raise FileSecurityError(f"ZIP contains too many files ({len(infolist)}). Limit is {settings.max_extracted_files}.")

        for member in infolist:
            # 1. Zip Slip / Path Traversal Check
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise FileSecurityError(f"Path traversal detected in archive entry: {member.filename}")

            destination = (target_dir / member.filename).resolve()
            if not str(destination).startswith(str(target_dir)):
                raise FileSecurityError(f"Illegal path escaping target directory: {member.filename}")

            # 2. Size limit checks
            total_uncompressed_size += member.file_size
            if total_uncompressed_size > max_uncompressed_size:
                raise FileSecurityError("Archive exceeds safe uncompressed size limit (Decompression Bomb protection).")

            # 3. Skip directories
            if member.is_dir():
                continue

            # 4. Check extension
            if not is_allowed_file(member.filename):
                # We skip unsupported/binary files safely
                continue

            # 5. Extract safely
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, open(destination, "wb") as target:
                shutil.copyfileobj(source, target)
            extracted_files.append(destination)

    return extracted_files

@contextmanager
def temporary_workspace():
    """Provides an isolated temporary workspace directory that is cleaned up on exit."""
    temp_dir = Path(tempfile.mkdtemp(prefix="genai_audit_"))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
