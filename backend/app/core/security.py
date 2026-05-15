from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .config import Settings, get_settings


class UploadValidationError(ValueError):
    pass


@dataclass(frozen=True)
class UploadValidationResult:
    filename: str
    extension: str
    content_type: str | None
    max_bytes: int


def safe_filename(filename: str) -> str:
    name = Path(filename or "upload").name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name or "upload"


def file_extension(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    return suffix[1:] if suffix.startswith(".") else suffix


def validate_upload_metadata(
    filename: str,
    content_type: str | None,
    kind: str,
    settings: Settings | None = None,
) -> UploadValidationResult:
    settings = settings or get_settings()
    safe_name = safe_filename(filename)
    extension = file_extension(safe_name)

    if kind == "video":
        allowed_exts = settings.allowed_video_exts
        max_bytes = settings.max_video_bytes
        allowed_content_prefixes = ("video/", "application/octet-stream")
    elif kind == "image":
        allowed_exts = settings.allowed_image_exts
        max_bytes = settings.max_image_bytes
        allowed_content_prefixes = ("image/", "application/octet-stream")
    else:
        raise UploadValidationError(f"unknown upload kind: {kind}")

    if extension not in allowed_exts:
        raise UploadValidationError(
            f"unsupported {kind} extension: .{extension or '<none>'}"
        )

    if content_type:
        normalized = content_type.lower()
        if not normalized.startswith(allowed_content_prefixes):
            raise UploadValidationError(
                f"unsupported {kind} content type: {content_type}"
            )

    return UploadValidationResult(
        filename=safe_name,
        extension=extension,
        content_type=content_type,
        max_bytes=max_bytes,
    )


def validate_upload_size(size_bytes: int, max_bytes: int) -> None:
    if size_bytes <= 0:
        raise UploadValidationError("uploaded file is empty")
    if size_bytes > max_bytes:
        raise UploadValidationError(
            f"uploaded file is too large: {size_bytes} > {max_bytes}"
        )

