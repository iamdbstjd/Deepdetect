# Face Embedding Matcher

현재 구현:
- `models/face/w600k_r50.onnx`를 OpenCV DNN으로 로드한다.
- 참조 이미지와 감지 얼굴 crop을 112x112로 resize한다.
- ArcFace 계열 전처리로 blob을 만든다.
- 512차원 embedding을 L2 normalize한다.
- cosine similarity가 threshold 이상이면 참조 인물로 판단한다.

기본 설정:

```bash
EMBED_FACE_MATCHER_MODE=arcface
EMBED_FACE_MATCH_MODEL=models/face/w600k_r50.onnx
EMBED_FACE_MATCH_THRESHOLD=0.35
```

Fallback:
- 모델 파일이 없거나 로딩 실패 시 `HistogramFaceMatcher`를 사용한다.
- histogram matcher는 개발용이며 실제 인물 식별 품질은 낮다.

현재 한계:
- 얼굴 landmark alignment가 아직 없다.
- 감지 box crop을 그대로 embedding에 넣는다.
- track 단위 score 누적이 아직 없다.

다음 보강:
- 얼굴 crop alignment
- track 단위 similarity 누적
- 샘플 영상 기준 threshold 튜닝
