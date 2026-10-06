const form = document.querySelector("#mission-form");
const startButton = document.querySelector("#start-button");
const pauseButton = document.querySelector("#pause-button");
const stopButton = document.querySelector("#stop-button");
const errorMessage = document.querySelector("#error-message");

const durationInput = document.querySelector("#duration");
const intervalInput = document.querySelector("#interval");
const stepsInput = document.querySelector("#steps");

function formatSeconds(value) {
  const seconds = Math.max(0, Math.round(value));
  if (seconds < 60) return `${seconds} sec`;
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return remainder ? `${minutes} min ${remainder} sec` : `${minutes} min`;
}

function roundLikePython(value) {
  const lower = Math.floor(value);
  const fraction = value - lower;
  if (fraction === 0.5) return lower % 2 === 0 ? lower : lower + 1;
  return Math.round(value);
}

function updatePreview() {
  const duration = Number(durationInput.value);
  const interval = Number(intervalInput.value);
  const steps = Number(stepsInput.value);
  const valid = Number.isFinite(duration) && duration > 0 &&
    Number.isFinite(interval) && interval > 0 &&
    Number.isInteger(steps) && steps >= 0;

  if (!valid) {
    document.querySelector("#preview-activations").textContent = "—";
    document.querySelector("#preview-steps").textContent = "—";
    document.querySelector("#preview-duration").textContent = "—";
    return;
  }

  const activations = Math.trunc(duration * 60 / interval);
  const stepsPerActivation = activations ? roundLikePython(steps / activations) : 0;
  document.querySelector("#preview-activations").textContent = activations.toLocaleString();
  document.querySelector("#preview-steps").textContent = stepsPerActivation.toLocaleString();
  document.querySelector("#preview-duration").textContent = formatSeconds(duration * 60);
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = !message;
}

function updateStatus(status) {
  const active = ["RUNNING", "PAUSED", "STOPPING"].includes(status.state);
  document.querySelector("#mission-state").textContent = status.state;
  document.querySelector("#completed-activations").textContent =
    `${status.activations} / ${status.total_activations}`;
  document.querySelector("#elapsed-time").textContent = formatSeconds(status.elapsed_seconds);
  document.querySelector("#remaining-time").textContent = formatSeconds(status.remaining_seconds);
  document.querySelector("#next-activation").textContent = status.next_activation_in === null
    ? "—"
    : formatSeconds(status.next_activation_in);

  const progress = Math.max(0, Math.min(1, status.progress));
  document.querySelector("#mission-progress").value = progress;
  document.querySelector("#progress-percent").textContent = `${Math.round(progress * 100)}%`;
  document.querySelector("#progress-label").textContent = active
    ? `Activation ${status.activations} of ${status.total_activations}`
    : status.state === "COMPLETED" ? "Sequence complete" : "No active mission";

  startButton.disabled = active;
  pauseButton.disabled = !["RUNNING", "PAUSED"].includes(status.state);
  pauseButton.textContent = status.state === "PAUSED" ? "Resume mission" : "Pause mission";
  stopButton.disabled = !["RUNNING", "PAUSED"].includes(status.state);
  for (const field of form.elements) {
    if (field !== pauseButton && field !== stopButton) field.disabled = active;
  }

  if (status.error) showError(status.error);
  document.querySelector("#connection-state").textContent = "Connected to local controller";
  document.querySelector(".connection-dot").style.backgroundColor = "#4f9b6e";
}

async function fetchStatus() {
  const response = await fetch("/api/status", { cache: "no-store" });
  if (!response.ok) throw new Error("Unable to read mission status");
  updateStatus(await response.json());
}

async function fetchSystemInfo() {
  try {
    const response = await fetch("/api/system", { cache: "no-store" });
    if (!response.ok) throw new Error("Unable to read system information");
    const system = await response.json();
    document.querySelector("#controller-host").textContent = system.hostname;
    document.querySelector("#cpu-temperature").textContent = system.cpu_temperature_c === null
      ? "Unavailable"
      : `${system.cpu_temperature_c.toFixed(1)} °C`;
  } catch (error) {
    document.querySelector("#cpu-temperature").textContent = "Unavailable";
  }
}

async function pollStatus() {
  try {
    await fetchStatus();
  } catch (error) {
    document.querySelector("#connection-state").textContent = "Controller connection lost; retrying";
    document.querySelector(".connection-dot").style.backgroundColor = "#a84437";
  }
  window.setTimeout(pollStatus, 1000);
}

function pollSystemInfo() {
  fetchSystemInfo();
  window.setTimeout(pollSystemInfo, 30000);
}

for (const input of [durationInput, intervalInput, stepsInput]) {
  input.addEventListener("input", updatePreview);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");
  const payload = {
    length_in_minutes: Number(durationInput.value),
    interval_in_seconds: Number(intervalInput.value),
    number_of_total_turns: Number(stepsInput.value),
    direction: document.querySelector("#direction").value,
  };

  try {
    const response = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Unable to start mission");
    updateStatus(result);
  } catch (error) {
    showError(error.message);
  }
});

stopButton.addEventListener("click", async () => {
  showError("");
  try {
    const response = await fetch("/api/stop", { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Unable to stop mission");
    updateStatus(result);
  } catch (error) {
    showError(error.message);
  }
});

pauseButton.addEventListener("click", async () => {
  showError("");
  const isPaused = document.querySelector("#mission-state").textContent === "PAUSED";
  try {
    const response = await fetch(isPaused ? "/api/resume" : "/api/pause", { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Unable to change mission pause state");
    updateStatus(result);
  } catch (error) {
    showError(error.message);
  }
});

updatePreview();
pollStatus();
pollSystemInfo();
