import io
import zipfile
import pytest
from pathlib import Path
from app.utils.file_security import safe_extract_zip, FileSecurityError, is_allowed_file

def test_allowed_files():
    assert is_allowed_file("model.py") is True
    assert is_allowed_file("config.json") is True
    assert is_allowed_file("archive.zip") is True
    assert is_allowed_file("malicious.exe") is False
    assert is_allowed_file("payload.sh") is False

def test_safe_zip_extraction(tmp_path):
    # Create valid zip
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, 'w') as zf:
        zf.writestr("app/main.py", "print('hello world')")
        zf.writestr("app/config.json", '{"model": "gpt-4"}')

    zip_file = tmp_path / "valid.zip"
    zip_file.write_bytes(zip_bytes.getvalue())

    dest_dir = tmp_path / "extracted"
    extracted = safe_extract_zip(zip_file, dest_dir)
    assert len(extracted) == 2
    assert (dest_dir / "app" / "main.py").exists()

def test_zip_slip_protection(tmp_path):
    # Craft malicious zip with directory traversal
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, 'w') as zf:
        zf.writestr("../../etc/passwd", "root:x:0:0:root")

    zip_file = tmp_path / "malicious_slip.zip"
    zip_file.write_bytes(zip_bytes.getvalue())

    dest_dir = tmp_path / "extracted_slip"
    with pytest.raises(FileSecurityError) as exc_info:
        safe_extract_zip(zip_file, dest_dir)
    assert "Path traversal" in str(exc_info.value) or "escaping" in str(exc_info.value)
