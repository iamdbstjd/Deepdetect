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

const cameraButton = document.querySelector("#camera-button");
const sessionButton = document.querySelector("#session-button");
const cameraVideo = document.querySelector("#camera-video");
const cameraCanvas = document.querySelector("#camera-canvas");
const realtimeMessage = document.querySelector("#realtime-message");
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
    characterMode: "캐릭터 대체",
    characterModeHint: "참조 인물 얼굴에 캐릭터 적용",
    characterPreset: "캐릭터 프리셋",
    smileEmoji: "스마일 이모지",
    startProcess: "처리 시작",
    processingButton: "처리 중...",
    uploading: "업로드 중...",
    uploadFailed: "업로드 실패",
    jobNumber: "작업 번호",
    status: "상태",
    progress: "진행률",
    initialJobMessage: "영상과 참조 얼굴을 선택하면 처리를 시작할 수 있습니다.",
    downloadResult: "결과 영상 받기",
    realtime: "실시간",
    realtimeTitle: "실시간 미리보기",
    browserCamera: "브라우저 카메라",
    camera: "카메라",
    processedPreview: "처리 결과",
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
    characterMode: "Replace with character",
    characterModeHint: "Apply a character to the reference face",
    characterPreset: "Character preset",
    smileEmoji: "Smile emoji",
    startProcess: "Start processing",
    processingButton: "Processing...",
    uploading: "Uploading...",
    uploadFailed: "Upload failed",
    jobNumber: "Job number",
    status: "Status",
    progress: "Progress",
    initialJobMessage: "Select a video and reference face to start processing.",
    downloadResult: "Download result video",
    realtime: "Realtime",
    realtimeTitle: "Realtime preview",
    browserCamera: "Browser camera",
    camera: "Camera",
    processedPreview: "Processed result",
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
  setMessage(job.error || job.message || "", job.status === "failed");
  if (job.result_url) {
    downloadLink.href = job.result_url;
    downloadLink.classList.remove("hidden");
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
