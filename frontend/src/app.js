const uploadForm = document.querySelector("#upload-form");
const submitButton = document.querySelector("#submit-button");
const videoInput = document.querySelector("#video-input");
const referenceInput = document.querySelector("#reference-input");
const videoFileNameEl = document.querySelector("#video-file-name");
const referenceFileNameEl = document.querySelector("#reference-file-name");
const modeInputs = Array.from(document.querySelectorAll('input[name="mode"]'));
const characterField = document.querySelector("#character-field");
const characterInput = document.querySelector("#character-input");
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
const langButtons = Array.from(document.querySelectorAll(".lang-button"));
const i18nElements = Array.from(document.querySelectorAll("[data-i18n]"));

let pollTimer = null;
let cameraStream = null;
let realtimeSessionId = null;
let realtimeTimer = null;
let realtimeBusy = false;
let submitBusy = false;
let currentLang = "ko";
let lastJob = null;

const TRANSLATIONS = {
  ko: {
    brandSubtitle: "영상 익명화",
    serviceReady: "AI 처리 준비됨",
    heroEyebrow: "영상 개인정보 보호",
    heroTitle: "공유 가능한 영상으로 안전하게 변환하세요",
    heroLede: "얼굴과 번호판을 감지하고, 참조 인물은 유지하거나 프라이버시 마스크로 대체합니다.",
    metricDetection: "감지된 얼굴",
    metricBlur: "블러 처리 대상",
    metricLanguage: "참조 인물 유지",
    showcaseBadge: "YOLO 스타일 After",
    showcaseBlurTitle: "감지 박스 기반 얼굴 블러",
    showcasePreserveTitle: "참조 인물만 원본 유지",
    showcaseMaskTitle: "참조 인물 프라이버시 마스크",
    showcaseBlur: "Blur",
    showcasePreserve: "Keep 1",
    showcaseMask: "Mask",
    savedVideo: "저장 영상",
    uploadTitle: "영상 익명화 작업",
    highQuality: "고품질 처리",
    videoFile: "처리할 영상",
    videoPlaceholder: "MP4, MOV, AVI, MKV",
    referenceFace: "유지할 얼굴",
    imagePlaceholder: "JPG, PNG, WEBP",
    choose: "선택",
    modeLegend: "처리 방식",
    preserveMode: "원본 유지",
    preserveModeHint: "참조 인물만 그대로 유지",
    characterMode: "마스크 대체",
    characterModeHint: "참조 인물 얼굴에 프라이버시 마스크 적용",
    characterPreset: "마스크 프리셋",
    privacyMask: "deepdetect 마스크",
    selectedPreserveTitle: "참조 인물 원본 유지",
    selectedPreserveCopy: "참조 사진과 일치한 인물만 원본으로 유지하고 나머지는 블러 처리합니다.",
    selectedCharacterTitle: "참조 인물 프라이버시 마스크",
    selectedCharacterCopy: "참조 인물 얼굴 위치에 deepdetect 마스크를 안정적으로 합성합니다.",
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
    realtimeTitle: "실시간 미리보기",
    browserCamera: "브라우저 카메라",
    camera: "카메라",
    processedPreview: "처리 결과",
    cameraPlaceholderTitle: "카메라 대기 중",
    cameraPlaceholderCopy: "권한을 허용하면 원본 화면이 표시됩니다.",
    processedPlaceholderTitle: "처리 결과 대기 중",
    processedPlaceholderCopy: "세션 생성 후 블러/마스크 결과가 표시됩니다.",
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
  },
  en: {
    brandSubtitle: "Video anonymizer",
    serviceReady: "AI processing ready",
    heroEyebrow: "Video privacy protection",
    heroTitle: "Turn raw footage into safe-to-share video",
    heroLede: "Detect faces and license plates, then preserve the reference person or replace them with a privacy mask.",
    metricDetection: "detected faces",
    metricBlur: "faces anonymized",
    metricLanguage: "reference kept",
    showcaseBadge: "YOLO-style after",
    showcaseBlurTitle: "Box-guided face blur",
    showcasePreserveTitle: "Only the reference stays original",
    showcaseMaskTitle: "Reference privacy mask",
    showcaseBlur: "Blur",
    showcasePreserve: "Keep 1",
    showcaseMask: "Mask",
    savedVideo: "Saved video",
    uploadTitle: "Video anonymization",
    highQuality: "High quality",
    videoFile: "Video file",
    videoPlaceholder: "MP4, MOV, AVI, MKV",
    referenceFace: "Face to keep",
    imagePlaceholder: "JPG, PNG, WEBP",
    choose: "Choose",
    modeLegend: "Processing mode",
    preserveMode: "Preserve original",
    preserveModeHint: "Keep only the reference person",
    characterMode: "Replace with mask",
    characterModeHint: "Apply a privacy mask to the reference face",
    characterPreset: "Mask preset",
    privacyMask: "deepdetect mask",
    selectedPreserveTitle: "Preserve the reference person",
    selectedPreserveCopy: "Keep the matched reference person unchanged and blur everyone else.",
    selectedCharacterTitle: "Mask the reference person",
    selectedCharacterCopy: "Attach the deepdetect mask at the reference face position without stretching the asset.",
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
    realtimeTitle: "Realtime preview",
    browserCamera: "Browser camera",
    camera: "Camera",
    processedPreview: "Processed result",
    cameraPlaceholderTitle: "Camera idle",
    cameraPlaceholderCopy: "Allow camera access to show the source feed.",
    processedPlaceholderTitle: "Waiting for processed frames",
    processedPlaceholderCopy: "Create a session to see blur or mask output.",
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
  },
};

langButtons.forEach((button) => {
  button.addEventListener("click", () => applyLanguage(button.dataset.lang || "ko"));
});
showcaseCards.forEach((button) => {
  button.addEventListener("click", () => setShowcase(button));
});
bindFileName(videoInput, videoFileNameEl, "videoPlaceholder");
bindFileName(referenceInput, referenceFileNameEl, "imagePlaceholder");
modeInputs.forEach((input) => input.addEventListener("change", syncModeState));
syncModeState();
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

  const formData = new FormData(uploadForm);

  try {
    const response = await fetch("/api/jobs/video", {
      method: "POST",
      body: formData,
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
  const reference = referenceInput.files[0];
  if (!reference) {
    setRealtimeMessage(t("realtimeNeedsReference"), true);
    return;
  }

  const formData = new FormData();
  formData.append("reference_image", reference);
  formData.append("mode", getSelectedMode());
  formData.append("character_id", characterInput.value);

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
    setRealtimeMessage(`${t("realtimeSessionReady")} ${payload.session_id}`);
    startRealtimeLoop();
  } catch (error) {
    setRealtimeMessage(error.message, true);
  }
});

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

function clearPoll() {
  if (pollTimer) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
}

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

    const response = await fetch("/api/realtime/frame", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || t("realtimeFrameFailed"));
    }
    const renderedBlob = await response.blob();
    await drawBlobToCanvas(renderedBlob);
  } catch (error) {
    setRealtimeMessage(error.message, true);
  } finally {
    realtimeBusy = false;
  }
}

function bindFileName(input, label, placeholderKey) {
  input.addEventListener("change", () => {
    updateFileName(input, label, placeholderKey);
  });
}

function updateFileName(input, label, placeholderKey) {
  const file = input.files[0];
  label.textContent = file ? file.name : t(placeholderKey);
  input.closest(".file-control").classList.toggle("has-file", Boolean(file));
}

function getSelectedMode() {
  const selectedInput = modeInputs.find((input) => input.checked);
  return selectedInput ? selectedInput.value : "preserve";
}

function syncModeState() {
  const isCharacterMode = getSelectedMode() === "character";
  characterField.classList.toggle("is-muted", !isCharacterMode);
  const titleKey = isCharacterMode ? "selectedCharacterTitle" : "selectedPreserveTitle";
  const copyKey = isCharacterMode ? "selectedCharacterCopy" : "selectedPreserveCopy";
  selectedModeTitle.dataset.i18n = titleKey;
  selectedModeCopy.dataset.i18n = copyKey;
  selectedModeTitle.textContent = t(titleKey);
  selectedModeCopy.textContent = t(copyKey);
  const showcaseName = isCharacterMode ? "character" : "preserve";
  setShowcase(showcaseCards.find((card) => card.dataset.showcase.includes(showcaseName)));
}

function setRealtimeMessage(message, isError = false) {
  realtimeMessage.textContent = message;
  realtimeMessage.classList.toggle("error", Boolean(isError));
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
  langButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.lang === currentLang);
  });
  syncModeState();
  setBusy(submitBusy);
  if (cameraStream) {
    cameraButton.textContent = t("stopCamera");
  }
  if (lastJob) {
    renderJob(lastJob);
  } else {
    jobStatusEl.textContent = t("statusIdle");
    jobStatusEl.dataset.status = "idle";
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

function drawBlobToCanvas(blob) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(blob);
    image.onload = () => {
      const context = cameraCanvas.getContext("2d");
      cameraCanvas.width = image.width;
      cameraCanvas.height = image.height;
      context.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);
      resolve();
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error(t("renderedFrameFailed")));
    };
    image.src = url;
  });
}
