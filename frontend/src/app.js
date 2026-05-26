const uploadForm = document.querySelector("#upload-form");
const submitButton = document.querySelector("#submit-button");
const analyzeButton = document.querySelector("#analyze-button");
const videoInput = document.querySelector("#video-input");
const referenceInput = document.querySelector("#reference-input");
const realtimeReferenceInput = document.querySelector("#realtime-reference-input");
const videoFileNameEl = document.querySelector("#video-file-name");
const referenceFileNameEl = document.querySelector("#reference-file-name");
const realtimeReferenceFileNameEl = document.querySelector("#realtime-reference-file-name");
const referenceCountEls = {
  video: document.querySelector('[data-reference-count="video"]'),
  realtime: document.querySelector('[data-reference-count="realtime"]'),
};
const referenceGuides = {
  video: document.querySelector('[data-reference-guide="video"]'),
  realtime: document.querySelector('[data-reference-guide="realtime"]'),
};
const candidateGrid = document.querySelector("#candidate-grid");
const modeInputs = Array.from(document.querySelectorAll('input[name="mode"]'));
const realtimeModeInputs = Array.from(document.querySelectorAll('input[name="realtime_mode"]'));
const characterField = document.querySelector("#character-field");
const realtimeCharacterField = document.querySelector("#realtime-character-field");
const characterInput = document.querySelector("#character-input");
const realtimeCharacterInput = document.querySelector("#realtime-character-input");
const jobIdEl = document.querySelector("#job-id");
const jobStatusEl = document.querySelector("#job-status");
const jobProgressEl = document.querySelector("#job-progress");
const jobProgressBar = document.querySelector("#job-progress-bar");
const jobMessageEl = document.querySelector("#job-message");
const downloadLink = document.querySelector("#download-link");
const workflowSteps = Array.from(document.querySelectorAll(".workflow-step"));
const selectedModeTitle = document.querySelector("#selected-mode-title");
const selectedModeCopy = document.querySelector("#selected-mode-copy");
const showcaseImage = document.querySelector("#showcase-image");
const showcaseTitle = document.querySelector("#showcase-title");
const showcaseCards = Array.from(document.querySelectorAll(".showcase-card"));
const resultPreview = document.querySelector("#result-preview");
const resultVideo = document.querySelector("#result-video");
const resultOpenLink = document.querySelector("#result-open-link");

const cameraButton = document.querySelector("#camera-button");
const sessionButton = document.querySelector("#session-button");
const cameraVideo = document.querySelector("#camera-video");
const cameraCanvas = document.querySelector("#camera-canvas");
const realtimeMessage = document.querySelector("#realtime-message");
const cameraFrame = cameraVideo.closest(".media-frame");
const processedFrame = cameraCanvas.closest(".media-frame");
const allowModal = document.querySelector("#allow-modal");
const allowFaceImage = document.querySelector("#allow-face-image");
const allowAcceptButton = document.querySelector("#allow-accept-button");
const allowRejectButton = document.querySelector("#allow-reject-button");
const captureOpenButtons = Array.from(document.querySelectorAll("[data-capture-open]"));
const captureClearButtons = Array.from(document.querySelectorAll("[data-capture-clear]"));
const captureStripEls = {
  video: document.querySelector('[data-capture-strip="video"]'),
  realtime: document.querySelector('[data-capture-strip="realtime"]'),
};
const captureModal = document.querySelector("#capture-modal");
const captureCloseButton = document.querySelector("#capture-close-button");
const captureResetButton = document.querySelector("#capture-reset-button");
const captureShotButton = document.querySelector("#capture-shot-button");
const referenceCaptureVideo = document.querySelector("#reference-capture-video");
const referenceCaptureCanvas = document.querySelector("#reference-capture-canvas");
const captureProgressEl = document.querySelector("#capture-progress");
const captureStepTitle = document.querySelector("#capture-step-title");
const captureMessage = document.querySelector("#capture-message");
const langButtons = Array.from(document.querySelectorAll(".lang-button"));
const themeButtons = Array.from(document.querySelectorAll(".theme-button"));
const pageTabs = Array.from(document.querySelectorAll(".page-tab"));
const pageViews = Array.from(document.querySelectorAll(".page-view"));
const i18nElements = Array.from(document.querySelectorAll("[data-i18n]"));

let pollTimer = null;
let cameraStream = null;
let realtimeSessionId = null;
let realtimeTimer = null;
let realtimeBusy = false;
let submitBusy = false;
let analyzeBusy = false;
let currentLang = "ko";
let currentTheme = readStoredTheme();
let lastJob = null;
let candidateAnalysisId = null;
let videoCandidates = [];
let selectedCandidateIds = new Set();
let pendingRealtimeCandidate = null;
let activeCaptureScope = null;
let referenceCaptureStream = null;
const capturedReferenceFiles = {
  video: [],
  realtime: [],
};
const capturedReferenceUrls = {
  video: [],
  realtime: [],
};
const promptedRealtimeCandidateIds = new Set();
const CAPTURE_STEPS = [
  { key: "angleFront", slug: "front" },
  { key: "angleLeft45", slug: "left-45" },
  { key: "angleRight45", slug: "right-45" },
  { key: "angleLeftProfile", slug: "left-profile" },
  { key: "angleRightProfile", slug: "right-profile" },
];

const TRANSLATIONS = {
  ko: {
    brandSubtitle: "영상 프라이버시 데스크",
    serviceReady: "처리 파이프라인 준비",
    videoWorkspace: "영상 작업",
    realtimeWorkspace: "실시간",
    heroEyebrow: "공개 전 검토 콘솔",
    heroTitle: "영상 공개 전 민감 영역 검토",
    heroLede: "인물 후보를 먼저 확인하고, 허용한 얼굴만 유지한 뒤 결과 영상을 렌더링합니다.",
    metricDetection: "후보 검토",
    metricBlur: "블러 처리 대상",
    metricLanguage: "허용 목록",
    detectorMeta: "YOLO 얼굴 · 번호판 스캔",
    showcaseBadge: "처리 예시",
    showcaseBlurTitle: "얼굴 블러 처리",
    showcasePreserveTitle: "허용 인물만 원본 유지",
    showcaseEmojiTitle: "허용 인물 스마일 이모지",
    showcaseBlur: "Blur",
    showcasePreserve: "Preserve",
    showcaseEmoji: "Emoji",
    savedVideo: "비디오 작업",
    uploadTitle: "허용 인물 선택 후 익명화",
    highQuality: "렌더링 작업",
    videoFile: "처리할 영상",
    videoPlaceholder: "MP4, MOV, AVI, MKV",
    referenceFace: "추가 허용 얼굴",
    realtimeReferenceFace: "처음부터 허용할 얼굴",
    imagePlaceholder: "정면, 좌우 45도, 좌우 측면 5장 권장",
    optionalImagePlaceholder: "선택 사항, 5장 권장",
    filesSelected: "{count}개 파일",
    captureReference: "노트북 카메라로 촬영",
    clearCapturedReferences: "촬영 사진 초기화",
    referenceGuideTitle: "얼굴 등록 가이드",
    referenceGuideCopy: "정면에서 시작해 좌우로 천천히 돌린 사진 5장을 추가하세요.",
    referenceGuideStage: "얼굴을 중앙에 맞추세요",
    referenceGuideCount: "{count} / 5",
    referenceGuideReady: "{count}장 준비됨",
    angleFront: "정면",
    angleLeft45: "왼쪽 45도",
    angleRight45: "오른쪽 45도",
    angleLeftProfile: "왼쪽 측면",
    angleRightProfile: "오른쪽 측면",
    choose: "선택",
    candidateTitle: "영상 속 인물 후보",
    candidateCopy: "영상을 먼저 분석한 뒤, 블러에서 제외할 인물만 선택하세요.",
    analyzeFaces: "얼굴 후보 찾기",
    analyzingFaces: "분석 중...",
    candidateEmpty: "영상을 선택하고 얼굴 후보를 찾으면 여기에 표시됩니다.",
    candidateEmptyFound: "감지된 인물 후보가 없습니다. 필요하면 허용 얼굴을 직접 업로드하세요.",
    candidateAnalysisFailed: "얼굴 후보 분석 실패",
    noVideoForAnalysis: "먼저 처리할 영상을 선택하세요.",
    candidateSelected: "허용됨",
    candidateNotSelected: "블러 대상",
    modeLegend: "처리 방식",
    preserveMode: "원본 유지",
    preserveModeHint: "허용 인물만 그대로 유지",
    realtimePreserveHint: "허용 인물은 블러 해제",
    characterMode: "이모지 대체",
    characterModeHint: "허용 인물 얼굴에 스마일 이모지 적용",
    characterPreset: "이모지 프리셋",
    smileEmoji: "스마일 이모지",
    selectedPreserveTitle: "허용 인물 원본 유지",
    selectedPreserveCopy: "선택한 허용 인물만 원본으로 유지하고 나머지는 블러 처리합니다.",
    selectedCharacterTitle: "허용 인물 스마일 이모지 대체",
    selectedCharacterCopy: "선택한 허용 인물 얼굴 위치에 스마일 이모지를 원본 비율로 안정적으로 합성합니다.",
    startProcess: "블러 시작",
    processingButton: "처리 중...",
    uploading: "업로드 중...",
    uploadFailed: "업로드 실패",
    jobNumber: "작업 번호",
    status: "상태",
    progress: "진행률",
    initialJobMessage: "영상 분석 후 허용할 인물을 선택하면 처리를 시작할 수 있습니다.",
    downloadResult: "결과 영상 받기",
    stepUpload: "업로드",
    stepDetect: "인물 선택",
    stepRender: "렌더링",
    stepExport: "완료",
    resultEyebrow: "결과",
    resultTitle: "처리 영상 미리보기",
    resultBadge: "MP4",
    resultEmptyTitle: "결과가 여기에 표시됩니다",
    resultEmptyCopy: "처리가 완료되면 다운로드와 미리보기가 활성화됩니다.",
    openResult: "새 탭에서 열기",
    realtime: "라이브 미리보기",
    realtimeTitle: "실시간 허용 인물 관리",
    realtimeLede: "브라우저 카메라에서 감지된 얼굴을 즉시 처리하고, 반복 등장하는 인물은 허용 목록에 추가합니다.",
    realtimeSettingsTitle: "실시간 설정",
    browserCamera: "브라우저 카메라",
    camera: "카메라",
    processedPreview: "처리 결과",
    cameraPlaceholderTitle: "카메라 대기 중",
    cameraPlaceholderCopy: "권한을 허용하면 원본 화면이 표시됩니다.",
    processedPlaceholderTitle: "처리 결과 대기 중",
    processedPlaceholderCopy: "세션 생성 후 블러/이모지 결과가 표시됩니다.",
    createSession: "세션 생성",
    startCamera: "카메라 시작",
    stopCamera: "카메라 중지",
    initialRealtimeMessage: "세션을 만들면 블러 처리된 인물이 10초 이상 유지될 때 허용 여부를 물어봅니다.",
    cameraPreviewRunning: "카메라 미리보기가 실행 중입니다.",
    cameraStartFailed: "카메라 시작 실패",
    sessionFailed: "세션 생성 실패",
    realtimeSessionReady: "실시간 세션이 준비되었습니다.",
    realtimeCandidate: "실시간 후보",
    allowPersonTitle: "이 인물을 허용할까요?",
    allowPersonCopy: "허용하면 이후 프레임부터 이 얼굴은 블러 처리하지 않습니다.",
    allowPerson: "허용",
    keepBlurred: "계속 블러",
    allowPersonDone: "인물을 허용 목록에 추가했습니다.",
    allowPersonFailed: "인물 허용 실패",
    statusFetchFailed: "상태 조회 실패",
    cameraStopped: "카메라가 중지되었습니다.",
    realtimeFrameFailed: "실시간 프레임 처리 실패",
    frameCaptureFailed: "프레임 캡처 실패",
    renderedFrameFailed: "처리된 프레임 표시 실패",
    captureEyebrow: "허용 얼굴 촬영",
    captureTitle: "노트북 카메라로 얼굴 등록",
    captureCopy: "각도 단계에 맞춰 한 장씩 촬영하면 업로드 사진과 함께 전송됩니다.",
    captureClose: "닫기",
    captureStepCopy: "얼굴을 프레임 중앙에 두고 현재 각도에서 촬영하세요.",
    captureInitialMessage: "카메라 권한을 허용한 뒤 단계별로 촬영하세요.",
    captureCameraStarting: "카메라를 여는 중...",
    captureCameraFailed: "카메라를 열 수 없습니다",
    captureNotSupported: "이 브라우저는 카메라 촬영을 지원하지 않습니다.",
    captureButton: "{angle} 촬영",
    captureCompleteButton: "촬영 완료",
    captureDone: "5장 촬영이 준비되었습니다. 닫고 처리하면 업로드 사진과 함께 전송됩니다.",
    captureSaved: "{angle} 촬영 완료",
    capturedLabel: "촬영 {number}",
    removeCapturedReference: "삭제",
    statusIdle: "대기 중",
    statusQueued: "대기열",
    statusProcessing: "처리 중",
    statusDone: "완료",
    statusFailed: "실패",
    statusCancelled: "취소됨",
  },
  en: {
    brandSubtitle: "Privacy video desk",
    serviceReady: "Pipeline ready",
    videoWorkspace: "Video workspace",
    realtimeWorkspace: "Realtime",
    heroEyebrow: "Pre-publish console",
    heroTitle: "Review sensitive regions before footage leaves your desk",
    heroLede: "Confirm detected people, keep only approved faces visible, then render a clean export.",
    metricDetection: "review queue",
    metricBlur: "blur targets",
    metricLanguage: "allow list",
    detectorMeta: "YOLO face · plate scan",
    showcaseBadge: "Processing example",
    showcaseBlurTitle: "Face blur result",
    showcasePreserveTitle: "Only allowed people stay original",
    showcaseEmojiTitle: "Allowed people as smile emoji",
    showcaseBlur: "Blur",
    showcasePreserve: "Preserve",
    showcaseEmoji: "Emoji",
    savedVideo: "Video job",
    uploadTitle: "Select allowed people, then anonymize",
    highQuality: "Render job",
    videoFile: "Video file",
    videoPlaceholder: "MP4, MOV, AVI, MKV",
    referenceFace: "Additional allowed faces",
    realtimeReferenceFace: "Initially allowed faces",
    imagePlaceholder: "Front, 45-degree, and profile shots recommended",
    optionalImagePlaceholder: "Optional, 5 shots recommended",
    filesSelected: "{count} files",
    captureReference: "Use laptop camera",
    clearCapturedReferences: "Clear captured photos",
    referenceGuideTitle: "Face reference guide",
    referenceGuideCopy: "Start facing forward, then add five photos as the face turns left and right.",
    referenceGuideStage: "Center the face in the frame",
    referenceGuideCount: "{count} / 5",
    referenceGuideReady: "{count} ready",
    angleFront: "Front",
    angleLeft45: "Left 45",
    angleRight45: "Right 45",
    angleLeftProfile: "Left profile",
    angleRightProfile: "Right profile",
    choose: "Choose",
    candidateTitle: "People detected in the video",
    candidateCopy: "Analyze the video first, then select only the people to exclude from blur.",
    analyzeFaces: "Find face candidates",
    analyzingFaces: "Analyzing...",
    candidateEmpty: "Select a video and find face candidates to show them here.",
    candidateEmptyFound: "No face candidates were detected. Upload allowed faces manually if needed.",
    candidateAnalysisFailed: "Face candidate analysis failed",
    noVideoForAnalysis: "Select a video first.",
    candidateSelected: "Allowed",
    candidateNotSelected: "Blurred",
    modeLegend: "Processing mode",
    preserveMode: "Preserve original",
    preserveModeHint: "Keep only allowed people",
    realtimePreserveHint: "Unblur allowed people",
    characterMode: "Replace with emoji",
    characterModeHint: "Apply a smile emoji to allowed faces",
    characterPreset: "Emoji preset",
    smileEmoji: "Smile emoji",
    selectedPreserveTitle: "Preserve allowed people",
    selectedPreserveCopy: "Keep selected people unchanged and blur everyone else.",
    selectedCharacterTitle: "Replace allowed faces",
    selectedCharacterCopy: "Attach the smile emoji to selected faces without stretching the asset.",
    startProcess: "Start blur",
    processingButton: "Processing...",
    uploading: "Uploading...",
    uploadFailed: "Upload failed",
    jobNumber: "Job number",
    status: "Status",
    progress: "Progress",
    initialJobMessage: "Analyze a video and select allowed people to start processing.",
    downloadResult: "Download result video",
    stepUpload: "Upload",
    stepDetect: "Select people",
    stepRender: "Render",
    stepExport: "Done",
    resultEyebrow: "Result",
    resultTitle: "Processed video preview",
    resultBadge: "MP4",
    resultEmptyTitle: "Your result appears here",
    resultEmptyCopy: "Preview and download become available when processing finishes.",
    openResult: "Open in new tab",
    realtime: "Live preview",
    realtimeTitle: "Realtime allowed-person control",
    realtimeLede: "Process browser-camera faces immediately and add recurring people to the allow list.",
    realtimeSettingsTitle: "Realtime settings",
    browserCamera: "Browser camera",
    camera: "Camera",
    processedPreview: "Processed result",
    cameraPlaceholderTitle: "Camera idle",
    cameraPlaceholderCopy: "Allow camera access to show the source feed.",
    processedPlaceholderTitle: "Waiting for processed frames",
    processedPlaceholderCopy: "Create a session to see blur or emoji output.",
    createSession: "Create session",
    startCamera: "Start camera",
    stopCamera: "Stop camera",
    initialRealtimeMessage: "Create a session. When a blurred face stays visible for 10 seconds, you can allow it.",
    cameraPreviewRunning: "Camera preview is running.",
    cameraStartFailed: "Camera start failed",
    sessionFailed: "Session creation failed",
    realtimeSessionReady: "Realtime session is ready.",
    realtimeCandidate: "Realtime candidate",
    allowPersonTitle: "Allow this person?",
    allowPersonCopy: "If allowed, this face will stop being blurred in later frames.",
    allowPerson: "Allow",
    keepBlurred: "Keep blurred",
    allowPersonDone: "Added this person to the allowed list.",
    allowPersonFailed: "Failed to allow person",
    statusFetchFailed: "Failed to fetch job status",
    cameraStopped: "Camera stopped.",
    realtimeFrameFailed: "Realtime frame processing failed",
    frameCaptureFailed: "Frame capture failed",
    renderedFrameFailed: "Failed to display processed frame",
    captureEyebrow: "Allowed face capture",
    captureTitle: "Register a face with the laptop camera",
    captureCopy: "Capture each angle and the photos will be sent with uploaded reference images.",
    captureClose: "Close",
    captureStepCopy: "Keep the face centered in the frame, then capture the current angle.",
    captureInitialMessage: "Allow camera access, then capture each step.",
    captureCameraStarting: "Opening camera...",
    captureCameraFailed: "Could not open the camera",
    captureNotSupported: "This browser does not support camera capture.",
    captureButton: "Capture {angle}",
    captureCompleteButton: "Capture complete",
    captureDone: "Five captured photos are ready. Close and process to upload them with references.",
    captureSaved: "Captured {angle}",
    capturedLabel: "Shot {number}",
    removeCapturedReference: "Remove",
    statusIdle: "Idle",
    statusQueued: "Queued",
    statusProcessing: "Processing",
    statusDone: "Done",
    statusFailed: "Failed",
    statusCancelled: "Cancelled",
  },
};

pageTabs.forEach((button) => {
  button.addEventListener("click", () => setPage(button.dataset.page || "video"));
});
langButtons.forEach((button) => {
  button.addEventListener("click", () => applyLanguage(button.dataset.lang || "ko"));
});
themeButtons.forEach((button) => {
  button.addEventListener("click", () => applyTheme(button.dataset.themeOption || "light"));
});
showcaseCards.forEach((button) => {
  button.addEventListener("click", () => setShowcase(button));
});
bindFileName(videoInput, videoFileNameEl, "videoPlaceholder");
bindFileName(referenceInput, referenceFileNameEl, "imagePlaceholder");
bindFileName(realtimeReferenceInput, realtimeReferenceFileNameEl, "optionalImagePlaceholder");
videoInput.addEventListener("change", resetCandidateAnalysis);
modeInputs.forEach((input) => input.addEventListener("change", syncVideoModeState));
realtimeModeInputs.forEach((input) => input.addEventListener("change", syncRealtimeModeState));
analyzeButton.addEventListener("click", analyzeCandidates);
allowAcceptButton.addEventListener("click", allowRealtimeCandidate);
allowRejectButton.addEventListener("click", hideAllowModal);
captureOpenButtons.forEach((button) => {
  button.addEventListener("click", () => openReferenceCapture(button.dataset.captureOpen));
});
captureClearButtons.forEach((button) => {
  button.addEventListener("click", () => clearCapturedReferences(button.dataset.captureClear));
});
captureCloseButton.addEventListener("click", closeReferenceCapture);
captureResetButton.addEventListener("click", () => {
  if (activeCaptureScope) {
    clearCapturedReferences(activeCaptureScope);
  }
});
captureShotButton.addEventListener("click", captureReferencePhoto);
captureModal.addEventListener("click", (event) => {
  if (event.target === captureModal) {
    closeReferenceCapture();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !captureModal.classList.contains("hidden")) {
    closeReferenceCapture();
  }
});
syncVideoModeState();
syncRealtimeModeState();
renderCandidateEmpty("candidateEmpty");
applyTheme(currentTheme);
applyLanguage("ko");

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearPoll();
  setBusy(true);
  setJobProgress(0);
  updateWorkflow(0, "queued");
  clearResultPreview();
  setMessage(t("uploading"), false);
  downloadLink.classList.add("hidden");

  try {
    const request = buildVideoJobRequest();
    const response = await fetch(request.url, {
      method: "POST",
      body: request.formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || t("uploadFailed"));
    }
    renderJob(payload);
    pollJob(payload.job_id);
  } catch (error) {
    setMessage(error.message, true);
    setBusy(false);
  }
});

cameraButton.addEventListener("click", async () => {
  if (cameraStream) {
    stopCamera();
    return;
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 960, height: 540 },
      audio: false,
    });
    cameraVideo.srcObject = cameraStream;
    cameraFrame.classList.add("is-live");
    processedFrame.classList.add("is-live");
    cameraButton.textContent = t("stopCamera");
    setRealtimeMessage(t("cameraPreviewRunning"));
    drawCameraLoop();
    startRealtimeLoop();
  } catch (error) {
    setRealtimeMessage(`${t("cameraStartFailed")}: ${error.message}`, true);
  }
});

sessionButton.addEventListener("click", async () => {
  const formData = new FormData();
  appendFiles(formData, "reference_images", realtimeReferenceInput.files);
  appendFiles(formData, "reference_images", capturedReferenceFiles.realtime);
  formData.append("mode", getRealtimeMode());
  formData.append("character_id", realtimeCharacterInput.value);

  try {
    const response = await fetch("/api/realtime/sessions", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || t("sessionFailed"));
    }
    realtimeSessionId = payload.session_id;
    promptedRealtimeCandidateIds.clear();
    setRealtimeMessage(`${t("realtimeSessionReady")} ${payload.session_id}`);
    startRealtimeLoop();
  } catch (error) {
    setRealtimeMessage(error.message, true);
  }
});

async function analyzeCandidates() {
  const video = videoInput.files[0];
  if (!video) {
    setMessage(t("noVideoForAnalysis"), true);
    return;
  }

  setAnalyzeBusy(true);
  candidateAnalysisId = null;
  selectedCandidateIds = new Set();
  renderCandidateBusy();

  const formData = new FormData();
  formData.append("video", video);

  try {
    const response = await fetch("/api/jobs/video/candidates", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || t("candidateAnalysisFailed"));
    }
    candidateAnalysisId = payload.analysis_id;
    videoCandidates = Array.isArray(payload.candidates) ? payload.candidates : [];
    renderCandidateGrid();
    updateWorkflow(35, "processing");
  } catch (error) {
    renderCandidateEmpty("candidateEmpty");
    setMessage(error.message, true);
  } finally {
    setAnalyzeBusy(false);
  }
}

function buildVideoJobRequest() {
  const formData = new FormData();
  formData.append("mode", getVideoMode());
  formData.append("character_id", characterInput.value);
  appendFiles(formData, "reference_images", referenceInput.files);
  appendFiles(formData, "reference_images", capturedReferenceFiles.video);

  if (candidateAnalysisId) {
    formData.append("analysis_id", candidateAnalysisId);
    selectedCandidateIds.forEach((candidateId) => {
      formData.append("selected_candidate_ids", candidateId);
    });
    return { url: "/api/jobs/video/from-candidates", formData };
  }

  const video = videoInput.files[0];
  if (!video) {
    throw new Error(t("noVideoForAnalysis"));
  }
  formData.append("video", video);
  return { url: "/api/jobs/video", formData };
}

function appendFiles(formData, fieldName, files) {
  Array.from(files || []).forEach((file) => {
    formData.append(fieldName, file);
  });
}

function pollJob(jobId) {
  pollTimer = window.setInterval(async () => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || t("statusFetchFailed"));
      }
      renderJob(payload);
      if (["done", "failed", "cancelled"].includes(payload.status)) {
        clearPoll();
        setBusy(false);
      }
    } catch (error) {
      clearPoll();
      setMessage(error.message, true);
      setBusy(false);
    }
  }, 700);
}

function renderJob(job) {
  lastJob = job;
  const status = job.status || "idle";
  const progress = Number(job.progress || 0);
  jobIdEl.textContent = job.job_id || "-";
  jobStatusEl.textContent = statusLabel(status);
  jobStatusEl.dataset.status = status;
  setJobProgress(progress);
  updateWorkflow(progress, status);
  setMessage(job.error || job.message || "", job.status === "failed");
  if (job.result_url) {
    downloadLink.href = job.result_url;
    downloadLink.classList.remove("hidden");
    setResultPreview(job.result_url);
  }
}

function renderCandidateGrid() {
  candidateGrid.replaceChildren();
  if (!videoCandidates.length) {
    renderCandidateEmpty("candidateEmptyFound");
    return;
  }

  videoCandidates.forEach((candidate, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "candidate-card";
    button.dataset.candidateId = candidate.candidate_id;
    button.setAttribute("aria-pressed", "false");

    const image = document.createElement("img");
    image.src = candidate.image_url;
    image.alt = "";

    const title = document.createElement("span");
    title.textContent = `Face ${index + 1}`;

    const state = document.createElement("small");
    state.dataset.role = "state";
    state.textContent = t("candidateNotSelected");

    button.append(image, title, state);
    button.addEventListener("click", () => toggleCandidate(candidate.candidate_id));
    candidateGrid.append(button);
  });
  updateCandidateSelection();
}

function toggleCandidate(candidateId) {
  if (selectedCandidateIds.has(candidateId)) {
    selectedCandidateIds.delete(candidateId);
  } else {
    selectedCandidateIds.add(candidateId);
  }
  updateCandidateSelection();
}

function updateCandidateSelection() {
  Array.from(candidateGrid.querySelectorAll(".candidate-card")).forEach((button) => {
    const selected = selectedCandidateIds.has(button.dataset.candidateId);
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
    const state = button.querySelector('[data-role="state"]');
    if (state) {
      state.textContent = selected ? t("candidateSelected") : t("candidateNotSelected");
    }
  });
}

function renderCandidateBusy() {
  candidateGrid.replaceChildren();
  const empty = document.createElement("p");
  empty.className = "candidate-empty";
  empty.textContent = t("analyzingFaces");
  candidateGrid.append(empty);
}

function renderCandidateEmpty(key) {
  candidateGrid.replaceChildren();
  const empty = document.createElement("p");
  empty.id = "candidate-empty";
  empty.className = "candidate-empty";
  empty.textContent = t(key);
  candidateGrid.append(empty);
}

function resetCandidateAnalysis() {
  candidateAnalysisId = null;
  videoCandidates = [];
  selectedCandidateIds = new Set();
  renderCandidateEmpty("candidateEmpty");
}

function setMessage(message, isError) {
  jobMessageEl.textContent = message;
  jobMessageEl.classList.toggle("error", Boolean(isError));
}

function setJobProgress(progress) {
  const normalized = Math.max(0, Math.min(100, Number(progress) || 0));
  jobProgressEl.textContent = `${normalized}%`;
  jobProgressBar.style.width = `${normalized}%`;
}

function setBusy(isBusy) {
  submitBusy = isBusy;
  submitButton.disabled = isBusy;
  submitButton.textContent = isBusy ? t("processingButton") : t("startProcess");
}

function setAnalyzeBusy(isBusy) {
  analyzeBusy = isBusy;
  analyzeButton.disabled = isBusy;
  analyzeButton.textContent = isBusy ? t("analyzingFaces") : t("analyzeFaces");
}

function clearPoll() {
  if (pollTimer) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
}

function stopCamera() {
  if (!cameraStream) {
    return;
  }
  cameraStream.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  stopRealtimeLoop();
  cameraVideo.srcObject = null;
  cameraFrame.classList.remove("is-live");
  processedFrame.classList.remove("is-live");
  cameraButton.textContent = t("startCamera");
  setRealtimeMessage(t("cameraStopped"));
}

function drawCameraLoop() {
  if (!cameraStream) {
    return;
  }
  const context = cameraCanvas.getContext("2d");
  if (!realtimeSessionId) {
    cameraCanvas.width = cameraVideo.videoWidth || 960;
    cameraCanvas.height = cameraVideo.videoHeight || 540;
    context.drawImage(cameraVideo, 0, 0, cameraCanvas.width, cameraCanvas.height);
  }
  window.requestAnimationFrame(drawCameraLoop);
}

function startRealtimeLoop() {
  stopRealtimeLoop();
  if (!cameraStream || !realtimeSessionId) {
    return;
  }
  realtimeTimer = window.setInterval(processRealtimeFrame, 350);
}

function stopRealtimeLoop() {
  if (realtimeTimer) {
    window.clearInterval(realtimeTimer);
    realtimeTimer = null;
  }
  realtimeBusy = false;
}

async function processRealtimeFrame() {
  if (!cameraStream || !realtimeSessionId || realtimeBusy) {
    return;
  }
  if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) {
    return;
  }

  realtimeBusy = true;
  try {
    const captureCanvas = document.createElement("canvas");
    const maxWidth = 640;
    const scale = Math.min(1, maxWidth / cameraVideo.videoWidth);
    captureCanvas.width = Math.max(1, Math.round(cameraVideo.videoWidth * scale));
    captureCanvas.height = Math.max(1, Math.round(cameraVideo.videoHeight * scale));
    const captureContext = captureCanvas.getContext("2d");
    captureContext.drawImage(cameraVideo, 0, 0, captureCanvas.width, captureCanvas.height);
    const blob = await canvasToBlob(captureCanvas);

    const formData = new FormData();
    formData.append("session_id", realtimeSessionId);
    formData.append("frame", blob, "frame.jpg");

    const response = await fetch("/api/realtime/frame-meta", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || t("realtimeFrameFailed"));
    }
    await drawDataUrlToCanvas(payload.image);
    handleRealtimeCandidates(payload.candidates || []);
  } catch (error) {
    setRealtimeMessage(error.message, true);
  } finally {
    realtimeBusy = false;
  }
}

function handleRealtimeCandidates(candidates) {
  if (pendingRealtimeCandidate) {
    return;
  }
  const candidate = candidates.find((item) => !promptedRealtimeCandidateIds.has(item.candidate_id));
  if (!candidate) {
    return;
  }
  promptedRealtimeCandidateIds.add(candidate.candidate_id);
  pendingRealtimeCandidate = candidate;
  allowFaceImage.src = candidate.image;
  allowModal.classList.remove("hidden");
}

async function allowRealtimeCandidate() {
  if (!pendingRealtimeCandidate || !realtimeSessionId) {
    hideAllowModal();
    return;
  }

  const candidateId = pendingRealtimeCandidate.candidate_id;
  const formData = new FormData();
  formData.append("candidate_id", candidateId);

  try {
    const response = await fetch(`/api/realtime/sessions/${realtimeSessionId}/allow-face`, {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || t("allowPersonFailed"));
    }
    hideAllowModal();
    setRealtimeMessage(t("allowPersonDone"));
  } catch (error) {
    setRealtimeMessage(error.message, true);
  }
}

function hideAllowModal() {
  pendingRealtimeCandidate = null;
  allowFaceImage.removeAttribute("src");
  allowModal.classList.add("hidden");
}

function bindFileName(input, label, placeholderKey) {
  input.addEventListener("change", () => {
    updateFileName(input, label, placeholderKey);
  });
}

function updateFileName(input, label, placeholderKey) {
  const files = Array.from(input.files || []);
  const scope = scopeForReferenceInput(input);
  const capturedCount = scope ? capturedReferenceFiles[scope].length : 0;
  const totalCount = files.length + capturedCount;
  if (totalCount === 0) {
    label.textContent = t(placeholderKey);
  } else if (files.length === 1 && capturedCount === 0) {
    label.textContent = files[0].name;
  } else {
    label.textContent = t("filesSelected").replace("{count}", String(totalCount));
  }
  input.closest(".file-control").classList.toggle("has-file", totalCount > 0);
  if (scope) {
    syncReferenceGuideCount(scope, totalCount);
    renderCapturedReferences(scope);
  }
}

function scopeForReferenceInput(input) {
  if (input === referenceInput) {
    return "video";
  }
  if (input === realtimeReferenceInput) {
    return "realtime";
  }
  return null;
}

function referenceInputForScope(scope) {
  return scope === "video" ? referenceInput : realtimeReferenceInput;
}

function referenceLabelForScope(scope) {
  return scope === "video" ? referenceFileNameEl : realtimeReferenceFileNameEl;
}

function referencePlaceholderForScope(scope) {
  return scope === "video" ? "imagePlaceholder" : "optionalImagePlaceholder";
}

function getReferenceCount(scope) {
  const input = referenceInputForScope(scope);
  return Array.from(input.files || []).length + capturedReferenceFiles[scope].length;
}

function updateReferenceState(scope) {
  updateFileName(referenceInputForScope(scope), referenceLabelForScope(scope), referencePlaceholderForScope(scope));
}

function syncReferenceGuideCount(scope, count) {
  const target = referenceCountEls[scope];
  if (!target) {
    return;
  }
  const key = count >= 5 ? "referenceGuideReady" : "referenceGuideCount";
  target.dataset.i18n = key;
  target.textContent = t(key).replace("{count}", String(count));
  target.classList.toggle("is-ready", count >= 5);
  setReferenceGuideProgress(scope, count);
}

function setReferenceGuideProgress(scope, count) {
  const guide = referenceGuides[scope];
  if (!guide) {
    return;
  }
  const normalizedCount = Math.max(0, Math.min(5, Number(count) || 0));
  guide.classList.toggle("is-ready", normalizedCount >= 5);
  guide.querySelectorAll("[data-angle-step]").forEach((step) => {
    setGuideStepState(step, Number(step.dataset.angleStep), normalizedCount);
  });
  guide.querySelectorAll("[data-guide-dot]").forEach((dot) => {
    setGuideStepState(dot, Number(dot.dataset.guideDot), normalizedCount);
  });
}

function setGuideStepState(element, stepNumber, count) {
  const complete = count >= stepNumber;
  const next = count < 5 && stepNumber === count + 1;
  element.classList.toggle("is-complete", complete);
  element.classList.toggle("is-next", next);
}

function renderCapturedReferences(scope) {
  const strip = captureStripEls[scope];
  if (!strip) {
    return;
  }
  capturedReferenceUrls[scope].forEach((url) => URL.revokeObjectURL(url));
  capturedReferenceUrls[scope] = [];
  strip.replaceChildren();
  capturedReferenceFiles[scope].forEach((file, index) => {
    const wrapper = document.createElement("div");
    wrapper.className = "reference-thumb";

    const image = document.createElement("img");
    const url = URL.createObjectURL(file);
    capturedReferenceUrls[scope].push(url);
    image.src = url;
    image.alt = "";

    const label = document.createElement("span");
    label.textContent = t("capturedLabel").replace("{number}", String(index + 1));

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = t("removeCapturedReference");
    removeButton.setAttribute("aria-label", `${t("removeCapturedReference")} ${index + 1}`);
    removeButton.addEventListener("click", () => removeCapturedReference(scope, index));

    wrapper.append(image, removeButton, label);
    strip.append(wrapper);
  });
  const hasCapturedReferences = capturedReferenceFiles[scope].length > 0;
  strip.classList.toggle("hidden", !hasCapturedReferences);
  captureClearButtons.forEach((button) => {
    if (button.dataset.captureClear === scope) {
      button.classList.toggle("hidden", !hasCapturedReferences);
    }
  });
}

function removeCapturedReference(scope, index) {
  capturedReferenceFiles[scope].splice(index, 1);
  updateReferenceState(scope);
  updateCaptureModal();
}

function clearCapturedReferences(scope) {
  if (!scope) {
    return;
  }
  capturedReferenceFiles[scope] = [];
  updateReferenceState(scope);
  setCaptureMessage(t("captureInitialMessage"));
  updateCaptureModal();
}

async function openReferenceCapture(scope) {
  if (!["video", "realtime"].includes(scope)) {
    return;
  }
  activeCaptureScope = scope;
  captureModal.classList.remove("hidden");
  setCaptureMessage(t("captureCameraStarting"));
  updateCaptureModal();

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setCaptureMessage(t("captureNotSupported"), true);
    updateCaptureModal();
    return;
  }

  stopReferenceCaptureStream();
  try {
    referenceCaptureStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 960, height: 720, facingMode: "user" },
      audio: false,
    });
    referenceCaptureVideo.srcObject = referenceCaptureStream;
    await referenceCaptureVideo.play();
    setCaptureMessage(t("captureInitialMessage"));
  } catch (error) {
    referenceCaptureStream = null;
    referenceCaptureVideo.removeAttribute("src");
    setCaptureMessage(`${t("captureCameraFailed")}: ${error.message}`, true);
  } finally {
    updateCaptureModal();
  }
}

function closeReferenceCapture() {
  stopReferenceCaptureStream();
  activeCaptureScope = null;
  captureModal.classList.add("hidden");
}

function stopReferenceCaptureStream() {
  if (!referenceCaptureStream) {
    return;
  }
  referenceCaptureStream.getTracks().forEach((track) => track.stop());
  referenceCaptureStream = null;
  referenceCaptureVideo.srcObject = null;
}

async function captureReferencePhoto() {
  const scope = activeCaptureScope;
  if (!scope || !referenceCaptureStream) {
    return;
  }
  const currentCount = getReferenceCount(scope);
  if (currentCount >= CAPTURE_STEPS.length) {
    setCaptureMessage(t("captureDone"));
    updateCaptureModal();
    return;
  }

  const step = CAPTURE_STEPS[currentCount];
  const width = referenceCaptureVideo.videoWidth || 960;
  const height = referenceCaptureVideo.videoHeight || 720;
  if (!width || !height) {
    setCaptureMessage(t("frameCaptureFailed"), true);
    return;
  }

  const maxWidth = 960;
  const scale = Math.min(1, maxWidth / width);
  try {
    captureShotButton.disabled = true;
    referenceCaptureCanvas.width = Math.max(1, Math.round(width * scale));
    referenceCaptureCanvas.height = Math.max(1, Math.round(height * scale));
    const context = referenceCaptureCanvas.getContext("2d");
    context.drawImage(referenceCaptureVideo, 0, 0, referenceCaptureCanvas.width, referenceCaptureCanvas.height);
    const blob = await canvasToBlob(referenceCaptureCanvas);
    const file = new File([blob], `deepdetect-reference-${scope}-${step.slug}.jpg`, {
      type: "image/jpeg",
      lastModified: Date.now(),
    });
    capturedReferenceFiles[scope].push(file);
    updateReferenceState(scope);
    setCaptureMessage(t("captureSaved").replace("{angle}", t(step.key)));
  } catch (error) {
    setCaptureMessage(error.message, true);
  } finally {
    updateCaptureModal();
  }
}

function updateCaptureModal() {
  const scope = activeCaptureScope;
  if (!scope) {
    return;
  }
  const count = getReferenceCount(scope);
  const normalizedCount = Math.max(0, Math.min(CAPTURE_STEPS.length, count));
  const nextStepIndex = Math.min(normalizedCount, CAPTURE_STEPS.length - 1);
  const nextStep = CAPTURE_STEPS[nextStepIndex];

  captureProgressEl.textContent =
    count >= CAPTURE_STEPS.length
      ? t("referenceGuideReady").replace("{count}", String(count))
      : t("referenceGuideCount").replace("{count}", String(count));
  captureProgressEl.classList.toggle("is-ready", count >= CAPTURE_STEPS.length);
  captureStepTitle.textContent = t(nextStep.key);
  captureShotButton.textContent =
    count >= CAPTURE_STEPS.length ? t("captureCompleteButton") : t("captureButton").replace("{angle}", t(nextStep.key));
  captureShotButton.disabled = !referenceCaptureStream || count >= CAPTURE_STEPS.length;
  captureResetButton.disabled = capturedReferenceFiles[scope].length === 0;
  if (count >= CAPTURE_STEPS.length) {
    setCaptureMessage(t("captureDone"));
  }

  captureModal.querySelectorAll("[data-capture-step]").forEach((step) => {
    setGuideStepState(step, Number(step.dataset.captureStep), normalizedCount);
  });
}

function setCaptureMessage(message, isError = false) {
  captureMessage.textContent = message;
  captureMessage.classList.toggle("error", Boolean(isError));
}

function getVideoMode() {
  return getSelectedValue(modeInputs, "preserve");
}

function getRealtimeMode() {
  return getSelectedValue(realtimeModeInputs, "preserve");
}

function getSelectedValue(inputs, fallback) {
  const selectedInput = inputs.find((input) => input.checked);
  return selectedInput ? selectedInput.value : fallback;
}

function syncVideoModeState() {
  const isCharacterMode = getVideoMode() === "character";
  characterField.classList.toggle("is-muted", !isCharacterMode);
  characterField.setAttribute("aria-disabled", String(!isCharacterMode));
  characterInput.disabled = !isCharacterMode;
  const titleKey = isCharacterMode ? "selectedCharacterTitle" : "selectedPreserveTitle";
  const copyKey = isCharacterMode ? "selectedCharacterCopy" : "selectedPreserveCopy";
  selectedModeTitle.dataset.i18n = titleKey;
  selectedModeCopy.dataset.i18n = copyKey;
  selectedModeTitle.textContent = t(titleKey);
  selectedModeCopy.textContent = t(copyKey);
  const showcaseName = isCharacterMode ? "character" : "preserve";
  setShowcase(showcaseCards.find((card) => card.dataset.showcase.includes(showcaseName)));
}

function syncRealtimeModeState() {
  const isCharacterMode = getRealtimeMode() === "character";
  realtimeCharacterField.classList.toggle("is-muted", !isCharacterMode);
  realtimeCharacterField.setAttribute("aria-disabled", String(!isCharacterMode));
  realtimeCharacterInput.disabled = !isCharacterMode;
}

function setRealtimeMessage(message, isError = false) {
  realtimeMessage.textContent = message;
  realtimeMessage.classList.toggle("error", Boolean(isError));
}

function setPage(page) {
  pageTabs.forEach((tab) => {
    const active = tab.dataset.page === page;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-pressed", String(active));
  });
  pageViews.forEach((view) => {
    view.classList.toggle("is-active", view.id === `${page}-page`);
  });
}

function applyLanguage(lang) {
  currentLang = lang === "en" ? "en" : "ko";
  document.documentElement.lang = currentLang === "ko" ? "ko" : "en";
  document.title = "deepdetect";
  i18nElements.forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  updateFileName(videoInput, videoFileNameEl, "videoPlaceholder");
  updateFileName(referenceInput, referenceFileNameEl, "imagePlaceholder");
  updateFileName(realtimeReferenceInput, realtimeReferenceFileNameEl, "optionalImagePlaceholder");
  langButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.lang === currentLang);
  });
  syncVideoModeState();
  syncRealtimeModeState();
  setBusy(submitBusy);
  setAnalyzeBusy(analyzeBusy);
  if (cameraStream) {
    cameraButton.textContent = t("stopCamera");
  }
  if (videoCandidates.length) {
    renderCandidateGrid();
  } else if (!analyzeBusy) {
    renderCandidateEmpty(candidateAnalysisId ? "candidateEmptyFound" : "candidateEmpty");
  }
  if (lastJob) {
    renderJob(lastJob);
  } else {
    jobStatusEl.textContent = t("statusIdle");
    jobStatusEl.dataset.status = "idle";
  }
  renderCapturedReferences("video");
  renderCapturedReferences("realtime");
  updateCaptureModal();
}

function applyTheme(theme) {
  currentTheme = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = currentTheme;
  themeButtons.forEach((button) => {
    const active = button.dataset.themeOption === currentTheme;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  try {
    window.localStorage.setItem("deepdetect-theme", currentTheme);
  } catch {
    return;
  }
}

function readStoredTheme() {
  try {
    return window.localStorage.getItem("deepdetect-theme") || "light";
  } catch {
    return "light";
  }
}

function setShowcase(button) {
  if (!button) {
    return;
  }
  showcaseImage.src = button.dataset.showcase;
  showcaseTitle.dataset.i18n = button.dataset.showcaseTitleKey || "showcaseBlurTitle";
  showcaseTitle.textContent = t(showcaseTitle.dataset.i18n);
  showcaseCards.forEach((card) => {
    const isActive = card === button;
    card.classList.toggle("is-active", isActive);
    card.setAttribute("aria-pressed", String(isActive));
  });
}

function setResultPreview(url) {
  resultVideo.src = url;
  resultPreview.classList.add("has-result");
  resultOpenLink.href = url;
  resultOpenLink.classList.remove("hidden");
}

function clearResultPreview() {
  resultVideo.removeAttribute("src");
  resultVideo.load();
  resultPreview.classList.remove("has-result");
  resultOpenLink.classList.add("hidden");
  resultOpenLink.href = "#";
}

function updateWorkflow(progress, status) {
  const normalized = Math.max(0, Math.min(100, Number(progress) || 0));
  const activeIndex =
    status === "done"
      ? 3
      : normalized >= 70
        ? 2
        : normalized >= 25
          ? 1
          : 0;
  workflowSteps.forEach((step, index) => {
    step.classList.toggle("is-complete", index < activeIndex || status === "done");
    step.classList.toggle("is-active", index === activeIndex && status !== "done");
  });
}

function t(key) {
  return TRANSLATIONS[currentLang][key] || TRANSLATIONS.ko[key] || key;
}

function statusLabel(status) {
  const key = `status${status.charAt(0).toUpperCase()}${status.slice(1)}`;
  return t(key) || status;
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob);
          return;
        }
        reject(new Error(t("frameCaptureFailed")));
      },
      "image/jpeg",
      0.82,
    );
  });
}

function drawDataUrlToCanvas(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const context = cameraCanvas.getContext("2d");
      cameraCanvas.width = image.width;
      cameraCanvas.height = image.height;
      context.drawImage(image, 0, 0);
      resolve();
    };
    image.onerror = () => reject(new Error(t("renderedFrameFailed")));
    image.src = dataUrl;
  });
}
