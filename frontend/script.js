const BASE_URL = "http://127.0.0.1:8000";

const pdfFile = document.getElementById("pdfFile");
const fileName = document.getElementById("fileName");
const uploadBtn = document.getElementById("uploadBtn");
const uploadMessage = document.getElementById("uploadMessage");
const queryInput = document.getElementById("queryInput");
const askBtn = document.getElementById("askBtn");
const spinner = document.getElementById("spinner");
const answerText = document.getElementById("answerText");
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
    title.textContent = `${source.source} · Page ${source.page}`;

    const text = document.createElement("p");
    text.className = "source-text";
    text.textContent = source.text;

    item.append(title, text);
    fragment.appendChild(item);
  });

  sourcesList.appendChild(fragment);
}

pdfFile.addEventListener("change", () => {
  fileName.textContent = pdfFile.files[0]?.name || "Choose a PDF file";
  setMessage(uploadMessage, "");
});

uploadBtn.addEventListener("click", async () => {
  const file = pdfFile.files[0];
  if (!file) {
    setMessage(uploadMessage, "Please choose a PDF first.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  setBusy(true, "upload");
  setMessage(uploadMessage, "Uploading and indexing document...");

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
  } catch (error) {
    setMessage(uploadMessage, error.message || "Upload request failed", "error");
  } finally {
    setBusy(false);
  }
});

askBtn.addEventListener("click", async () => {
  const query = queryInput.value.trim();
  if (!query) {
    answerText.textContent = "Enter a question first.";
    renderSources([]);
    return;
  }

  setBusy(true, "query");
  answerText.textContent = "Thinking...";
  renderSources([]);

  try {
    const url = new URL(`${BASE_URL}/query/`);
    url.searchParams.set("query", query);

    const response = await fetch(url, { method: "POST" });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Query failed");
    }

    answerText.textContent = data.answer || "No answer received";
    renderSources(data.sources);
  } catch (error) {
    answerText.textContent = error.message || "Request failed";
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
