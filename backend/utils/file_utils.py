"""File handling utilities."""

from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, create if not."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    """Sanitize filename for safe storage."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)


def get_file_size(path: Path) -> int:
    """Get file size in bytes."""
    return path.stat().st_size if path.exists() else 0
