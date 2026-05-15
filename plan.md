# YOLO 기반 얼굴/번호판 익명화 웹 서비스 상세 계획

작성일: 2026-05-15  
상태: 요구사항 인터뷰 완료, 구현 전 계획 단계

## 1. 프로젝트 목표

사용자가 업로드한 영상 또는 브라우저 카메라 실시간 영상에서 개인정보가 될 수 있는 얼굴과 차량 번호판을 자동으로 감지하고 익명화하는 웹 서비스를 만든다.

핵심 목표는 다음과 같다.

- YOLO를 사용해 얼굴과 차량 번호판 위치를 감지한다.
- 사용자가 참조 얼굴 사진을 업로드하면, 해당 사람은 기본 모드에서 원본 얼굴을 유지한다.
- 참조 사진과 일치하지 않는 다른 사람 얼굴은 블러 처리한다.
- 차량 번호판은 항상 블러 처리한다.
- 캐릭터 모드에서는 참조 사진과 일치한 사람의 얼굴 위치에 이모지/캐릭터를 자연스럽게 합성한다.
- 저장된 영상 처리 결과의 시각적 품질을 최우선으로 한다.
- 실시간 기능은 브라우저 카메라 미리보기 수준으로 제공한다.

## 2. 확정된 요구사항

### 2.1 주요 사용 흐름

#### 저장 영상 처리

1. 사용자가 영상 파일을 업로드한다.
2. 사용자가 참조 얼굴 사진을 업로드한다.
3. 사용자가 처리 모드를 선택한다.
   - 참조 인물 원본 유지 모드
   - 참조 인물 캐릭터/이모지 대체 모드
4. 서버가 영상을 프레임 단위로 처리한다.
5. 처리된 결과 영상을 사용자가 미리보기하거나 다운로드한다.

#### 실시간 미리보기

1. 사용자가 브라우저에서 카메라 권한을 허용한다.
2. 참조 사진과 처리 모드를 선택한다.
3. 카메라 영상에서 얼굴/번호판 블러 또는 캐릭터 대체 결과를 실시간으로 확인한다.

### 2.2 합격 기준

- 얼굴과 번호판이 대부분 잘 감지되고 처리된다.
- 멀리 있는 얼굴이나 반쪽만 보이는 얼굴은 일부 놓쳐도 허용한다.
- 참조 사진 인물은 기본 모드에서 대부분 원본 얼굴로 유지된다.
- 참조 사진 인물이 아닌 다른 사람은 블러 처리된다.
- 캐릭터 모드에서는 참조 인물 얼굴 위치에 이모지/캐릭터가 흔들림 없이 붙어야 한다.
- 저장 영상은 처리 시간이 조금 오래 걸려도 결과물이 보기 좋아야 한다.
- 실시간 기능은 저장 영상만큼 완벽하지 않아도, 같은 핵심 로직을 미리보기 수준으로 보여줘야 한다.

### 2.3 정량 QA 기준

최종 평가는 실제 샘플 영상 기준으로 한다. 아래 수치는 1차 목표값이며, 모델/하드웨어 제약에 따라 조정할 수 있다.

| 평가 항목 | 1차 합격 기준 | 비고 |
|---|---:|---|
| 가시 얼굴 처리율 | 90% 이상 | 멀리 있거나 반쪽만 보이는 얼굴은 평가 제외 가능 |
| 가시 번호판 처리율 | 90% 이상 | 흐림/가림/극소형 번호판은 평가 제외 가능 |
| 참조 인물 보존 성공률 | 85% 이상 | 정면/약간 측면 기준 |
| 참조 인물이 아닌 얼굴 원본 노출 | 0건 목표 | 애매하면 blur 처리 |
| 캐릭터 overlay 흔들림 | 육안상 거슬리지 않을 것 | 필요 시 track 중심 이동량을 픽셀 기준으로 측정 |
| 저장 영상 재생 가능성 | 100% | 결과 파일이 브라우저/일반 플레이어에서 재생되어야 함 |
| 실시간 미리보기 | 기능 시연 가능 | 저장 영상 품질보다 낮아도 허용 |

평가 방식:
- 영상별로 `총 가시 얼굴 수`, `정상 blur 수`, `누락 수`, `참조 인물 유지 성공 수`, `번호판 처리 수`를 수동 체크한다.
- 반쪽 얼굴, 지나치게 작은 얼굴, 심한 가림은 별도 `허용 누락`으로 분류한다.
- 캐릭터 모드는 짧은 구간을 반복 재생해 overlay가 튀는지 확인한다.

### 2.4 비목표

- 완벽한 얼굴 인증 보안은 목표가 아니다.
- 모든 각도, 마스크, 가림, 반쪽 얼굴까지 100% 인식하는 것은 목표가 아니다.
- 로그인, 사용자 작업 기록, 관리자 페이지는 현재 범위에 포함하지 않는다.
- 법적 개인정보 컴플라이언스 인증 수준까지 다루지 않는다.
- 저장 영상 품질이 확보되기 전에 실시간 FPS 최적화에 과도하게 집중하지 않는다.

## 3. 핵심 설계 원칙

1. YOLO는 위치 감지용으로 사용한다.
   - 얼굴 bounding box 감지
   - 번호판 bounding box 감지

2. 참조 인물 판별은 별도 얼굴 임베딩 모델로 처리한다.
   - YOLO만으로는 "이 사람이 참조 사진과 같은 사람인지" 판단할 수 없다.
   - YOLO로 얼굴 영역을 찾고, 얼굴 crop을 임베딩 모델에 넣어 유사도를 비교한다.

3. 저장 영상 처리 품질을 실시간보다 우선한다.
   - 저장 영상은 고품질 blur, padding, tracking, smoothing을 적용한다.
   - 실시간은 해상도 축소, 프레임 샘플링, 간단한 smoothing으로 동작성을 확보한다.

4. 프레임 단위 감지 결과를 그대로 쓰지 않는다.
   - 얼굴 박스가 매 프레임 흔들리면 이모지/캐릭터가 떨린다.
   - tracking과 bounding box smoothing을 적용한다.

5. 처음부터 임베디드 최적화에 묶이지 않는다.
   - 1차 목표는 웹 서비스 기능 완성이다.
   - 이후 대상 보드가 정해지면 모델 경량화, ONNX 변환, 하드웨어 가속을 진행한다.

## 4. 권장 시스템 구조

```text
frontend/
  사용자가 영상, 참조 사진, 처리 모드, 캐릭터를 선택
  결과 영상 미리보기/다운로드
  브라우저 카메라 실시간 미리보기

backend/
  업로드 API
  작업 생성/상태 조회 API
  결과 영상 다운로드 API
  실시간 프레임 처리 API
  background worker/job queue
  작업 실패/취소/cleanup 관리

vision pipeline/
  YOLO 얼굴 감지
  YOLO 번호판 감지
  참조 얼굴 임베딩 추출
  감지된 얼굴과 참조 얼굴 track 단위 유사도 비교
  tracking/smoothing
  blur/emoji rendering
  output video encoding

storage/
  업로드 원본
  참조 이미지
  처리 결과 영상
  임시 프레임/작업 상태
  만료된 파일 cleanup
```

## 5. 제안 기술 스택

기술 선택은 구현 편의성과 결과 품질을 기준으로 한다.

### 5.1 백엔드

- Python 기반 API 서버
- 영상 처리와 AI 추론을 같은 언어에서 다루기 쉽기 때문에 Python을 우선 사용한다.
- 후보:
  - FastAPI
  - OpenCV
  - FFmpeg
  - PyTorch 또는 ONNX Runtime

### 5.2 프론트엔드

- 단일 웹 화면 중심의 UI
- 후보:
  - React
  - Vite
  - HTML video/canvas

### 5.3 AI/비전 구성

- YOLO face detector
- YOLO license plate detector
- 얼굴 임베딩 모델
- 간단한 tracker
  - IoU 기반 tracking
  - 필요 시 SORT/ByteTrack 계열로 확장
- bounding box smoothing
  - 이동 평균
  - confidence 기반 안정화

### 5.4 모델 확보 전략

1차 구현은 공개 pretrained 모델을 사용한다.

- 얼굴 감지:
  - YOLO 기반 face detector를 우선 사용한다.
  - 일반 object detection 모델보다 얼굴 전용 weight를 우선 검토한다.
- 번호판 감지:
  - 번호판 전용 YOLO weight를 우선 사용한다.
  - 국내 번호판이 잘 잡히지 않으면 샘플 데이터 기반 fine-tuning을 검토한다.
- 얼굴 임베딩:
  - 참조 인물 판별용 face recognition/embedding 모델을 사용한다.
  - YOLO는 얼굴 위치만 찾고, 동일 인물 판별은 임베딩 유사도로 처리한다.

모델 선택 기준:
- 저장 영상 샘플에서 얼굴/번호판 처리율이 높은가
- 추론 속도가 실시간 preview에 최소한으로 대응 가능한가
- ONNX export 또는 경량화 가능성이 있는가
- 라이선스와 배포 조건이 프로젝트 사용 목적에 맞는가

모델 교체 기준:
- 샘플 영상에서 얼굴 또는 번호판 처리율이 80% 미만이면 다른 weight를 검토한다.
- 참조 인물 오판정이 반복되면 임베딩 모델 또는 similarity threshold를 조정한다.
- 실시간 preview가 지나치게 느리면 더 작은 모델이나 낮은 해상도를 사용한다.

### 5.5 배포/실행

초기 개발:
- 로컬 개발 서버
- CPU/GPU 사용 가능 환경

후속 임베디드 단계:
- 대상 보드 확정 후 최적화
- 모델 경량화
- ONNX export
- 하드웨어별 inference backend 검토

임베디드 관련 초기 전제:
- 1차 MVP는 PC/노트북 또는 개발 서버에서 웹 서비스로 구현한다.
- 최종 시연이 임베디드 보드에서 직접 실행되어야 한다면, Phase 2 완료 직후 목표 보드를 확정한다.
- 임베디드 보드가 확정되기 전에는 특정 하드웨어 가속 API에 강하게 의존하지 않는다.
- 모델과 pipeline은 나중에 ONNX Runtime, TensorRT, OpenVINO, NPU SDK 등으로 옮길 수 있도록 wrapper 구조로 작성한다.

## 6. 저장 영상 처리 파이프라인

### 6.1 입력

- 영상 파일
- 참조 얼굴 이미지
- 처리 모드
  - `preserve`: 참조 인물 원본 유지
  - `character`: 참조 인물 캐릭터/이모지 대체
- 선택 캐릭터/이모지 asset

### 6.2 처리 단계

1. 업로드 파일 저장
   - 영상 파일을 작업 디렉터리에 저장한다.
   - 참조 이미지를 저장한다.
   - 파일 크기, 확장자, MIME type을 검사한다.
   - 허용하지 않는 파일은 처리하지 않고 사용자에게 오류를 반환한다.

2. 참조 얼굴 전처리
   - 참조 이미지에서 얼굴을 감지한다.
   - 얼굴이 없으면 오류를 반환한다.
   - 얼굴이 여러 명이면 가장 큰 얼굴을 사용하거나, 사용자에게 단일 얼굴 사진을 요구한다.
   - 참조 얼굴 crop을 얼굴 임베딩 벡터로 변환한다.

3. 영상 디코딩
   - OpenCV 또는 FFmpeg로 프레임을 순차적으로 읽는다.
   - 원본 FPS, 해상도, 프레임 수를 기록한다.

4. YOLO 감지
   - 얼굴 bounding box 감지
   - 번호판 bounding box 감지
   - confidence threshold를 적용한다.

5. 기본 tracking
   - 현재 프레임의 얼굴 box를 이전 프레임 track과 연결한다.
   - IoU, box 중심 거리, 크기 변화를 기준으로 같은 얼굴인지 판단한다.
   - track ID를 유지해 같은 사람의 여러 프레임 정보를 누적한다.

6. 얼굴 매칭
   - 감지된 각 얼굴 crop에서 임베딩을 추출한다.
   - 참조 임베딩과 cosine similarity를 계산한다.
   - 단일 프레임 결과만으로 바로 원본 유지하지 않는다.
   - track 단위로 similarity score를 누적한다.
   - 일정 프레임 이상 안정적으로 threshold를 넘을 때 참조 인물로 판단한다.
   - 애매하면 개인정보 보호를 우선해 blur 처리한다.

7. smoothing
   - 이전 프레임의 얼굴/번호판 위치와 현재 감지 결과를 매칭한다.
   - bounding box 위치를 부드럽게 보정한다.
   - 캐릭터 overlay가 튀지 않게 한다.
   - 짧은 detection miss가 발생하면 직전 track 위치를 제한된 프레임 동안 유지한다.

8. 렌더링 정책 적용
   - 참조 인물 + preserve 모드: 원본 유지
   - 참조 인물 + character 모드: 이모지/캐릭터 overlay
   - 참조 인물 아님: 얼굴 blur
   - 번호판: blur
   - 참조 인물 판정이 불확실하면 blur 처리한다.
   - overlay 실패 시 blur 처리로 fallback한다.

9. 결과 영상 인코딩
   - 처리된 프레임을 원본 FPS 기준으로 인코딩한다.
   - 오디오가 있으면 가능하면 원본 오디오를 다시 붙인다.
   - 다운로드 가능한 결과 파일을 생성한다.

## 7. 실시간 미리보기 파이프라인

### 7.1 기본 방향

실시간 기능은 저장 영상 처리와 같은 정책을 사용하되, 처리 속도를 위해 품질을 일부 낮춘다.

- 사용자가 참조 사진을 업로드하면 서버가 실시간 session을 만든다.
- session 생성 시 참조 얼굴 임베딩을 1회 계산해 캐시한다.
- 브라우저에서 카메라 프레임을 캡처한다.
- 프레임을 축소해서 WebSocket 또는 스트리밍 API로 서버에 전송한다.
- 서버가 YOLO 감지, 얼굴 매칭, blur/overlay를 수행한다.
- 처리된 프레임을 브라우저 canvas에 표시한다.
- 단순 MVP에서는 HTTP frame request로 시작할 수 있지만, 최종 실시간 preview는 WebSocket/session 방식을 우선한다.

### 7.2 실시간 최적화 정책

- 입력 프레임 해상도를 낮춘다.
- 모든 프레임을 처리하지 않고 일정 간격으로 처리할 수 있다.
- 감지되지 않은 프레임은 이전 tracking 결과를 짧게 유지할 수 있다.
- 저장 영상보다 blur/overlay 품질이 낮아도 허용한다.
- 참조 얼굴 임베딩은 프레임마다 다시 계산하지 않는다.
- 최근 track 상태를 session 단위로 유지해 깜빡임을 줄인다.
- 처리 지연이 커지면 최신 프레임만 처리하고 오래된 프레임은 버린다.

### 7.3 실시간 session 상태

실시간 preview는 다음 session 상태를 가진다.

- `session_id`
- 참조 얼굴 임베딩
- 선택 모드
- 선택 캐릭터/이모지
- 최근 얼굴 track 상태
- 최근 번호판 track 상태
- 마지막 처리 시각

session은 일정 시간 입력이 없으면 만료시키고 메모리에서 제거한다.

## 8. 웹 화면 계획

### 8.1 메인 업로드 화면

필수 UI:
- 영상 업로드 input
- 참조 사진 업로드 input
- 처리 모드 선택
  - 원본 유지
  - 캐릭터/이모지 대체
- 캐릭터/이모지 선택
- 처리 시작 버튼
- 처리 진행 상태
- 결과 영상 미리보기
- 결과 다운로드 버튼

### 8.2 실시간 미리보기 화면

필수 UI:
- 카메라 시작 버튼
- 참조 사진 업로드
- 모드 선택
- 실시간 preview canvas
- 처리 중 상태 표시

### 8.3 현재 제외 UI

- 로그인
- 회원가입
- 작업 히스토리
- 관리자 페이지
- 클라우드 저장소 연동

## 9. 권장 파일 구조

```text
backend/
  app/
    main.py
    api/
      routes_upload.py
      routes_jobs.py
      routes_realtime.py
    core/
      config.py
      paths.py
      security.py
    services/
      job_service.py
      queue_service.py
      video_service.py
      realtime_service.py
      cleanup_service.py
    vision/
      yolo_detector.py
      face_identity.py
      tracker.py
      renderer.py
      video_pipeline.py
    schemas/
      jobs.py
      processing.py
  tests/
    test_upload_validation.py
    test_policy.py
    test_renderer.py
    test_tracker.py
    test_video_pipeline.py

frontend/
  src/
    App.tsx
    api/
      client.ts
    components/
      UploadForm.tsx
      ModeSelector.tsx
      ResultViewer.tsx
      RealtimePreview.tsx
    pages/
      VideoPage.tsx
      RealtimePage.tsx
    styles/
      app.css

assets/
  characters/
    default_emoji.png

models/
  yolo/
  face/
  plate/

storage/
  uploads/
  outputs/
  temp/
```

## 10. 구현 단계

### Phase 0. 샘플과 시연 환경 확정

목표:
- 개발 중 품질 판단이 가능하도록 최소 샘플과 시연 환경을 정한다.

작업:
- 실제 테스트에 사용할 짧은 영상 2~3개 확보
- 참조 얼굴 사진 예시 확보
- 기본 캐릭터/이모지 asset 준비
- 최종 시연이 PC 웹 서비스인지, 임베디드 보드 실행인지 임시 결정
- 임베디드 보드가 이미 있다면 모델 실행 가능 조건 확인

완료 기준:
- 수동 QA에 사용할 샘플 영상과 참조 사진이 준비된다.
- 1차 개발/시연 실행 환경이 문서화된다.

### Phase 1. 프로젝트 뼈대 구성

목표:
- 웹 서비스 기본 구조를 만든다.
- 영상 업로드와 결과 다운로드 흐름을 먼저 만든다.
- 긴 영상 처리에 대비해 job lifecycle을 먼저 잡는다.

작업:
- backend API 서버 생성
- frontend 기본 화면 생성
- 업로드 파일 저장 경로 구성
- 업로드 파일 크기/확장자/MIME 검사
- 작업 ID 생성
- job 상태 모델 구성
  - `queued`
  - `processing`
  - `done`
  - `failed`
  - `cancelled`
- 결과 파일 다운로드 API 구성
- background worker 또는 간단한 queue service 구성
- 임시 파일 cleanup 정책 추가

완료 기준:
- 사용자가 영상 파일을 업로드할 수 있다.
- 서버가 작업 ID를 반환한다.
- 작업 상태를 조회할 수 있다.
- 더미 결과 파일을 다운로드할 수 있다.
- 실패한 작업이 `failed` 상태와 오류 메시지를 반환한다.

### Phase 2. YOLO 기반 전체 blur MVP

목표:
- 참조 인물 구분 없이 얼굴과 번호판을 감지하고 모두 blur한다.

작업:
- YOLO detector wrapper 작성
- 얼굴 감지 모델 연결
- 번호판 감지 모델 연결
- blur renderer 작성
- 프레임 처리 후 결과 영상 저장
- 결과 영상에 원본 오디오 재결합 가능성 확인

완료 기준:
- 업로드한 영상에서 감지된 얼굴이 blur된다.
- 감지된 번호판이 blur된다.
- 결과 영상이 재생 가능하다.
- 샘플 영상 기준 얼굴/번호판 처리율을 수동 QA 표에 기록한다.

### Phase 3. 참조 인물 원본 유지

목표:
- 참조 사진과 같은 사람은 blur하지 않고 유지한다.
- track 단위로 참조 인물 판별을 안정화한다.

작업:
- 참조 사진 얼굴 crop 추출
- 참조 얼굴 임베딩 생성
- 감지된 얼굴별 임베딩 비교
- similarity threshold 설정
- 기본 tracking 도입
- track별 similarity score 누적
- 일정 프레임 이상 안정적으로 threshold를 넘을 때만 참조 인물로 판단
- 참조 인물 유지, 나머지 얼굴 blur 정책 적용

완료 기준:
- 참조 사진 인물이 영상에서 대부분 원본 유지된다.
- 참조 인물이 아닌 사람은 blur된다.
- 참조 얼굴이 없는 이미지 입력 시 사용자에게 오류를 보여준다.
- 참조 인물인지 애매한 얼굴은 blur 처리된다.

### Phase 4. 캐릭터/이모지 대체 모드

목표:
- 참조 인물을 선택한 캐릭터/이모지로 대체한다.

작업:
- 캐릭터 asset 관리
- 얼굴 box 크기에 맞춘 overlay resizing
- 얼굴 위치 기준 overlay 배치
- alpha blending
- box padding 조정

완료 기준:
- 캐릭터 모드에서 참조 인물 얼굴 위치에 이모지가 붙는다.
- 다른 사람 얼굴은 계속 blur된다.
- 번호판도 계속 blur된다.

### Phase 5. tracking과 흔들림 고도화

목표:
- blur 영역과 캐릭터 overlay가 프레임마다 튀지 않게 한다.
- Phase 3의 기본 tracking을 품질 중심으로 개선한다.

작업:
- IoU 기반 frame-to-frame matching
- track ID 유지
- bounding box 이동 평균 smoothing
- detection miss가 짧게 발생해도 이전 위치를 잠깐 유지
- overlay jitter 조정
- track이 끊겼다가 다시 잡히는 경우의 재식별 정책 정리
- 번호판 blur 영역도 smoothing 적용 여부 검토

완료 기준:
- 캐릭터가 얼굴을 따라가며 눈에 띄게 흔들리지 않는다.
- blur 영역이 프레임마다 심하게 튀지 않는다.
- 짧은 detection miss에도 원본 얼굴이 갑자기 노출되지 않는다.

### Phase 6. 실시간 브라우저 카메라 미리보기

목표:
- 브라우저 카메라로 실시간 처리 결과를 보여준다.

작업:
- getUserMedia 기반 카메라 입력
- canvas frame capture
- 실시간 session 생성 API 구성
- 참조 얼굴 임베딩 session cache 구성
- WebSocket 또는 스트리밍 기반 프레임 전송 구성
- MVP 단계에서 필요하면 HTTP frame request fallback 제공
- 낮은 해상도 실시간 처리 경로 구성
- 최신 프레임 우선 처리와 오래된 프레임 drop 정책 적용
- 처리 결과를 canvas에 표시

완료 기준:
- 브라우저 카메라 영상이 화면에 보인다.
- 얼굴/번호판 blur가 미리보기로 동작한다.
- 참조 인물 preserve 또는 character 모드가 동작한다.
- session 만료와 cleanup이 동작한다.

### Phase 7. 품질 튜닝

목표:
- 합격 기준에 맞게 결과 품질을 끌어올린다.

작업:
- YOLO confidence threshold 조정
- blur padding 조정
- 얼굴 similarity threshold 조정
- 번호판 검출 누락 케이스 점검
- 먼 얼굴/반쪽 얼굴 허용 범위 정리
- sample video별 결과 비교

완료 기준:
- 테스트 영상에서 대부분의 얼굴과 번호판이 잘 처리된다.
- 참조 인물 보존/대체 결과가 안정적이다.
- 저장 영상 결과물이 보기 좋다.

### Phase 8. 임베디드 최적화 준비

목표:
- 웹 서비스 MVP 이후 임베디드 시스템으로 옮길 수 있는 준비를 한다.
- Phase 2 이후부터 하드웨어 제약을 병행 확인한다.

작업:
- 목표 하드웨어 후보 정리
- CPU/GPU/NPU 지원 여부 확인
- 모델 export 전략 수립
- 추론 속도 benchmark
- 해상도/FPS별 품질 비교
- 실시간 preview 경량화
- 웹 서버와 AI inference를 같은 보드에서 돌릴지, 보드는 카메라/전처리만 하고 서버가 inference할지 결정

완료 기준:
- 어떤 하드웨어에서 어느 정도 성능이 나오는지 측정할 수 있다.
- 모델 경량화 또는 하드웨어 가속 방향이 정해진다.
- 최종 시연 구조가 `PC 서버형`, `임베디드 단독형`, `임베디드+서버 분리형` 중 하나로 정리된다.

## 11. API 초안

### 11.1 영상 처리 작업 생성

```http
POST /api/jobs/video
Content-Type: multipart/form-data
```

입력:
- `video`: 업로드 영상
- `reference_image`: 참조 얼굴 사진
- `mode`: `preserve` 또는 `character`
- `character_id`: 캐릭터 모드일 때 선택 asset ID

응답:

```json
{
  "job_id": "job_001",
  "status": "queued",
  "status_url": "/api/jobs/job_001"
}
```

### 11.2 작업 상태 조회

```http
GET /api/jobs/{job_id}
```

응답:

```json
{
  "job_id": "job_001",
  "status": "processing",
  "progress": 42,
  "message": "Processing frame 420 / 1000",
  "error": null,
  "result_url": null
}
```

상태값:
- `queued`
- `processing`
- `done`
- `failed`
- `cancelled`

### 11.3 결과 다운로드

```http
GET /api/jobs/{job_id}/result
```

응답:
- 처리된 영상 파일

### 11.4 작업 취소

```http
POST /api/jobs/{job_id}/cancel
```

응답:

```json
{
  "job_id": "job_001",
  "status": "cancelled"
}
```

### 11.5 실시간 session 생성

```http
POST /api/realtime/sessions
Content-Type: multipart/form-data
```

입력:
- `reference_image`: 참조 얼굴 사진
- `mode`: `preserve` 또는 `character`
- `character_id`: 캐릭터 모드일 때 선택 asset ID

응답:

```json
{
  "session_id": "rt_001",
  "status": "ready",
  "websocket_url": "/api/realtime/sessions/rt_001/ws"
}
```

### 11.6 실시간 프레임 처리

기본 방향은 WebSocket/session 방식이다.

```http
WS /api/realtime/sessions/{session_id}/ws
```

메시지:
- client -> server: JPEG/PNG frame bytes 또는 base64 frame
- server -> client: 처리된 JPEG/PNG frame bytes 또는 base64 frame

MVP fallback으로 단순 HTTP frame request를 둘 수 있다.

```http
POST /api/realtime/frame
Content-Type: multipart/form-data
```

입력:
- `frame`: 브라우저 캡처 이미지
- `reference_image` 또는 `session_id`
- `mode`
- `character_id`

응답:
- 처리된 이미지 frame

### 11.7 업로드 제한

초기 기본값:
- 허용 영상 확장자: `mp4`, `mov`, `avi`, `mkv`
- 허용 이미지 확장자: `jpg`, `jpeg`, `png`, `webp`
- 파일 크기 제한: 개발 환경 기준으로 임시 상한을 둔다.
- 처리 완료 또는 실패 후 일정 시간이 지나면 업로드/임시 파일을 삭제한다.

## 12. 처리 정책 상세

### 12.1 얼굴 처리

| 조건 | preserve 모드 | character 모드 |
|---|---|---|
| 참조 인물로 판단됨 | 원본 유지 | 캐릭터/이모지 overlay |
| 참조 인물이 아님 | blur | blur |
| 유사도 애매함 | blur 우선 | blur 우선 |
| 얼굴 너무 작음 | 감지되면 blur, 미감지는 허용 | 감지되면 blur, 미감지는 허용 |

### 12.2 track 단위 참조 인물 판별

단일 프레임 similarity만으로 참조 인물 여부를 확정하지 않는다.

| 상태 | 의미 | 처리 |
|---|---|---|
| `unknown` | 새로 잡힌 얼굴 track | blur 우선 |
| `candidate_reference` | 일부 프레임에서 참조 인물과 유사함 | 누적 score 확인 전까지 blur |
| `reference` | 여러 프레임에서 안정적으로 threshold 통과 | preserve 또는 character 처리 |
| `non_reference` | 참조 인물과 유사하지 않음 | blur |
| `lost` | 잠시 감지 누락 | 짧은 시간만 이전 정책 유지, 길어지면 unknown |

기본 원칙:
- 참조 인물로 확정되기 전에는 blur한다.
- 참조 인물 track이라도 confidence가 급격히 낮아지면 blur로 되돌릴 수 있다.
- 다른 사람을 참조 인물로 잘못 보존하는 것보다 참조 인물을 잠깐 blur하는 쪽이 안전하다.
- 캐릭터 overlay는 `reference` 상태에서만 적용한다.

### 12.3 번호판 처리

| 조건 | 처리 |
|---|---|
| 번호판 감지됨 | blur |
| confidence 낮음 | threshold 이상이면 blur |
| 번호판 일부만 보임 | 감지되면 blur, 미감지는 허용 |

### 12.4 안전한 기본값

- 참조 인물인지 확실하지 않은 얼굴은 blur한다.
- 번호판으로 감지된 영역은 무조건 blur한다.
- 캐릭터 overlay가 실패하면 해당 얼굴은 blur 처리로 fallback한다.
- 참조 얼굴 사진에서 얼굴을 찾지 못하면 작업을 시작하지 않는다.
- 업로드 파일이 검증을 통과하지 못하면 저장하지 않거나 즉시 삭제한다.

## 13. 테스트 계획

### 13.1 수동 QA 영상 세트

테스트 영상은 최소 다음 케이스를 포함한다.

- 참조 인물 1명과 다른 사람 여러 명
- 차량 번호판이 보이는 영상
- 참조 인물이 정면으로 보이는 영상
- 참조 인물이 고개를 조금 돌린 영상
- 사람이 멀리 있는 영상
- 얼굴이 일부 잘린 영상
- 실내/실외 조명 차이가 있는 영상

각 영상마다 다음 표를 작성한다.

| 영상 | 가시 얼굴 수 | 얼굴 blur 성공 | 얼굴 누락 | 허용 누락 | 번호판 수 | 번호판 blur 성공 | 참조 인물 유지 | 캐릭터 흔들림 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| sample_01 |  |  |  |  |  |  |  |  |

### 13.2 단위 테스트

- bounding box padding 계산
- blur 영역이 이미지 범위를 벗어나지 않는지
- preserve/character/blur 정책 선택
- similarity threshold 판정
- smoothing 계산
- track 상태 전환
- 업로드 확장자/MIME/크기 검증
- session 만료 계산

### 13.3 통합 테스트

- 영상 업로드 API
- 작업 상태 조회 API
- 결과 다운로드 API
- 작업 실패 상태 반환
- 작업 취소 API
- 임시 파일 cleanup
- 샘플 영상 처리 후 결과 파일 생성
- 결과 영상 duration/frame count 확인
- 실시간 session 생성
- 실시간 frame 처리 응답

### 13.4 시각 검증

체크리스트:
- 참조 인물이 blur되지 않았는가
- 참조 인물이 아닌 사람은 blur됐는가
- 번호판이 blur됐는가
- 캐릭터 overlay가 얼굴 위치를 따라가는가
- overlay가 심하게 흔들리지 않는가
- 저장 영상 품질이 보기 좋은가

### 13.5 임베디드 준비 검증

- 목표 보드에서 Python/OpenCV/추론 runtime 실행 가능 여부 확인
- 샘플 모델 추론 benchmark
- 720p/480p 등 해상도별 처리 시간 비교
- 저장 영상 처리와 실시간 preview 중 어느 기능을 보드에서 직접 실행할지 결정

## 14. 주요 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| YOLO 얼굴 감지 누락 | 얼굴이 그대로 노출될 수 있음 | confidence/padding 튜닝, 샘플 영상 기반 모델 선택 |
| 번호판 감지 모델 품질 부족 | 번호판 블러 누락 | 번호판 특화 YOLO 모델 사용, 테스트 영상 추가 |
| 참조 인물 오인식 | 잘못된 사람을 원본 유지할 수 있음 | 유사도 threshold 보수적으로 설정, 애매하면 blur |
| 캐릭터 overlay 흔들림 | 결과 품질 저하 | tracking/smoothing 도입 |
| 실시간 처리 지연 | 미리보기 사용성 저하 | 해상도 축소, 프레임 샘플링, 서버 처리 단순화 |
| 임베디드 하드웨어 미정 | 최적화 방향 불명확 | MVP 이후 보드 확정 및 benchmark |
| 긴 영상 처리 timeout | 작업 실패 또는 서버 응답 지연 | background worker와 job 상태 조회 사용 |
| 업로드 파일 남음 | 저장소 낭비/개인정보 잔존 | 파일 크기 제한, 만료 cleanup, 실패 시 삭제 |
| 공개 모델 라이선스 문제 | 배포/발표 제약 | 모델 출처와 라이선스 기록 |

## 15. 품질 우선순위

우선순위는 다음 순서다.

1. 저장 영상에서 얼굴/번호판 블러가 잘 되는가
2. 참조 인물이 원본 유지되는가
3. 캐릭터 모드가 자연스럽게 동작하는가
4. 긴 영상 처리 job이 실패/진행/완료 상태를 안정적으로 관리하는가
5. 결과 영상이 다운로드 가능하고 재생되는가
6. 실시간 미리보기가 동작하는가
7. 처리 속도와 임베디드 최적화

## 16. 구현 전 확인해야 할 최소 항목

구현 시작 전에 반드시 정할 필요는 없지만, 품질 튜닝 단계에서는 필요하다.

- 테스트에 사용할 실제 샘플 영상
- 참조 사진 예시
- 사용할 기본 캐릭터/이모지 asset
- 목표 임베디드 보드
- 최종 발표/시연 환경
- 사용할 공개 모델 후보와 라이선스
- 업로드 파일 크기 상한
- 작업 결과 파일 보관 시간

## 17. 다음 실행 단위

가장 좋은 첫 작업은 Phase 1과 Phase 2를 묶어 "업로드 영상 전체 blur MVP"를 만드는 것이다.

첫 구현 목표:

- 웹에서 영상 업로드
- 업로드 파일 검증
- job 생성/상태 조회
- 서버에서 프레임 추출
- YOLO로 얼굴/번호판 감지
- 감지 영역 blur
- 결과 영상 저장
- 웹에서 결과 다운로드

이 단계가 성공하면 이후 참조 인물 보존, 캐릭터 모드, 실시간 preview를 순서대로 얹는다.
