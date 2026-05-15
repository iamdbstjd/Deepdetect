# Models

모델 파일은 용량과 라이선스 이슈 때문에 기본적으로 저장소에 커밋하지 않는다.

예상 구조:

```text
models/
  yolo/
    face_detector.pt
  plate/
    license_plate_detector.pt
  face/
    face_embedding.onnx
```

Phase 2:
- YOLO 얼굴 감지 모델 연결
- YOLO 번호판 감지 모델 연결

Phase 3:
- 얼굴 임베딩 모델 연결
- 참조 인물 similarity threshold 튜닝

