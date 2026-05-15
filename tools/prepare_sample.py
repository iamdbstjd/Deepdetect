from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import get_settings  # noqa: E402
from backend.app.vision.detections import Detection  # noqa: E402
from backend.app.vision.yolo_detector import build_detector  # noqa: E402


class Y4MReader:
    def __init__(self, path: Path):
        self.path = path
        self.handle = path.open("rb")
        header = self.handle.readline().decode("ascii", errors="replace").strip()
        if not header.startswith("YUV4MPEG2 "):
            self.handle.close()
            raise ValueError(f"not a Y4M file: {path}")
        self.width, self.height, self.fps = self._parse_header(header)
        self.frame_size = self.width * self.height * 3 // 2

    def read(self) -> tuple[bool, np.ndarray | None]:
        frame_header = self.handle.readline()
        if not frame_header:
            return False, None
        if not frame_header.startswith(b"FRAME"):
            raise ValueError(f"invalid Y4M frame marker in {self.path}")
        payload = self.handle.read(self.frame_size)
        if len(payload) != self.frame_size:
            return False, None
        yuv = np.frombuffer(payload, dtype=np.uint8).reshape((self.height * 3 // 2, self.width))
        return True, cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)

    def release(self) -> None:
        self.handle.close()

    @staticmethod
    def _parse_header(header: str) -> tuple[int, int, float]:
        width = 0
        height = 0
        fps = 30.0
        for token in header.split()[1:]:
            if token.startswith("W"):
                width = int(token[1:])
            elif token.startswith("H"):
                height = int(token[1:])
            elif token.startswith("F") and ":" in token:
                numerator, denominator = token[1:].split(":", 1)
                fps = int(numerator) / max(1, int(denominator))
        if width <= 0 or height <= 0:
            raise ValueError(f"Y4M header has invalid dimensions: {header}")
        return width, height, fps


class CaptureReader:
    def __init__(self, path: Path):
        self.capture = cv2.VideoCapture(str(path))
        if not self.capture.isOpened():
            raise ValueError(f"OpenCV cannot open video: {path}")
        self.width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.capture.get(cv2.CAP_PROP_FPS) or 30.0
        if self.width <= 0 or self.height <= 0:
            self.capture.release()
            raise ValueError(f"OpenCV reported invalid dimensions for: {path}")

    def read(self) -> tuple[bool, np.ndarray | None]:
        ok, frame = self.capture.read()
        return ok, frame if ok else None

    def release(self) -> None:
        self.capture.release()


def open_reader(path: Path) -> CaptureReader | Y4MReader:
    try:
        return CaptureReader(path)
    except ValueError:
        if path.suffix.lower() == ".y4m":
            return Y4MReader(path)
        raise


def create_writer(path: Path, fps: float, width: int, height: int) -> cv2.VideoWriter:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"cannot create output video: {path}")
    return writer


def crop_detection(frame: np.ndarray, detection: Detection, padding: float) -> np.ndarray:
    height, width = frame.shape[:2]
    box = detection.clipped(width, height, padding)
    if not box.is_valid:
        raise RuntimeError("selected face detection is invalid after clipping")
    return frame[box.y1 : box.y2, box.x1 : box.x2]


def center_face_fallback(frame: np.ndarray) -> tuple[Detection, str]:
    height, width = frame.shape[:2]
    box_width = int(width * 0.34)
    box_height = int(height * 0.55)
    x1 = max(0, (width - box_width) // 2)
    y1 = max(0, int(height * 0.18))
    return (
        Detection(
            kind="face",
            x1=x1,
            y1=y1,
            x2=min(width, x1 + box_width),
            y2=min(height, y1 + box_height),
            confidence=0.0,
            label="center_fallback",
        ),
        "center_fallback",
    )


def select_best_face(detections: list[Detection]) -> Detection | None:
    faces = [detection for detection in detections if detection.kind == "face" and detection.is_valid]
    if not faces:
        return None
    return max(
        faces,
        key=lambda detection: (
            (detection.x2 - detection.x1) * (detection.y2 - detection.y1),
            detection.confidence,
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a short sample clip and reference face.")
    parser.add_argument("--source", type=Path, default=Path("samples/videos/akiyo_cif.y4m"))
    parser.add_argument("--output-video", type=Path, default=Path("samples/videos/akiyo_short.mp4"))
    parser.add_argument(
        "--reference-output",
        type=Path,
        default=Path("samples/references/akiyo_reference.jpg"),
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=Path("samples/reports/akiyo_preparation.json"),
    )
    parser.add_argument("--max-frames", type=int, default=90)
    parser.add_argument("--reference-padding", type=float, default=0.18)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.exists():
        raise FileNotFoundError(f"sample source does not exist: {args.source}")

    settings = get_settings()
    detector = build_detector(settings)
    reader = open_reader(args.source)
    writer = create_writer(args.output_video, reader.fps, reader.width, reader.height)

    best_face: Detection | None = None
    best_frame: np.ndarray | None = None
    first_frame: np.ndarray | None = None
    frames_written = 0
    face_detection_frames = 0
    try:
        while frames_written < args.max_frames:
            ok, frame = reader.read()
            if not ok or frame is None:
                break
            if first_frame is None:
                first_frame = frame.copy()
            writer.write(frame)
            detections = detector.detect(frame)
            face = select_best_face(detections)
            if face:
                face_detection_frames += 1
                if best_face is None:
                    best_face = face
                    best_frame = frame.copy()
                else:
                    current_area = (face.x2 - face.x1) * (face.y2 - face.y1)
                    best_area = (best_face.x2 - best_face.x1) * (best_face.y2 - best_face.y1)
                    if (current_area, face.confidence) > (best_area, best_face.confidence):
                        best_face = face
                        best_frame = frame.copy()
            frames_written += 1
    finally:
        writer.release()
        reader.release()

    if frames_written == 0 or first_frame is None:
        raise RuntimeError(f"no frames were decoded from: {args.source}")

    selection = "yolo"
    if best_face is None or best_frame is None:
        best_face, selection = center_face_fallback(first_frame)
        best_frame = first_frame

    reference_crop = crop_detection(best_frame, best_face, args.reference_padding)
    args.reference_output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.reference_output), reference_crop):
        raise RuntimeError(f"cannot write reference image: {args.reference_output}")

    report = {
        "source": str(args.source),
        "output_video": str(args.output_video),
        "reference_image": str(args.reference_output),
        "frames_written": frames_written,
        "fps": reader.fps,
        "width": reader.width,
        "height": reader.height,
        "detector": type(detector).__name__,
        "detector_confidence": settings.detector_confidence,
        "face_detection_frames": face_detection_frames,
        "reference_selection": selection,
        "reference_detection": asdict(best_face),
    }
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
