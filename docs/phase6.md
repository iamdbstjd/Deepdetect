# Phase 6: 실시간 브라우저 카메라 미리보기

구현 상태:
- 실시간 session 생성 시 참조 이미지와 mode를 저장한다.
- session별 runtime에 prepared face matcher, character image, tracker를 보관한다.
- `/api/realtime/frame`은 JPEG/PNG frame을 받아 처리된 JPEG frame을 반환한다.
- WebSocket endpoint도 같은 realtime frame processor를 사용한다.
- 프론트엔드는 카메라 frame을 낮은 해상도 JPEG로 캡처해 주기적으로 서버에 보낸다.
- 처리된 frame은 canvas에 표시한다.

관련 파일:
- `backend/app/services/realtime_processor.py`
- `backend/app/services/realtime_service.py`
- `backend/app/api/routes_realtime.py`
- `frontend/src/app.js`

현재 처리 흐름:
1. 브라우저에서 카메라 frame 캡처
2. `/api/realtime/frame`에 `session_id`와 frame 업로드
3. OpenCV decode
4. detector 실행
5. session tracker update
6. preserve/character 정책 적용
7. blur/overlay 렌더링
8. JPEG encode 후 응답

현재 한계:
- HTTP polling 방식이라 지연이 있을 수 있다.
- WebSocket endpoint는 구현되어 있지만 프론트는 아직 HTTP fallback을 사용한다.
- 실제 YOLO weight와 face embedding 모델이 없으면 fallback detector/matcher 품질에 의존한다.

다음 보강:
- WebSocket client 전환
- 최신 frame 우선 처리/drop 정책 강화
- 실시간 전용 저해상도 detector 튜닝
- session cleanup을 주기적으로 실행
