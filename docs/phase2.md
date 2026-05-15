# Phase 2: YOLO 기반 전체 blur MVP

구현 상태:
- 영상 파일을 OpenCV로 프레임 단위 처리한다.
- detector가 반환한 얼굴/번호판 영역을 Gaussian blur 처리한다.
- 결과는 `storage/outputs/{job_id}/result.mp4`로 저장한다.
- metadata에는 처리 phase, detector 종류, frame/detection 통계를 남긴다.

Detector 정책:
- 기본값 `EMBED_DETECTOR_MODE=auto`
- YOLO 모델 파일이 있으면 `YoloRegionDetector` 사용
- YOLO 모델 파일이 없으면 개발용 `HaarFaceFallbackDetector` 사용

주의:
- `HaarFaceFallbackDetector`는 얼굴만 잡는 개발용 fallback이다.
- 최종 요구사항의 얼굴/번호판 감지는 반드시 YOLO weight를 배치해야 충족된다.
- 번호판 blur는 `models/plate/license_plate_detector.pt`가 있어야 실제로 동작한다.

다음 보강:
- 실제 face YOLO weight 확보
- 실제 license plate YOLO weight 확보
- 샘플 영상으로 QA 표 작성
- 결과 영상에 원본 오디오 재결합
