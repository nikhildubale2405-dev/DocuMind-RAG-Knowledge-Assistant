const BASE_URL = "";

const pdfFile = document.getElementById("pdfFile");
const fileName = document.getElementById("fileName");
const uploadBtn = document.getElementById("uploadBtn");
const uploadMessage = document.getElementById("uploadMessage");
const uploadTiming = document.getElementById("uploadTiming");
const queryInput = document.getElementById("queryInput");
const askBtn = document.getElementById("askBtn");
const spinner = document.getElementById("spinner");
const answerText = document.getElementById("answerText");
const answerTiming = document.getElementById("answerTiming");
const sourcesList = document.getElementById("sourcesList");
const apiStatus = document.getElementById("apiStatus");

function setMessage(element, message, type = "") {
  element.textContent = message;
  element.className = `message ${type}`.trim();
}

function setBusy(isBusy, action) {
  uploadBtn.disabled = isBusy;
  askBtn.disabled = isBusy;
  spinner.classList.toggle("hidden", !isBusy || action !== "query");
  apiStatus.textContent = isBusy ? "Processing" : "Ready";
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) {
    return "";
  }

  if (seconds < 1) {
    return `${Math.round(seconds * 1000)} ms`;
  }

  return `${seconds.toFixed(2)} s`;
}

function renderSources(sources) {
  sourcesList.innerHTML = "";

  if (!sources || sources.length === 0) {
    sourcesList.innerHTML = '<p class="muted">No sources returned.</p>';
    return;
  }

  const fragment = document.createDocumentFragment();

  sources.forEach((source) => {
    const item = document.createElement("div");
    item.className = "source-item";

    const title = document.createElement("div");
    title.className = "source-title";
    title.textContent = `${source.source} - Page ${source.page}`;

    const text = document.createElement("p");
    text.className = "source-text";
    text.textContent = source.text || "";

    item.append(title, text);
    fragment.appendChild(item);
  });

  sourcesList.appendChild(fragment);
}

pdfFile.addEventListener("change", () => {
  fileName.textContent = pdfFile.files[0]?.name || "Choose a PDF file";
  setMessage(uploadMessage, "");
  uploadTiming.textContent = "";
});

uploadBtn.addEventListener("click", async () => {
  const file = pdfFile.files[0];

  if (!file) {
    setMessage(uploadMessage, "Please choose a PDF first.", "error");
    uploadTiming.textContent = "";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  setBusy(true, "upload");
  setMessage(uploadMessage, "Uploading and indexing document...");
  uploadTiming.textContent = "";
  const uploadStartedAt = performance.now();

  try {
    const response = await fetch(`${BASE_URL}/upload/`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Upload failed");
    }

    setMessage(uploadMessage, data.message || "File uploaded successfully", "success");
    const clientUploadSeconds = (performance.now() - uploadStartedAt) / 1000;
    const uploadSeconds = Number(data.upload_time_seconds) || clientUploadSeconds;
    uploadTiming.textContent = `Upload time: ${formatDuration(uploadSeconds)}`;
  } catch (error) {
    setMessage(uploadMessage, error.message || "Upload request failed", "error");
    uploadTiming.textContent = "";
  } finally {
    setBusy(false);
  }
});

askBtn.addEventListener("click", async () => {
  const query = queryInput.value.trim();

  if (!query) {
    answerText.textContent = "Enter a question first.";
    answerTiming.textContent = "";
    renderSources([]);
    return;
  }

  setBusy(true, "query");
  answerText.textContent = "Thinking...";
  answerTiming.textContent = "";
  renderSources([]);
  const answerStartedAt = performance.now();

  try {
    const url = new URL(`${window.location.origin}/query/`);
    url.searchParams.set("query", query);

    const response = await fetch(url, { method: "POST" });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Query failed");
    }

    answerText.textContent = data.answer || "No answer received";
    const clientAnswerSeconds = (performance.now() - answerStartedAt) / 1000;
    const answerSeconds = Number(data.answer_time_seconds) || clientAnswerSeconds;
    answerTiming.textContent = `Answered in ${formatDuration(answerSeconds)}`;
    renderSources(data.sources);
  } catch (error) {
    answerText.textContent = error.message || "Request failed";
    answerTiming.textContent = "";
    renderSources([]);
  } finally {
    setBusy(false);
  }
});

queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    askBtn.click();
  }
});
