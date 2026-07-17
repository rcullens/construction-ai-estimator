const API = "http://127.0.0.1:17865";

let state = {
  hasProject: false, projectName: "Untitled Project", completeness: 0,
  tradeCount: 0, reviewCount: 0, packages: [], chatHistory: [],
  viewer: null, massing: null,
};

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function setStatus(msg) {
  document.getElementById("status").textContent = msg;
}

async function refreshState() {
  try {
    const data = await api("/state");
    state.hasProject = data.has_project;
    state.projectName = data.project_name || "Untitled Project";
    state.completeness = data.completeness || 0;
    state.tradeCount = data.trade_count || 0;
    state.reviewCount = data.review_count || 0;
    state.packages = data.packages || [];
    state.chatHistory = data.chat_history || [];
    state.viewer = data.viewer;
    state.massing = data.massing;
    document.getElementById("header-title").textContent = state.projectName;
  } catch (e) {}
}

function viewDashboard() {
  if (!state.hasProject) {
    return `<div class="empty">Upload PDFs and run an analysis to get started.<br>
      <button class="primary" style="margin-top:20px" onclick="showView('analyze')">Go to Analyze</button></div>`;
  }
  return `
    <div class="metrics">
      <div class="metric"><div style="color:var(--muted);font-size:0.78rem">Completeness</div><div class="value">${Math.round(state.completeness*100)}%</div></div>
      <div class="metric"><div style="color:var(--muted);font-size:0.78rem">Trade Packages</div><div class="value">${state.tradeCount}</div></div>
      <div class="metric"><div style="color:var(--muted);font-size:0.78rem">Needs Review</div><div class="value">${state.reviewCount}</div></div>
    </div>
    <div class="card"><h3>Quick Actions</h3>
      <button class="primary" onclick="window.open('${API}/viewer')" ${!state.viewer?"disabled":""}>Open 2D Viewer</button>
      <button class="primary" onclick="window.open('${API}/massing')" ${!state.massing?"disabled":""}>Open 3D Massing</button>
      <button class="primary" onclick="doExport()">Export JSON + Excel</button>
    </div>`;
}

function viewAnalyze() {
  return `<div class="card" style="max-width:560px"><h3>New Analysis</h3>
    <label>Project Name</label>
    <input type="text" id="proj-name" value="${state.projectName}" />
    <label>PDF Files</label>
    <input type="file" id="files" multiple accept=".pdf" />
    <button class="primary" id="run-btn" onclick="runAnalysis()">Run Full Analysis</button></div>`;
}

function viewChat() {
  const messages = state.chatHistory.length
    ? state.chatHistory.map(m => `<div class="msg ${m.role}">${m.content.replace(/\n/g,"<br>")}</div>`).join("")
    : `<div class="empty">No messages yet</div>`;
  return `<div class="chat-box">
    <div class="chat-messages" id="chat-messages">${messages}</div>
    <div class="chat-input">
      <input type="text" id="chat-input" placeholder="Ask about scope..." onkeydown="if(event.key==='Enter')sendChat()" ${!state.hasProject?"disabled":""} />
      <button class="primary" onclick="sendChat()" ${!state.hasProject?"disabled":""}>Send</button>
    </div></div>`;
}

async function viewTrades() {
  if (!state.hasProject) return `<div class="empty">No project loaded</div>`;
  const data = await api("/packages");
  return data.packages.map(pkg => `
    <div class="card"><h3>${pkg.trade_name} <span class="badge">${pkg.total_items} items</span></h3>
    <table style="width:100%;font-size:0.88rem"><thead><tr><th>Description</th><th>Conf</th><th>Override</th></tr></thead>
    <tbody>${pkg.requirements.map(r=>`<tr>
      <td>${r.description.slice(0,100)}</td><td>${r.confidence.toFixed(2)}</td>
      <td>${r.override?"Yes":""}</td></tr>`).join("")}</tbody></table></div>`).join("");
}

async function viewReview() {
  if (!state.hasProject) return `<div class="empty">No project loaded</div>`;
  const data = await api("/review");
  if (!data.items.length) return `<div class="empty" style="color:var(--success)">No items flagged</div>`;
  return data.items.map(r => `
    <div class="card"><strong>${r.trade_name}</strong>
      <p style="color:var(--muted);margin:8px 0">${r.description}</p>
      <div style="font-size:0.82rem">Confidence: ${r.confidence.toFixed(2)}</div></div>`).join("");
}

window.runAnalysis = async () => {
  const nameInput = document.getElementById("proj-name");
  const fileInput = document.getElementById("files");
  if (!fileInput.files.length) { alert("Select at least one PDF"); return; }
  setStatus("Running analysis…");
  document.getElementById("run-btn").disabled = true;
  try {
    await api("/project-name", { method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ name: nameInput.value || "Untitled Project" }) });
    const form = new FormData();
    for (const f of fileInput.files) form.append("files", f);
    await api("/analyze", { method:"POST", body: form });
    setStatus("Analysis complete");
    await refreshState();
    showView("dashboard");
  } catch (e) { setStatus("Error: " + e.message); alert(e.message); }
  finally { document.getElementById("run-btn").disabled = false; }
};

window.sendChat = async () => {
  const input = document.getElementById("chat-input");
  const msg = input.value.trim();
  if (!msg || !state.hasProject) return;
  input.value = "";
  setStatus("Thinking…");
  state.chatHistory.push({ role: "user", content: msg });
  showView("chat");
  try {
    const data = await api("/chat", { method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ message: msg }) });
    state.chatHistory = data.history;
    showView("chat");
    setStatus("Ready");
  } catch (e) { setStatus("Chat error: " + e.message); }
};

window.doExport = async () => {
  try {
    setStatus("Exporting…");
    const data = await api("/export", { method: "POST" });
    setStatus(`Exported → ${data.excel}`);
  } catch (e) { alert(e.message); setStatus("Ready"); }
};

async function showView(name) {
  document.querySelectorAll("nav button").forEach(b => b.classList.toggle("active", b.dataset.view === name));
  const content = document.getElementById("content");
  if (name === "dashboard") content.innerHTML = viewDashboard();
  else if (name === "analyze") content.innerHTML = viewAnalyze();
  else if (name === "chat") content.innerHTML = viewChat();
  else if (name === "trades") content.innerHTML = await viewTrades();
  else if (name === "review") content.innerHTML = await viewReview();
}
window.showView = showView;

document.getElementById("nav").addEventListener("click", e => {
  const btn = e.target.closest("button[data-view]");
  if (btn) showView(btn.dataset.view);
});

refreshState().then(() => showView("dashboard"));
setInterval(refreshState, 10000);
