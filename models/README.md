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
    w600k_r50.onnx
```

기본 실행은 위 파일명을 찾는다. 다른 파일명을 사용할 경우 환경변수로 경로를 지정한다.

```bash
EMBED_YOLO_FACE_MODEL=models/yolo/face_detector.pt
EMBED_YOLO_PLATE_MODEL=models/plate/license_plate_detector.pt
EMBED_FACE_MATCH_MODEL=models/face/w600k_r50.onnx
```
