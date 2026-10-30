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

<<<<<<< HEAD
let currentStoredChunks = 0;

=======
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
function setMessage(element, message, type = "") {
  element.textContent = message;
  element.className = `message ${type}`.trim();
}

function setBusy(isBusy, action) {
  uploadBtn.disabled = isBusy;
  askBtn.disabled = isBusy;
  spinner.classList.toggle("hidden", !isBusy || action !== "query");
<<<<<<< HEAD
  if (!isBusy) {
    apiStatus.textContent = currentStoredChunks > 0 ? `${currentStoredChunks} Chunks Loaded` : "Ready";
  } else {
    apiStatus.textContent = action === "upload" ? "Indexing" : "Thinking";
  }
=======
  apiStatus.textContent = isBusy ? "Processing" : "Ready";
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
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
<<<<<<< HEAD
    const scoreInfo = source.score ? ` · Score: ${source.score}` : "";
    title.textContent = `${source.source} — Page ${source.page}${scoreInfo}`;
=======
    title.textContent = `${source.source} - Page ${source.page}`;
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46

    const text = document.createElement("p");
    text.className = "source-text";
    text.textContent = source.text || "";

    item.append(title, text);
    fragment.appendChild(item);
  });

  sourcesList.appendChild(fragment);
}

<<<<<<< HEAD
// Check initial index status on page load
async function checkInitialStatus() {
  try {
    const res = await fetch(`${BASE_URL}/upload/status`);
    if (res.ok) {
      const data = await res.json();
      currentStoredChunks = data.total_chunks || 0;
      if (currentStoredChunks > 0) {
        apiStatus.textContent = `${currentStoredChunks} Chunks Loaded`;
        answerText.textContent = `${currentStoredChunks} document chunks loaded from persistent storage. Ask any question below.`;
      } else {
        apiStatus.textContent = "Ready";
      }
    }
  } catch {
    apiStatus.textContent = "Ready";
  }
}

checkInitialStatus();

=======
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
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
<<<<<<< HEAD
  setMessage(uploadMessage, "Uploading, extracting, and indexing document...");
=======
  setMessage(uploadMessage, "Uploading and indexing document...");
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
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

<<<<<<< HEAD
    currentStoredChunks = data.total_chunks_stored || currentStoredChunks;
=======
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
    setMessage(uploadMessage, data.message || "File uploaded successfully", "success");
    const clientUploadSeconds = (performance.now() - uploadStartedAt) / 1000;
    const uploadSeconds = Number(data.upload_time_seconds) || clientUploadSeconds;
    uploadTiming.textContent = `Upload time: ${formatDuration(uploadSeconds)}`;
<<<<<<< HEAD
    answerText.textContent = `Indexed ${data.chunks_indexed || "new"} chunks. You can now ask questions about this document.`;
=======
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
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
<<<<<<< HEAD
    answerText.textContent = "Please enter a question first.";
=======
    answerText.textContent = "Enter a question first.";
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
    answerTiming.textContent = "";
    renderSources([]);
    return;
  }

  setBusy(true, "query");
<<<<<<< HEAD
  answerText.textContent = "Retrieving context and generating answer...";
=======
  answerText.textContent = "Thinking...";
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
  answerTiming.textContent = "";
  renderSources([]);
  const answerStartedAt = performance.now();

  try {
<<<<<<< HEAD
    // Send standard POST request with JSON payload for production robustness
    const response = await fetch(`${BASE_URL}/query/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query,
        top_k: 3,
        use_hybrid: true,
        use_langchain: false,
      }),
    });

=======
    const url = new URL(`${window.location.origin}/query/`);
    url.searchParams.set("query", query);

    const response = await fetch(url, { method: "POST" });
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
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
