/* ════ 페이지 전환 ════ */
function goPage(name) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.getElementById("page-" + name).classList.add("active");
  window.scrollTo(0, 0);
}
window.goPage = goPage;
 
/* ════ 공통 요소 ════ */
const langButtons = Array.from(document.querySelectorAll(".lang-button"));
const i18nElements = Array.from(document.querySelectorAll("[data-i18n]"));
let currentLang = "ko";
 
/* ════ 영상처리 요소 ════ */
const uploadForm = document.querySelector("#upload-form");
const submitButton = document.querySelector("#submit-button");
const videoInput = document.querySelector("#video-input");
const referenceInput = document.querySelector("#reference-input");
const emojiInput = document.querySelector("#emoji-input");
const videoFileNameEl = document.querySelector("#video-file-name");
const referenceFileNameEl = document.querySelector("#reference-file-name");
const emojiFileNameEl = document.querySelector("#emoji-file-name");
const videoCtrl = document.querySelector("#video-ctrl");
const referenceCtrl = document.querySelector("#reference-ctrl");
const emojiCtrl = document.querySelector("#emoji-ctrl");
const modeInputs = Array.from(document.querySelectorAll('input[name="mode"]'));
const selectedModeTitle = document.querySelector("#selected-mode-title");
const selectedModeCopy = document.querySelector("#selected-mode-copy");
const jobIdEl = document.querySelector("#job-id");
const jobStatusEl = document.querySelector("#job-status");
const jobProgressEl = document.querySelector("#job-progress");
const jobProgressBar = document.querySelector("#job-progress-bar");
const jobMessageEl = document.querySelector("#job-message");
const downloadLink = document.querySelector("#download-link");
const workflowSteps = Array.from(document.querySelectorAll(".workflow-step"));
const resultPreview = document.querySelector("#result-preview");
const resultVideo = document.querySelector("#result-video");
const resultOpenLink = document.querySelector("#result-open-link");
const showcaseCards = Array.from(document.querySelectorAll(".showcase-card"));
const showcaseImage = document.querySelector("#showcase-image");
const showcaseTitle = document.querySelector("#showcase-title");
 
/* ════ 실시간 요소 ════ */
const cameraButton = document.querySelector("#camera-button");
const sessionButton = document.querySelector("#session-button");
const sessionCreateButton = document.querySelector("#session-create-button");
const cameraVideo = document.querySelector("#camera-video");
const cameraCanvas = document.querySelector("#camera-canvas");
const realtimeMessage = document.querySelector("#realtime-message");
const cameraFrame = cameraVideo.closest(".media-frame");
const processedFrame = cameraCanvas.closest(".media-frame");
const rtReferenceInput = document.querySelector("#rt-reference-input");
const rtReferenceFileNameEl = document.querySelector("#rt-reference-file-name");
const rtReferenceCtrl = document.querySelector("#rt-reference-ctrl");
const rtEmojiInput = document.querySelector("#rt-emoji-input");
const rtEmojiFileNameEl = document.querySelector("#rt-emoji-file-name");
const rtEmojiCtrl = document.querySelector("#rt-emoji-ctrl");
const rtModeInputs = Array.from(document.querySelectorAll('input[name="rt-mode"]'));
const sessionStatusBadge = document.querySelector("#session-status-badge");
const sessionInfo = document.querySelector("#session-info");
const sessionInfoLabel = document.querySelector("#session-info-label");
const sessionInfoId = document.querySelector("#session-info-id");
 
/* ════ 상태 ════ */
let pollTimer = null;
let cameraStream = null;
let realtimeSessionId = null;
let realtimeTimer = null;
let realtimeBusy = false;
let submitBusy = false;
let lastJob = null;
 
/* ════ 번역 ════ */
const TRANSLATIONS = {
  ko: {
    brandSubtitle: "영상 익명화",
    serviceReady: "AI 처리 준비됨",
    backHome: "홈으로",
    heroEyebrow: "영상 개인정보 보호",
    heroTitle: "공유 가능한 영상으로 안전하게 변환하세요",
    heroLede: "얼굴과 번호판을 감지하고, 참조 인물은 유지하거나 스마일 이모지로 대체합니다.",
    metricDetection: "샘플 얼굴 감지",
    metricBlur: "평균 선명도 감소",
    metricLanguage: "언어 전환",
    showcaseBadge: "실제 샘플 결과",
    showcaseBlurTitle: "얼굴 블러 처리",
    showcasePreserveTitle: "참조 인물만 원본 유지",
    showcaseEmojiTitle: "참조 인물 스마일 이모지",
    showcaseBlur: "Blur",
    showcasePreserve: "Preserve",
    showcaseEmoji: "Emoji",
    featVideoTitle: "영상 처리",
    featVideoDesc: "MP4, MOV 등 영상 파일을 업로드하면 YOLO가 얼굴과 번호판을 감지하고 자동으로 블러 처리합니다. 참조 이미지 등록 시 해당 인물만 원본 유지 가능합니다.",
    featRtTitle: "실시간 스트리밍 처리",
    featRtDesc: "브라우저 카메라를 켜면 WebSocket으로 실시간 블러/이모지 처리 결과를 즉시 확인할 수 있습니다. 세션 생성 후 바로 시작 가능합니다.",
    featGo: "시작하기 →",
    savedVideo: "저장 영상",
    uploadTitle: "영상 익명화 작업",
    highQuality: "고품질 처리",
    videoFile: "처리할 영상",
    videoPlaceholder: "MP4, MOV, AVI, MKV",
    referenceFace: "유지할 얼굴",
    imagePlaceholder: "JPG, PNG, WEBP",
    emojiFile: "이모지 이미지",
    emojiPlaceholder: "PNG (투명 배경 권장)",
    emojiDefaultHint: "PNG — 기본 스마일 이모지 사용 중",
    emojiModeOnly: "이모지 모드",
    required: "필수",
    optional: "선택",
    choose: "선택",
    change: "변경",
    modeLegend: "처리 방식",
    preserveMode: "원본 유지",
    preserveModeHint: "참조 인물만 그대로 유지",
    characterMode: "이모지 대체",
    characterModeHint: "참조 인물 얼굴을 이모지로 교체",
    selectedPreserveTitle: "참조 인물 원본 유지",
    selectedPreserveCopy: "참조 사진과 일치한 인물만 원본으로 유지하고 나머지는 블러 처리합니다.",
    selectedCharacterTitle: "참조 인물 이모지 대체",
    selectedCharacterCopy: "참조 인물 얼굴 위치에 이모지를 원본 비율로 합성합니다. 이모지를 직접 업로드하거나 기본 스마일을 사용하세요.",
    startProcess: "처리 시작",
    processingButton: "처리 중...",
    uploading: "업로드 중...",
    uploadFailed: "업로드 실패",
    jobNumber: "작업 번호",
    status: "상태",
    progress: "진행률",
    initialJobMessage: "영상과 참조 얼굴을 선택하면 처리를 시작할 수 있습니다.",
    downloadResult: "결과 영상 받기",
    stepUpload: "업로드",
    stepDetect: "감지",
    stepRender: "렌더링",
    stepExport: "완료",
    resultEyebrow: "결과",
    resultTitle: "처리 영상 미리보기",
    resultBadge: "MP4",
    resultEmptyTitle: "결과가 여기에 표시됩니다",
    resultEmptyCopy: "처리가 완료되면 다운로드와 미리보기가 활성화됩니다.",
    openResult: "새 탭에서 열기",
    realtime: "실시간",
    realtimeTitle: "실시간 스트리밍 처리",
    wsBadge: "WebSocket",
    sessionConfig: "설정",
    sessionTitle: "세션 설정",
    aiReady: "AI 준비됨",
    sessionStatus: "세션 상태",
    noSession: "세션 생성 버튼을 눌러주세요",
    camera: "원본 카메라",
    processedPreview: "AI 처리 결과",
    cameraPlaceholderTitle: "카메라 대기 중",
    cameraPlaceholderCopy: "카메라 시작을 누르면 원본 화면이 표시됩니다.",
    processedPlaceholderTitle: "처리 결과 대기 중",
    processedPlaceholderCopy: "세션 생성 후 블러/이모지 결과가 표시됩니다.",
    createSession: "세션 생성",
    startCamera: "카메라 시작",
    stopCamera: "카메라 중지",
    initialRealtimeMessage: "참조 얼굴을 선택한 뒤 세션을 만들면 실시간 처리를 볼 수 있습니다.",
    cameraPreviewRunning: "카메라 미리보기가 실행 중입니다.",
    cameraStartFailed: "카메라 시작 실패",
    realtimeNeedsReference: "실시간 세션을 만들려면 참조 얼굴 사진을 먼저 선택하세요.",
    sessionFailed: "세션 생성 실패",
    realtimeSessionReady: "실시간 세션이 준비되었습니다.",
    statusFetchFailed: "상태 조회 실패",
    cameraStopped: "카메라가 중지되었습니다.",
    realtimeFrameFailed: "실시간 프레임 처리 실패",
    frameCaptureFailed: "프레임 캡처 실패",
    renderedFrameFailed: "처리된 프레임 표시 실패",
    statusIdle: "대기 중",
    statusQueued: "대기열",
    statusProcessing: "처리 중",
    statusDone: "완료",
    statusFailed: "실패",
    statusCancelled: "취소됨",
    sessionActive: "세션 활성",
  },
  en: {
    brandSubtitle: "Video anonymizer",
    serviceReady: "AI processing ready",
    backHome: "Home",
    heroEyebrow: "Video privacy protection",
    heroTitle: "Turn raw footage into safe-to-share video",
    heroLede: "Detect faces and license plates, then preserve the reference person or replace them with a smile emoji.",
    metricDetection: "detected faces",
    metricBlur: "sharpness reduced",
    metricLanguage: "language toggle",
    showcaseBadge: "Real sample result",
    showcaseBlurTitle: "Box-guided face blur",
    showcasePreserveTitle: "Only reference stays original",
    showcaseEmojiTitle: "Reference smile emoji",
    showcaseBlur: "Blur",
    showcasePreserve: "Preserve",
    showcaseEmoji: "Emoji",
    featVideoTitle: "Video Processing",
    featVideoDesc: "Upload MP4, MOV and more — YOLO detects faces and plates and blurs them automatically. Register a reference image to keep that person unblurred.",
    featRtTitle: "Realtime Streaming",
    featRtDesc: "Turn on your browser camera and see blur/emoji results instantly over WebSocket. Create a session and start right away.",
    featGo: "Get started →",
    savedVideo: "Saved video",
    uploadTitle: "Video anonymization",
    highQuality: "High quality",
    videoFile: "Video file",
    videoPlaceholder: "MP4, MOV, AVI, MKV",
    referenceFace: "Face to keep",
    imagePlaceholder: "JPG, PNG, WEBP",
    emojiFile: "Emoji image",
    emojiPlaceholder: "PNG (transparent background)",
    emojiDefaultHint: "PNG — default smile emoji in use",
    emojiModeOnly: "Emoji mode",
    required: "Required",
    optional: "Optional",
    choose: "Choose",
    change: "Change",
    modeLegend: "Processing mode",
    preserveMode: "Preserve original",
    preserveModeHint: "Keep only the reference person",
    characterMode: "Replace with emoji",
    characterModeHint: "Replace reference face with emoji",
    selectedPreserveTitle: "Preserve the reference person",
    selectedPreserveCopy: "Keep the matched reference person unchanged and blur everyone else.",
    selectedCharacterTitle: "Replace reference face with emoji",
    selectedCharacterCopy: "Attach an emoji at the reference face position. Upload your own or use the default smile.",
    startProcess: "Start processing",
    processingButton: "Processing...",
    uploading: "Uploading...",
    uploadFailed: "Upload failed",
    jobNumber: "Job number",
    status: "Status",
    progress: "Progress",
    initialJobMessage: "Select a video and reference face to start processing.",
    downloadResult: "Download result video",
    stepUpload: "Upload",
    stepDetect: "Detect",
    stepRender: "Render",
    stepExport: "Done",
    resultEyebrow: "Result",
    resultTitle: "Processed video preview",
    resultBadge: "MP4",
    resultEmptyTitle: "Your result appears here",
    resultEmptyCopy: "Preview and download become available when processing finishes.",
    openResult: "Open in new tab",
    realtime: "Realtime",
    realtimeTitle: "Realtime Streaming",
    wsBadge: "WebSocket",
    sessionConfig: "Settings",
    sessionTitle: "Session settings",
    aiReady: "AI ready",
    sessionStatus: "Session status",
    noSession: "Press Create Session to begin",
    camera: "Source camera",
    processedPreview: "AI processed",
    cameraPlaceholderTitle: "Camera idle",
    cameraPlaceholderCopy: "Press Start Camera to show the source feed.",
    processedPlaceholderTitle: "Waiting for processed frames",
    processedPlaceholderCopy: "Create a session to see blur or emoji output.",
    createSession: "Create session",
    startCamera: "Start camera",
    stopCamera: "Stop camera",
    initialRealtimeMessage: "Select a reference face, then create a session for realtime preview.",
    cameraPreviewRunning: "Camera preview is running.",
    cameraStartFailed: "Camera start failed",
    realtimeNeedsReference: "Select a reference face before creating a realtime session.",
    sessionFailed: "Session creation failed",
    realtimeSessionReady: "Realtime session is ready.",
    statusFetchFailed: "Failed to fetch job status",
    cameraStopped: "Camera stopped.",
    realtimeFrameFailed: "Realtime frame processing failed",
    frameCaptureFailed: "Frame capture failed",
    renderedFrameFailed: "Failed to display processed frame",
    statusIdle: "Idle",
    statusQueued: "Queued",
    statusProcessing: "Processing",
    statusDone: "Done",
    statusFailed: "Failed",
    statusCancelled: "Cancelled",
    sessionActive: "Session active",
  },
};
 
function t(key) {
  return TRANSLATIONS[currentLang]?.[key] ?? TRANSLATIONS.ko[key] ?? key;
}
 
/* ════ 언어 ════ */
langButtons.forEach((btn) => btn.addEventListener("click", () => applyLanguage(btn.dataset.lang || "ko")));
 
function applyLanguage(lang) {
  currentLang = lang === "en" ? "en" : "ko";
  document.documentElement.lang = currentLang === "ko" ? "ko" : "en";
  i18nElements.forEach((el) => { el.textContent = t(el.dataset.i18n); });
  langButtons.forEach((btn) => btn.classList.toggle("is-active", btn.dataset.lang === currentLang));
  updateFileName(videoInput, videoFileNameEl, "videoPlaceholder");
  updateFileName(referenceInput, referenceFileNameEl, "imagePlaceholder");
  updateFileName(emojiInput, emojiFileNameEl, "emojiPlaceholder");
  updateFileName(rtReferenceInput, rtReferenceFileNameEl, "imagePlaceholder");
  updateFileName(rtEmojiInput, rtEmojiFileNameEl, "emojiDefaultHint");
  setBusy(submitBusy);
  syncModeState();
  if (cameraStream) cameraButton.textContent = t("stopCamera");
  if (lastJob) renderJob(lastJob);
  else { jobStatusEl.textContent = t("statusIdle"); jobStatusEl.dataset.status = "idle"; }
}
 
/* ════ 쇼케이스 ════ */
showcaseCards.forEach((btn) => btn.addEventListener("click", () => setShowcase(btn)));
 
function setShowcase(button) {
  if (!button) return;
  showcaseImage.src = button.dataset.showcase;
  showcaseTitle.dataset.i18n = button.dataset.showcaseTitleKey || "showcaseBlurTitle";
  showcaseTitle.textContent = t(showcaseTitle.dataset.i18n);
  showcaseCards.forEach((card) => {
    const isActive = card === button;
    card.classList.toggle("is-active", isActive);
    card.setAttribute("aria-pressed", String(isActive));
  });
}
 
/* ════ 파일명 바인딩 ════ */
function bindFileName(input, label, placeholderKey, ctrl) {
  input.addEventListener("change", () => {
    const file = input.files[0];
    label.textContent = file ? file.name : t(placeholderKey);
    if (ctrl) ctrl.classList.toggle("has-file", Boolean(file));
  });
}
bindFileName(videoInput, videoFileNameEl, "videoPlaceholder", videoCtrl);
bindFileName(referenceInput, referenceFileNameEl, "imagePlaceholder", referenceCtrl);
bindFileName(emojiInput, emojiFileNameEl, "emojiPlaceholder", emojiCtrl);
bindFileName(rtReferenceInput, rtReferenceFileNameEl, "imagePlaceholder", rtReferenceCtrl);
bindFileName(rtEmojiInput, rtEmojiFileNameEl, "emojiPlaceholder", rtEmojiCtrl);
 
function updateFileName(input, label, placeholderKey) {
  const file = input.files[0];
  label.textContent = file ? file.name : t(placeholderKey);
}
 
/* ════ 영상처리 모드 ════ */
modeInputs.forEach((input) => input.addEventListener("change", syncModeState));
 
function syncModeState() {
  const isCharacter = getSelectedMode() === "character";
  // 이모지 업로드 칸 활성/비활성
  emojiCtrl.classList.toggle("file-control--disabled", !isCharacter);
  emojiCtrl.classList.toggle("is-active", isCharacter);
  emojiCtrl.setAttribute("aria-disabled", String(!isCharacter));
  emojiInput.disabled = !isCharacter;
  // 모드 미리보기 텍스트
  const titleKey = isCharacter ? "selectedCharacterTitle" : "selectedPreserveTitle";
  const copyKey = isCharacter ? "selectedCharacterCopy" : "selectedPreserveCopy";
  selectedModeTitle.dataset.i18n = titleKey;
  selectedModeCopy.dataset.i18n = copyKey;
  selectedModeTitle.textContent = t(titleKey);
  selectedModeCopy.textContent = t(copyKey);
  // 이모지 모드 해제 시 파일 초기화
  if (!isCharacter) {
    emojiInput.value = "";
    emojiFileNameEl.textContent = t("emojiPlaceholder");
    emojiCtrl.classList.remove("has-file");
  }
  // 쇼케이스 연동
  const showcaseName = isCharacter ? "character" : "preserve";
  setShowcase(showcaseCards.find((c) => c.dataset.showcase?.includes(showcaseName)));
}
 
function getSelectedMode() {
  return modeInputs.find((i) => i.checked)?.value ?? "preserve";
}
 
/* ════ 영상처리 제출 ════ */
uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearPoll();
  setBusy(true);
  setJobProgress(0);
  updateWorkflow(0, "queued");
  clearResultPreview();
  setMessage(t("uploading"), false);
  downloadLink.classList.add("hidden");
 
  const formData = new FormData(uploadForm);
  // 이모지 파일이 없으면 필드 제거 (빈 파일 전송 방지)
  if (!emojiInput.files[0]) formData.delete("emoji_image");
 
  try {
    const response = await fetch("/api/jobs/video", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("uploadFailed"));
    renderJob(payload);
    pollJob(payload.job_id);
  } catch (error) {
    setMessage(error.message, true);
    setBusy(false);
  }
});
 
/* ════ 폴링 ════ */
function pollJob(jobId) {
  pollTimer = window.setInterval(async () => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || t("statusFetchFailed"));
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
  jobIdEl.textContent = job.job_id || "-";
  jobStatusEl.textContent = statusLabel(status);
  jobStatusEl.dataset.status = status;
  setJobProgress(Number(job.progress || 0));
  updateWorkflow(Number(job.progress || 0), status);
  setMessage(job.error || job.message || "", job.status === "failed");
  if (job.result_url) {
    downloadLink.href = job.result_url;
    downloadLink.classList.remove("hidden");
    setResultPreview(job.result_url);
  }
}
 
function setMessage(message, isError) {
  jobMessageEl.textContent = message;
  jobMessageEl.classList.toggle("error", Boolean(isError));
}
function setJobProgress(progress) {
  const n = Math.max(0, Math.min(100, Number(progress) || 0));
  jobProgressEl.textContent = `${n}%`;
  jobProgressBar.style.width = `${n}%`;
}
function setBusy(isBusy) {
  submitBusy = isBusy;
  submitButton.disabled = isBusy;
  submitButton.textContent = isBusy ? t("processingButton") : t("startProcess");
}
function clearPoll() {
  if (pollTimer) { window.clearInterval(pollTimer); pollTimer = null; }
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
  const n = Math.max(0, Math.min(100, Number(progress) || 0));
  const activeIndex = status === "done" ? 3 : n >= 70 ? 2 : n >= 25 ? 1 : 0;
  workflowSteps.forEach((step, index) => {
    step.classList.toggle("is-complete", index < activeIndex || status === "done");
    step.classList.toggle("is-active", index === activeIndex && status !== "done");
  });
}
function statusLabel(status) {
  const key = `status${status.charAt(0).toUpperCase()}${status.slice(1)}`;
  return t(key) || status;
}
 
/* ════ 실시간 — 모드 ════ */
rtModeInputs.forEach((input) => input.addEventListener("change", syncRtModeState));
 
function syncRtModeState() {
  const isCharacter = rtModeInputs.find((i) => i.checked)?.value === "character";
  rtEmojiCtrl.classList.toggle("file-control--disabled", !isCharacter);
  rtEmojiCtrl.classList.toggle("is-active", isCharacter);
  rtEmojiCtrl.setAttribute("aria-disabled", String(!isCharacter));
  rtEmojiInput.disabled = !isCharacter;
  if (!isCharacter) {
    rtEmojiInput.value = "";
    rtEmojiFileNameEl.textContent = t("emojiDefaultHint");
    rtEmojiCtrl.classList.remove("has-file");
  }
}
 
/* ════ 실시간 — 세션 생성 ════ */
async function createRealtimeSession() {
  const reference = rtReferenceInput.files[0];
  if (!reference) {
    setRealtimeMessage(t("realtimeNeedsReference"), true);
    return;
  }
  const mode = rtModeInputs.find((i) => i.checked)?.value ?? "preserve";
  const formData = new FormData();
  formData.append("reference_image", reference);
  formData.append("mode", mode);
  formData.append("character_id", "default_emoji");
  if (rtEmojiInput.files[0]) formData.append("emoji_image", rtEmojiInput.files[0]);
 
  try {
    const response = await fetch("/api/realtime/sessions", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("sessionFailed"));
    realtimeSessionId = payload.session_id;
    setRealtimeMessage(`${t("realtimeSessionReady")} ${payload.session_id}`);
    // 세션 상태 UI 업데이트
    sessionInfo.classList.add("is-active");
    sessionInfoLabel.textContent = t("sessionActive");
    sessionInfoId.textContent = `session_id: ${payload.session_id}`;
    sessionStatusBadge.textContent = t("sessionActive");
    sessionStatusBadge.style.cssText = "background:var(--accent-soft);color:var(--accent-dark);border-color:rgba(12,124,114,.3);";
    startRealtimeLoop();
  } catch (error) {
    setRealtimeMessage(error.message, true);
  }
}
 
sessionButton.addEventListener("click", createRealtimeSession);
sessionCreateButton.addEventListener("click", createRealtimeSession);
 
/* ════ 실시간 — 카메라 ════ */
cameraButton.addEventListener("click", async () => {
  if (cameraStream) { stopCamera(); return; }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { width: 960, height: 540 }, audio: false });
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
 
function stopCamera() {
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
  if (!cameraStream) return;
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
  if (!cameraStream || !realtimeSessionId) return;
  realtimeTimer = window.setInterval(processRealtimeFrame, 350);
}
function stopRealtimeLoop() {
  if (realtimeTimer) { window.clearInterval(realtimeTimer); realtimeTimer = null; }
  realtimeBusy = false;
}
 
async function processRealtimeFrame() {
  if (!cameraStream || !realtimeSessionId || realtimeBusy) return;
  if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) return;
  realtimeBusy = true;
  try {
    const captureCanvas = document.createElement("canvas");
    const maxWidth = 640;
    const scale = Math.min(1, maxWidth / cameraVideo.videoWidth);
    captureCanvas.width = Math.max(1, Math.round(cameraVideo.videoWidth * scale));
    captureCanvas.height = Math.max(1, Math.round(cameraVideo.videoHeight * scale));
    captureCanvas.getContext("2d").drawImage(cameraVideo, 0, 0, captureCanvas.width, captureCanvas.height);
    const blob = await canvasToBlob(captureCanvas);
    const formData = new FormData();
    formData.append("session_id", realtimeSessionId);
    formData.append("frame", blob, "frame.jpg");
    const response = await fetch("/api/realtime/frame", { method: "POST", body: formData });
    if (!response.ok) {
      const p = await response.json().catch(() => ({}));
      throw new Error(p.detail || t("realtimeFrameFailed"));
    }
    await drawBlobToCanvas(await response.blob());
  } catch (error) {
    setRealtimeMessage(error.message, true);
  } finally {
    realtimeBusy = false;
  }
}
 
function setRealtimeMessage(message, isError = false) {
  realtimeMessage.textContent = message;
  realtimeMessage.classList.toggle("error", Boolean(isError));
}
 
/* ════ 유틸 ════ */
function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => { blob ? resolve(blob) : reject(new Error(t("frameCaptureFailed"))); }, "image/jpeg", 0.82);
  });
}
function drawBlobToCanvas(blob) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(blob);
    image.onload = () => {
      const ctx = cameraCanvas.getContext("2d");
      cameraCanvas.width = image.width;
      cameraCanvas.height = image.height;
      ctx.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);
      resolve();
    };
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error(t("renderedFrameFailed"))); };
    image.src = url;
  });
}
 
/* ════ 초기화 ════ */
syncModeState();
syncRtModeState();
applyLanguage("ko");
 