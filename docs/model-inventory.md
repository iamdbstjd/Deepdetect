# Model Inventory

작성일: 2026-05-15

## 다운로드/배치 완료

| 용도 | 파일 | 출처 | SHA256 |
|---|---|---|---|
| YOLO 얼굴 감지 | `models/yolo/face_detector.pt` | `https://github.com/lindevs/yolov8-face/releases/latest/download/yolov8n-face-lindevs.pt` | `b038ca653b503453a94f6e12d76feca6840b2a97d7a1322b4498c5e922f29832` |
| YOLO 번호판 감지 | `models/plate/license_plate_detector.pt` | `https://huggingface.co/Koushim/yolov8-license-plate-detection/resolve/main/best.pt` | `2d95861825bb4184404344c9cf809f40fd31dba785fe54e8ba5b9a3583789822` |
| 얼굴 임베딩 | `models/face/w600k_r50.onnx` | 로컬 InsightFace cache: `/home/bys0626/.insightface/models/buffalo_l/w600k_r50.onnx` | `4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43` |

## 현재 코드 연결 상태

- 얼굴/번호판 감지:
  - 모델 파일이 있으므로 기본 `EMBED_DETECTOR_MODE=auto`에서 `YoloRegionDetector`가 선택된다.
  - `models/yolo/face_detector.pt`와 `models/plate/license_plate_detector.pt`를 모두 로드한다.
- 얼굴 임베딩:
  - `models/face/w600k_r50.onnx`를 OpenCV DNN 기반 `ArcFaceMatcher`로 사용한다.
  - 모델 파일이 없거나 로딩 실패하면 개발용 `HistogramFaceMatcher`로 fallback한다.

## 확인 결과

```text
YOLO model load: ok
App detector: YoloRegionDetector
Current face matcher: ArcFaceMatcher
```

## 다음 작업

- 참조 이미지에서 얼굴 crop/alignment 후 embedding 추출
- 감지된 얼굴 crop embedding과 cosine similarity 비교
- 기존 `HistogramFaceMatcher`는 fallback 또는 테스트용으로 유지
