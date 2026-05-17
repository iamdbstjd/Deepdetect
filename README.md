# deepdetect

[English](README.md) | [KR](README.ko.md)

deepdetect is a privacy-first video anonymization web service. It detects faces and license plates with YOLO, then applies blur, reference-person preservation, or a character/emoji overlay depending on the selected mode.

The current build focuses on high-quality saved-video processing, with a browser-camera realtime preview for demonstrations.

## Features

- Upload a video and a reference face image.
- Detect faces and license plates using YOLO model wrappers.
- Blur all detected privacy regions.
- Preserve the reference person while blurring other faces.
- Replace the reference person's face with a glossy emoji/character overlay.
- Keep character overlays stable with IoU tracking and bounding-box smoothing.
- Preview realtime processing from the browser camera.
- Download the processed result video.
- Switch the web UI between KR and ENG.

## Demo Evidence

The sample QA run uses the public Xiph Derf `akiyo` test sequence.

| Check | Result |
|---|---:|
| Sample frames processed | 90 |
| Face detections in blur mode | 90 / 90 |
| Average face-region sharpness reduction after blur | 98.05% |
| Minimum face-region sharpness reduction after blur | 95.35% |
| Preserve-mode reference matches | 90 / 90 |
| Character overlays | 90 / 90 |

Artifacts:

- Blur result: [samples/outputs/akiyo_blur.mp4](samples/outputs/akiyo_blur.mp4)
- Preserve result: [samples/outputs/akiyo_preserve.mp4](samples/outputs/akiyo_preserve.mp4)
- Character result: [samples/outputs/akiyo_character.mp4](samples/outputs/akiyo_character.mp4)
- Visual QA sheet: [samples/reports/akiyo_contact_sheet.jpg](samples/reports/akiyo_contact_sheet.jpg)
- Sample QA graph: [samples/reports/performance_trend.png](samples/reports/performance_trend.png)
- Blur metrics: [samples/reports/akiyo_blur_quality.json](samples/reports/akiyo_blur_quality.json)

![deepdetect sample QA metrics](samples/reports/performance_trend.png)

## Architecture

```mermaid
flowchart TD
    User[User] --> WebUI[Static Web UI<br/>Video upload, reference upload, mode selection]
    WebUI --> JobsAPI[FastAPI Jobs API]
    WebUI --> RealtimeAPI[FastAPI Realtime API]

    JobsAPI --> JobService[Job Service<br/>metadata, status, cancellation]
    JobService --> Queue[Background Job Queue]
    Queue --> Pipeline[BlurVideoPipeline]

    RealtimeAPI --> RealtimeSession[Realtime Session Service]
    RealtimeSession --> FrameProcessor[Realtime Frame Processor]
    FrameProcessor --> VisionCore[Shared Vision Core]
    Pipeline --> VisionCore

    VisionCore --> Detector[YOLO Region Detector<br/>faces and plates]
    VisionCore --> Matcher[ArcFace Matcher<br/>reference identity]
    VisionCore --> Tracker[IoU Tracker<br/>smoothing and short miss retention]
    VisionCore --> Renderer[Privacy Renderer<br/>blur and character overlay]

    Renderer --> OutputVideo[Processed MP4]
    Renderer --> OutputFrame[Processed JPEG Frame]

    JobService --> Storage[(Storage<br/>uploads, references, results, temp)]
    OutputVideo --> Storage
    Storage --> Download[Result Download]
    Download --> User
    OutputFrame --> WebUI
```

## Processing Modes

| Mode | Reference person | Other faces | License plates |
|---|---|---|---|
| `blur` | blurred | blurred | blurred |
| `preserve` | kept original | blurred | blurred |
| `character` | replaced with emoji/character | blurred | blurred |

The web UI exposes `preserve` and `character` for the main product flow. The `blur` mode is available in the sample tooling and pipeline for QA.

## Project Layout

```text
backend/
  app/
    api/          FastAPI routes
    core/         settings, paths, security helpers
    services/     jobs, queue, realtime processing
    vision/       YOLO detector, matcher, tracker, renderer, pipeline
  tests/          unittest test suite
frontend/
  index.html      deepdetect UI
  src/app.js      upload, realtime, KR/ENG language toggle
  styles/app.css  responsive product styling
models/
  yolo/           face detector weights
  plate/          license plate detector weights
  face/           ArcFace ONNX model
samples/
  videos/         sample source and short clips
  outputs/        processed demo videos
  reports/        QA reports and screenshots
tools/
  prepare_sample.py
  run_sample_pipeline.py
  export_sample_contact_sheet.py
  measure_blur_quality.py
```

## Requirements

- Python 3.11+
- OpenCV
- FastAPI
- Ultralytics YOLO
- Existing model files under `models/`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Model Files

deepdetect currently uses two YOLO model files:

| Model | Path | Current role |
|---|---|---|
| YOLO face detector | `models/yolo/face_detector.pt` | Detect face bounding boxes |
| YOLO license plate detector | `models/plate/license_plate_detector.pt` | Detect license plate bounding boxes |

No custom YOLO fine-tuning has been performed in this repository yet. The model files are pretrained weights documented in [docs/model-inventory.md](docs/model-inventory.md).

Default model paths:

```text
models/yolo/face_detector.pt
models/plate/license_plate_detector.pt
models/face/w600k_r50.onnx
```

The downloaded model inventory and hashes are documented in [docs/model-inventory.md](docs/model-inventory.md).

## Future Fine-Tuning Datasets

These datasets are suitable candidates for a future, honest fine-tuning or benchmark pass. They are not claimed as training data for the current uploaded model weights.

| Area | Dataset | Why it is relevant |
|---|---|---|
| Face detection | [WIDER FACE](http://shuoyang1213.me/WIDERFACE/) | Face detection benchmark with large variation in scale, pose, and occlusion. TensorFlow Datasets documents 32,203 images and 393,703 labeled faces. |
| License plate detection | [CCPD](https://github.com/detectRecog/ccpd) | Large license plate detection/recognition dataset with challenging subsets such as blur, rotation, tilt, and challenge images. |
| License plate detection | [UFPR-ALPR](https://web.inf.ufpr.br/vri/databases/ufpr-alpr/) | Vehicle and license plate dataset associated with ALPR research using the YOLO detector. |

Useful environment variables:

```bash
EMBED_DETECTOR_MODE=auto
EMBED_YOLO_FACE_MODEL=models/yolo/face_detector.pt
EMBED_YOLO_PLATE_MODEL=models/plate/license_plate_detector.pt

EMBED_FACE_MATCHER_MODE=arcface
EMBED_FACE_MATCH_MODEL=models/face/w600k_r50.onnx
EMBED_FACE_MATCH_THRESHOLD=0.35

EMBED_TRACKER_ENABLED=true
EMBED_TRACKER_IOU_THRESHOLD=0.3
EMBED_TRACKER_SMOOTHING_ALPHA=0.55
EMBED_TRACKER_MAX_MISSING=2
```

## Sample QA Workflow

Prepare the sample:

```bash
python tools/prepare_sample.py --max-frames 90
```

Run all demo modes:

```bash
python tools/run_sample_pipeline.py --mode blur --output samples/outputs/akiyo_blur.mp4 --report samples/reports/akiyo_blur.json
python tools/run_sample_pipeline.py --mode preserve --output samples/outputs/akiyo_preserve.mp4 --report samples/reports/akiyo_preserve.json
python tools/run_sample_pipeline.py --mode character --output samples/outputs/akiyo_character.mp4 --report samples/reports/akiyo_character.json
```

Export visual QA and blur metrics:

```bash
python tools/export_sample_contact_sheet.py
python tools/measure_blur_quality.py
```

## API Summary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/jobs/video` | Upload video/reference and create a processing job |
| `GET` | `/api/jobs/{job_id}` | Read job status |
| `POST` | `/api/jobs/{job_id}/cancel` | Cancel a job |
| `GET` | `/api/jobs/{job_id}/result` | Download processed video |
| `POST` | `/api/realtime/sessions` | Create realtime processing session |
| `POST` | `/api/realtime/frame` | Process one camera frame |
| `WS` | `/api/realtime/sessions/{session_id}/ws` | Realtime websocket frame endpoint |

## Tests

```bash
python -m unittest discover -s backend/tests -v
node --check frontend/src/app.js
```

Current verification:

- Backend tests: 26 passing.
- Frontend syntax check: passing.
- Browser rendering checked with Playwright for desktop and mobile.
- Blur sample QA checked visually and with sharpness metrics.

## Limitations

- Small, far, heavily occluded, or partial faces may be missed.
- License plate quality depends on the selected plate YOLO model and target region.
- Reference-person matching is pragmatic, not a security-grade identity system.
- Apple emoji assets are not bundled; the default emoji is a custom generated glossy asset.

## Roadmap

- Add a traffic sample with visible license plates for plate blur QA.
- Add result preview playback in the web UI.
- Add user-uploaded custom character assets.
- Improve realtime throughput with frame skipping, batching, or ONNX/TensorRT/OpenVINO backends.
- Add a deployment profile for the final embedded target.

## License

MIT License. See [LICENSE](LICENSE).
