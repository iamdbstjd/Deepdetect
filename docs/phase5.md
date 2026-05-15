# Phase 5: Tracking과 흔들림 완화

구현 상태:
- IoU 기반 `DetectionTracker`를 추가했다.
- 같은 kind의 detection끼리 IoU로 track을 연결한다.
- matched box는 exponential smoothing을 적용한다.
- 짧은 detection miss는 이전 위치를 제한된 프레임 동안 유지한다.
- retained missing detection은 `observed=False`로 표시된다.

기본 설정:
- `EMBED_TRACKER_ENABLED=true`
- `EMBED_TRACKER_IOU_THRESHOLD=0.3`
- `EMBED_TRACKER_SMOOTHING_ALPHA=0.55`
- `EMBED_TRACKER_MAX_MISSING=2`

정책:
- 감지가 잠깐 빠지면 이전 위치에 blur를 유지해 원본 노출을 줄인다.
- 참조 인물 identity match는 `observed=True` detection에서만 수행한다.
- retained missing detection은 참조 인물로 재판정하지 않고 blur 대상으로 남긴다.

현재 한계:
- track ID는 영상 job 내부에서만 유지된다.
- 실제 재식별은 아직 없다.
- track 단위 reference score 누적은 아직 구현 전이다.

다음 보강:
- reference/non-reference 상태를 track 단위로 누적한다.
- 캐릭터 overlay도 track 상태를 이용해 더 안정화한다.
- 번호판 track smoothing 품질을 샘플 영상에서 별도 확인한다.
