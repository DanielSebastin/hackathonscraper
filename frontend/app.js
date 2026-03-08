const API = "http://127.0.0.1:8000";
const SAVE_KEY = "hf_saved";

/* ── Saved hackathons (localStorage) ───────────────────────── */
function getSaved() {
  try { return JSON.parse(localStorage.getItem(SAVE_KEY) || "{}"); }
  catch { return {}; }
}

function saveHackathon(id, data) {
  const saved = getSaved();
  saved[id] = data;
  localStorage.setItem(SAVE_KEY, JSON.stringify(saved));
  updateSavedBadge();
}

function unsaveHackathon(id) {
  const saved = getSaved();
  delete saved[id];
  localStorage.setItem(SAVE_KEY, JSON.stringify(saved));
  updateSavedBadge();
}

function isSaved(id) {
  return !!getSaved()[id];
}

function cardId(r) {
  return r.registration_url || r.title || Math.random().toString(36);
}

function updateSavedBadge() {
  const badge = document.getElementById("savedBadge");
  if (!badge) return;
  const count = Object.keys(getSaved()).length;
  badge.textContent = count;
  badge.style.display = count > 0 ? "flex" : "none";
}

/* ── View toggle ────────────────────────────────────────────── */
let currentView = "search"; // "search" | "saved"

function showSearchView() {
  currentView = "search";
  document.getElementById("searchView").style.display = "";
  document.getElementById("savedView").style.display = "none";
  document.getElementById("navSearch").classList.add("active");
  document.getElementById("navSaved").classList.remove("active");
}

function showSavedView() {
  currentView = "saved";
  document.getElementById("searchView").style.display = "none";
  document.getElementById("savedView").style.display = "";
  document.getElementById("navSearch").classList.remove("active");
  document.getElementById("navSaved").classList.add("active");
  renderSavedList();
}

function renderSavedList() {
  const container = document.getElementById("savedResults");
  const saved = getSaved();
  const items = Object.entries(saved);

  if (items.length === 0) {
    container.innerHTML = `
      <div class="state-msg">
        ${svgBookmark("state-icon")}
        <h3>No saved hackathons</h3>
        <p>Hit the bookmark icon on any result to save it here.</p>
      </div>`;
    return;
  }

  container.innerHTML = "";
  items.forEach(([id, r], i) => {
    const card = buildCard(r, id, i);
    container.appendChild(card);
  });
}

/* ── Search ─────────────────────────────────────────────────── */
async function doSearch(overrideText) {
  const input = document.getElementById("searchInput");
  const query = (overrideText ?? input.value).trim();
  if (!query) return;
  if (overrideText) input.value = overrideText;

  showLoading();

  try {
    const res = await fetch(`${API}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: query, limit: 10 }),
    });

    if (!res.ok) throw new Error(`Server responded with status ${res.status}`);
    const data = await res.json();
    renderResults(data.results, query, data.llm_summary);
  } catch (err) {
    showError(err.message);
  }
}

function chipSearch(el) {
  showSearchView();
  doSearch(el.textContent.trim());
}

/* ── Render results ─────────────────────────────────────────── */
function renderResults(results, query, llmSummary) {
  const container = document.getElementById("results");
  const statsBar = document.getElementById("statsBar");
  const llmCard = document.getElementById("llmCard");
  const llmText = document.getElementById("llmText");

  container.innerHTML = "";

  document.getElementById("resultCount").textContent = results.length;
  document.getElementById("queryLabel").textContent = `"${query}"`;
  statsBar.style.display = "flex";

  if (llmSummary) {
    llmText.textContent = llmSummary;
    llmCard.classList.add("visible");
  } else {
    llmCard.classList.remove("visible");
  }

  if (results.length === 0) {
    container.innerHTML = `
      <div class="state-msg">
        ${svgSearch("state-icon")}
        <h3>No results found</h3>
        <p>No hackathons matched your query.<br>Try a broader or different search term.</p>
      </div>`;
    return;
  }

  results.forEach((r, i) => {
    const id = cardId(r);
    const card = buildCard(r, id, i);
    container.appendChild(card);
  });
}

/* ── Card builder (shared) ──────────────────────────────────── */
function buildCard(r, id, i = 0) {
  const card = document.createElement("div");
  card.className = "card";
  card.style.animationDelay = `${i * 0.04}s`;
  card.dataset.cardId = id;

  const scorePercent = Math.round((r.score || 0) * 100);
  const scoreHtml = r.score != null ? `<span class="score-pill">${scorePercent}%</span>` : "";
  const saved = isSaved(id);

  const regBtn = r.registration_url
    ? `<a class="reg-btn" href="${r.registration_url}" target="_blank" rel="noopener noreferrer">Register</a>`
    : `<span class="reg-btn disabled">No link</span>`;

  // Format Dates
  const startDate = r.date || "TBD";
  const endDate = r.end_date ? ` – ${r.end_date}` : "";
  const fullDate = `${startDate}${endDate}`;

  const hasDomains = r.domains && r.domains.length > 0;
  const hasPS = r.problem_statements && r.problem_statements.length > 0;

  const domainStr = hasDomains ? r.domains.join(", ") : "";
  const psStr = hasPS ? r.problem_statements.join("\\n") : "";

  const deadline = r.registration_deadline ? `<span class="meta-item hl">${svgClock()}Apply by ${escHtml(r.registration_deadline)}</span>` : "";

  // Event info formatting
  const PREVIEW_LEN = 220;
  const cleanDesc = cleanText(r.description || "");
  const isLong = cleanDesc.length > PREVIEW_LEN;
  const previewDesc = isLong ? cleanDesc.slice(0, PREVIEW_LEN).trimEnd() + "…" : cleanDesc;

  const eventInfoHtml = `
    <div class="card-desc" data-full="${escAttr(cleanDesc)}" data-expanded="false">
      <strong>Event Info:</strong><br><br>
      <span class="desc-text desc-preview">${escHtml(previewDesc)}</span>
      ${hasDomains ? `<br><br><strong>Domain:</strong> ${escHtml(domainStr)}` : ""}
      ${hasPS ? `<br><br><strong>Problem Statements:</strong><br><span class="desc-text">${escHtml(cleanText(psStr))}</span>` : ""}
    </div>
    ${isLong ? `<button class="expand-btn" onclick="toggleExpand(event)">Show more</button>` : ""}
  `;

  card.innerHTML = `
    <div class="card-header">
      <div class="card-title">${escHtml(r.title || "Untitled")}</div>
      ${scoreHtml}
    </div>
    <div class="card-meta">
      ${deadline}
      <span class="meta-item">${svgCalendar()}${escHtml(fullDate)}</span>
      <span class="meta-item">${svgPin()}${escHtml(r.location || "Location TBD")}</span>
      ${r.team_size ? `<span class="meta-item">${svgUsers()}${escHtml(r.team_size)}</span>` : ""}
    </div>
    ${eventInfoHtml}
    <div class="card-footer">
      <div class="footer-left">
        <span class="type-badge">${escHtml(r.type || "Hackathon")}</span>
      </div>
      <div class="footer-right">
        <button
          class="save-later-btn ${saved ? "saved" : ""}"
          onclick="toggleSave(event, '${escAttr(id)}')"
          aria-label="${saved ? "Remove from saved" : "Save for later"}"
        >${saved ? "Saved" : "Save for later"}</button>
        ${regBtn}
      </div>
    </div>`;

  return card;
}

/* ── Expand / collapse ──────────────────────────────────────── */
function toggleExpand(event) {
  event.stopPropagation();
  const btn = event.currentTarget;
  const desc = btn.previousElementSibling; // .card-desc
  const preview = desc.querySelector(".desc-preview");
  const isExpanded = desc.dataset.expanded === "true";

  if (isExpanded) {
    const full = desc.dataset.full || "";
    preview.textContent = full.slice(0, 220).trimEnd() + "…";
    desc.dataset.expanded = "false";
    btn.textContent = "Show more";
  } else {
    preview.textContent = desc.dataset.full || "";
    desc.dataset.expanded = "true";
    btn.textContent = "Show less";
  }
}

function togglePS(event) {
  event.stopPropagation();
  const header = event.currentTarget;
  const list = header.nextElementSibling;
  const arrow = header.querySelector(".ps-arrow");

  const isExpanded = list.style.display === "block";
  list.style.display = isExpanded ? "none" : "block";
  arrow.style.transform = isExpanded ? "rotate(0deg)" : "rotate(180deg)";
}

/* ── Toggle save ────────────────────────────────────────────── */
function toggleSave(event, id) {
  event.stopPropagation();

  const card = event.currentTarget.closest(".card");
  const title = card.querySelector(".card-title")?.textContent || "";
  const metaItems = card.querySelectorAll(".meta-item");
  const date = metaItems[0]?.textContent.trim() || "";
  const location = metaItems[1]?.textContent.trim() || "";
  const desc = card.querySelector(".card-desc")?.textContent || "";
  const type = card.querySelector(".type-badge")?.textContent || "";
  const regLink = card.querySelector("a.reg-btn")?.href || null;

  const btn = event.currentTarget;

  if (isSaved(id)) {
    unsaveHackathon(id);
    btn.classList.remove("saved");
    btn.textContent = "Save for later";
    btn.ariaLabel = "Save for later";
    if (currentView === "saved") card.remove();
    if (currentView === "saved" && !document.querySelector("#savedResults .card")) renderSavedList();
  } else {
    saveHackathon(id, { title, date, location, description: desc, type, registration_url: regLink });
    btn.classList.add("saved");
    btn.textContent = "Saved";
    btn.ariaLabel = "Remove from saved";
  }
}

/* ── States ─────────────────────────────────────────────────── */
function showLoading() {
  document.getElementById("statsBar").style.display = "none";
  document.getElementById("llmCard").classList.remove("visible");
  document.getElementById("results").innerHTML = Array(6).fill(`
    <div class="skeleton">
      <div class="skel-line" style="width:60%;height:14px"></div>
      <div class="skel-line" style="width:40%"></div>
      <div class="skel-line" style="width:90%;margin-top:4px"></div>
      <div class="skel-line" style="width:70%"></div>
    </div>`).join("");
}

function showError(msg) {
  document.getElementById("statsBar").style.display = "none";
  document.getElementById("results").innerHTML = `
    <div class="state-msg">
      ${svgError("state-icon")}
      <h3>Connection failed</h3>
      <p>Could not reach the API. Make sure the server is running.
        <span class="error-detail">${escHtml(msg)}</span>
      </p>
    </div>`;
}

/* ── SVG Icons ──────────────────────────────────────────────── */
function svgCalendar() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>
  </svg>`;
}
function svgPin() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
    <circle cx="12" cy="9" r="2.5"/>
  </svg>`;
}
function svgUsers() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
  </svg>`;
}
function svgClock() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>
  </svg>`;
}
function svgTrophy() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><circle cx="12" cy="9" r="6"></circle>
  </svg>`;
}
function svgList() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line>
  </svg>`;
}
function svgSearch(cls = "") {
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
  </svg>`;
}
function svgError(cls = "") {
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
  </svg>`;
}
function svgBookmark(cls = "") {
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
  </svg>`;
}
function svgBookmarkOutline() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
  </svg>`;
}
function svgBookmarkFilled() {
  return `<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
  </svg>`;
}

/* ── Utils ──────────────────────────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function escAttr(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

/**
 * Strips emojis and cleans up raw scraped text into readable prose.
 * Collapses multiple newlines/whitespace into single spaces.
 */
function cleanText(str) {
  return String(str)
    // remove emoji
    .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F000}-\u{1FFFF}]/gu, "")
    // collapse any mix of newlines/tabs/multiple spaces to a single space
    .replace(/[\r\n\t]+/g, " ")
    .replace(/ {2,}/g, " ")
    .trim();
}

/* ── Init ───────────────────────────────────────────────────── */
document.getElementById("searchInput").addEventListener("keydown", e => {
  if (e.key === "Enter") doSearch();
});

updateSavedBadge();
