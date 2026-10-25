const input = document.getElementById("input");
const output = document.getElementById("output");
const stylesEl = document.getElementById("styles");
const runBtn = document.getElementById("run");
const copyBtn = document.getElementById("copy");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error");
const resultWrap = document.getElementById("result-wrap");
const counter = document.getElementById("counter");

let selectedStyle = "academic";
let modelReady = false;

function setError(message) {
  if (!message) {
    errorEl.hidden = true;
    errorEl.textContent = "";
    return;
  }
  errorEl.hidden = false;
  errorEl.textContent = message;
}

function updateCounter() {
  counter.textContent = `${input.value.length} / 2000`;
}

function setStatus(kind, text) {
  statusEl.className = `status status-${kind}`;
  statusEl.textContent = text;
}

function updateRunEnabled() {
  runBtn.disabled = !modelReady || !input.value.trim() || !selectedStyle;
}

async function pollHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();

    if (data.status === "ready") {
      modelReady = true;
      setStatus("ready", "Модель готова");
      updateRunEnabled();
      return true;
    }

    if (data.status === "error") {
      modelReady = false;
      setStatus("error", "Ошибка загрузки модели");
      setError(data.error || "Не удалось загрузить нейросеть.");
      updateRunEnabled();
      return true;
    }

    setStatus("loading", "Загрузка модели…");
    return false;
  } catch {
    setStatus("error", "Сервер недоступен");
    return false;
  }
}

async function rewrite() {
  setError("");
  runBtn.disabled = true;
  runBtn.textContent = "Думаю…";

  try {
    const res = await fetch("/api/rewrite", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: input.value,
        style: selectedStyle,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Не удалось перефразировать текст.");
    }

    output.value = data.rewritten;
    resultWrap.hidden = false;
  } catch (err) {
    setError(err.message);
  } finally {
    runBtn.textContent = "Перефразировать";
    updateRunEnabled();
  }
}

copyBtn.addEventListener("click", async () => {
  if (!output.value) return;
  try {
    await navigator.clipboard.writeText(output.value);
    copyBtn.textContent = "Скопировано";
    setTimeout(() => {
      copyBtn.textContent = "Скопировать";
    }, 1200);
  } catch {
    setError("Не удалось скопировать текст.");
  }
});

input.addEventListener("input", () => {
  updateCounter();
  updateRunEnabled();
});

runBtn.addEventListener("click", rewrite);

updateCounter();

const FALLBACK_STYLES = [
  { id: "academic", label: "Академический" },
  { id: "business", label: "Деловой" },
  { id: "informal", label: "Неформальный" },
  { id: "poetic", label: "Поэтический" },
  { id: "simple", label: "Простой" },
  { id: "news", label: "Новостной" },
];

function renderStyles(styles) {
  stylesEl.innerHTML = "";
  for (const style of styles) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "style-btn" + (style.id === selectedStyle ? " active" : "");
    btn.textContent = style.label;
    btn.dataset.id = style.id;
    btn.setAttribute("role", "option");
    btn.setAttribute("aria-selected", style.id === selectedStyle ? "true" : "false");
    btn.addEventListener("click", () => {
      selectedStyle = style.id;
      stylesEl.querySelectorAll(".style-btn").forEach((el) => {
        const active = el.dataset.id === selectedStyle;
        el.classList.toggle("active", active);
        el.setAttribute("aria-selected", active ? "true" : "false");
      });
      updateRunEnabled();
    });
    stylesEl.appendChild(btn);
  }
}

async function loadStyles() {
  try {
    const res = await fetch("/api/styles");
    if (!res.ok) throw new Error("styles http " + res.status);
    renderStyles(await res.json());
  } catch (err) {
    console.warn("styles fallback", err);
    renderStyles(FALLBACK_STYLES);
  }
}

await loadStyles();
updateRunEnabled();

while (!(await pollHealth())) {
  await new Promise((r) => setTimeout(r, 1500));
}
