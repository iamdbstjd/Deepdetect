# Phase 4: 캐릭터/이모지 대체 모드

구현 상태:
- `character` 모드에서 참조 인물로 match된 얼굴은 blur 대상에서 제외한다.
- match된 얼굴 위치에 캐릭터/이모지 이미지를 alpha blending으로 합성한다.
- 참조 인물이 아닌 얼굴과 번호판은 계속 blur한다.
- 캐릭터 asset이 없으면 기본 이모지 fallback을 생성해 사용한다.

관련 파일:
- `backend/app/vision/character_overlay.py`
- `backend/app/vision/renderer.py`
- `backend/app/vision/video_pipeline.py`

asset 규칙:
- `assets/characters/{character_id}.png`
- 파일명에는 영문, 숫자, `_`, `-`만 사용한다.
- PNG alpha channel이 있으면 투명도를 반영한다.
- PNG가 없거나 읽을 수 없으면 기본 fallback 이모지를 사용한다.

현재 한계:
- overlay 위치는 현재 face detection box 기준이다.
- track smoothing은 아직 고도화 전이다.
- 실제 얼굴 식별은 아직 histogram fallback이라 정확도가 낮다.

다음 보강:
- Phase 5에서 track ID와 box smoothing을 적용해 overlay 흔들림을 줄인다.
- 실제 ArcFace/InsightFace matcher를 붙여 참조 인물 판별 품질을 높인다.
- 샘플 영상 QA에서 overlay 흔들림을 기록한다.
