from __future__ import annotations

from enum import Enum


class ProcessingMode(str, Enum):
    PRESERVE = "preserve"
    CHARACTER = "character"


def parse_processing_mode(value: str) -> ProcessingMode:
    try:
        return ProcessingMode(value)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in ProcessingMode)
        raise ValueError(f"unsupported mode: {value}; expected one of {allowed}") from exc

