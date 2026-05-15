# Phase 3: 참조 인물 원본 유지

구현 상태:
- 업로드된 참조 이미지를 읽어 face matcher를 준비한다.
- detector가 반환한 `face` detection에 대해 참조 이미지와 match score를 계산한다.
- `preserve` 모드에서 참조 인물로 판단된 얼굴은 blur 대상에서 제외한다.
- 참조 인물이 아닌 얼굴, 번호판, 애매한 얼굴은 계속 blur한다.

현재 matcher:
- `HistogramFaceMatcher`
- 실제 얼굴 임베딩 모델이 아니라 개발용 fallback이다.
- 색상 histogram 기반이므로 실제 인물 식별 품질은 낮다.

안전 정책:
- matcher가 match로 판단하지 않으면 blur한다.
- `EMBED_FACE_MATCHER_MODE=disabled`로 두면 모든 얼굴을 blur한다.
- 실제 시연 품질을 위해서는 ArcFace/InsightFace 계열 임베딩 모델 연결이 필요하다.

다음 보강:
- 참조 이미지에서 얼굴 crop을 먼저 잡고 그 crop으로 임베딩/비교 수행
- track 단위 누적 score
- similarity threshold 튜닝
- `character` 모드에서 참조 얼굴 overlay 처리
