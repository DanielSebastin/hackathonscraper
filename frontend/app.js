"use strict";

const API = "http://127.0.0.1:8000";
const SAVE_KEY = "hf_saved_v2";

/* ═══════ LocalStorage helpers ════════════════════════════════ */
function getSaved() {
  try { return JSON.parse(localStorage.getItem(SAVE_KEY) || "{}"); }
  catch { return {}; }
}
function saveItem(id, data) {
  const s = getSaved(); s[id] = data;
  localStorage.setItem(SAVE_KEY, JSON.stringify(s));
  updateBadge();
}
function unsaveItem(id) {
  const s = getSaved(); delete s[id];
  localStorage.setItem(SAVE_KEY, JSON.stringify(s));
  updateBadge();
}
function isSaved(id) { return !!getSaved()[id]; }
function cardId(r) { return (r.registration_url || r.title || Math.random().toString(36)).slice(0, 120); }

function updateBadge() {
  const badge = document.getElementById("savedBadge");
  if (!badge) return;
  const n = Object.keys(getSaved()).length;
  badge.textContent = n;
  badge.style.display = n > 0 ? "flex" : "none";
}

/* ═══════ Page routing ════════════════════════════════════════ */
let currentPage = "home";
let exploreState = {
  results: [],
  page: 1,
  limit: 9,
  total: 0
};

function activatePage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showHome() {
  currentPage = "home";
  activatePage("pageHome");
  document.getElementById("navHome").classList.add("active");
}

function showSearch() {
  currentPage = "search";
  activatePage("pageSearch");
  document.getElementById("navSearch").classList.add("active");
  setTimeout(() => document.getElementById("searchInput").focus(), 100);
}

function showSaved() {
  currentPage = "saved";
  activatePage("pageSaved");
  document.getElementById("navSaved").classList.add("active");
  renderSaved();
}

function showExplore() {
  currentPage = "explore";
  activatePage("pageExplore");
  document.getElementById("navExplore").classList.add("active");
  loadExplorePage(1);
}

/* ═══════ Search ══════════════════════════════════════════════ */
async function doSearch(override) {
  const input = document.getElementById("searchInput");
  const query = (override ?? input.value).trim();
  if (!query) { input.focus(); return; }
  if (override !== undefined) input.value = override;

  showLoading();

  try {
    const res = await fetch(`${API}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: query, limit: 9 }),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();
    renderResults(data.results, query, data.llm_summary);
  } catch (err) {
    showError(err.message);
  }
}

function chipSearch(el) { showSearch(); doSearch(el.textContent.trim()); }
function quickSearch(el) { showSearch(); doSearch(el.textContent.trim()); }

/* ═══════ Render results ══════════════════════════════════════ */
function renderResults(results, query, llmSummary) {
  const grid = document.getElementById("results");
  const meta = document.getElementById("resultsMeta");
  const llmCard = document.getElementById("llmCard");
  const llmText = document.getElementById("llmText");
  const emptyEl = document.getElementById("searchEmptyState");

  grid.innerHTML = "";
  emptyEl.style.display = "none";

  // AI summary
  if (llmSummary) {
    llmText.textContent = llmSummary;
    llmCard.style.display = "flex";
  } else {
    llmCard.style.display = "none";
  }

  // Meta bar
  document.getElementById("resultCount").textContent = results.length;
  document.getElementById("queryLabel").innerHTML = `"${escHtml(query)}"`;
  meta.style.display = results.length > 0 ? "block" : "none";

  if (results.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <h3>No results found</h3>
        <p>Try a different term, or broaden your search.</p>
      </div>`;
    return;
  }

  results.forEach((r, i) => {
    const id = cardId(r);
    const card = buildCard(r, id, i);
    grid.appendChild(card);
  });
}

/* ═══════ Saved page ══════════════════════════════════════════ */
function renderSaved() {
  const grid = document.getElementById("savedResults");
  const emptyEl = document.getElementById("savedEmptyState");
  const items = Object.entries(getSaved());

  grid.innerHTML = "";
  if (items.length === 0) {
    emptyEl.style.display = "";
    return;
  }
  emptyEl.style.display = "none";
  items.forEach(([id, r], i) => grid.appendChild(buildCard(r, id, i)));
}

/* ═══════ Prize value extractor ══════════════════════════════ */
function parsePrize(raw) {
  if (!raw) return null;
  // Match currency symbols followed by digits (e.g. ₹1,00,000 / $5000 / INR 50000)
  const match = String(raw).match(/([₹$€£]\s?[\d,]+(?:\.\d+)?(?:\s?(?:lakh|lakhs|L|k|K|crore|cr))?|INR\s?[\d,]+(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?(?:\s?(?:lakh|lakhs|L|k|K|crore|cr)))/i);
  return match ? match[0].trim() : null;
}

/* ═══════ Card builder ════════════════════════════════════════ */
function buildCard(r, id, i = 0) {
  const card = document.createElement("div");
  card.className = "card";
  card.style.animationDelay = `${i * 0.05}s`;
  card.dataset.cardId = id;

  const saved = isSaved(id);

  // SVG icons (inline, keeps things fast)
  const icoCalendar = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>`;
  const icoPin = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>`;

  const date = r.date ? `<div class="meta-row">${icoCalendar} ${escHtml(r.date)}</div>` : "";
  const location = r.location ? `<div class="meta-row">${icoPin} ${escHtml(r.location)}</div>` : "";

  const prizeVal = parsePrize(r.prize);
  const prizeDisplay = prizeVal ? escHtml(prizeVal) : "Not specified";
  const prizeBadge = `<span class="info-tag prize">🏆 ${prizeDisplay}</span>`;
  // Normalize fee text
  let feeText = "Refer website";
  if (r.fee && r.fee !== "Null" && String(r.fee).trim() !== "") {
    feeText = escHtml(r.fee);
  }
  const feeBadge = `<span class="info-tag fee">💳 ${feeText}</span>`;

  // Domains - filter out Knowafest and render it as a corner badge
  const domainsRaw = Array.isArray(r.domains) ? r.domains : [];
  const isKnowafest = domainsRaw.includes("Knowafest");
  const domains = domainsRaw.filter(d => d !== "Knowafest");
  
  let domainBadges = "";
  if (domains.length > 0) {
    domainBadges = domains.map((d, idx) => {
      const isExtra = idx >= 3;
      return `<span class="info-tag domain ${isExtra ? "hidden" : ""}">${escHtml(d)}</span>`;
    }).join("");
    
    if (domains.length > 3) {
      domainBadges += `<button class="more-tags" onclick="expandTags(this)">+${domains.length - 3} more</button>`;
    }
  }

  const knowafestBadge = isKnowafest ? `<div class="source-badge">Knowafest</div>` : "";

  const regBtn = r.registration_url
    ? `<a class="reg-btn" href="${escAttr(r.registration_url)}" target="_blank" rel="noopener noreferrer" aria-label="Register for ${escAttr(r.title || '')}">Register →</a>`
    : `<span class="reg-btn disabled">No link</span>`;

  const visitBtn = r.visit_url
    ? `<a class="reg-btn alt-btn" href="${escAttr(r.visit_url)}" target="_blank" rel="noopener noreferrer" aria-label="Visit site for ${escAttr(r.title || '')}">Visit Site ↗</a>`
    : ``;

  card.innerHTML = `
    ${knowafestBadge}
    <div class="card-title">${escHtml(r.title || "Untitled Hackathon")}</div>
    <div class="card-meta">
      ${date}
      ${location}
    </div>
    <div class="info-tags">
      ${prizeBadge}
      ${feeBadge}
      ${domainBadges}
    </div>
    <div class="card-footer">
      <button
        class="save-btn ${saved ? "saved" : ""}"
        onclick="toggleSave(event,'${escAttr(id)}')"
        aria-label="${saved ? "Remove from saved" : "Save hackathon"}"
        title="${saved ? "Remove from saved" : "Save for later"}"
      >${saved ? "−" : "+"}</button>
      <div style="display: flex; gap: 8px; margin-left: auto;">
        ${visitBtn}
        ${regBtn}
      </div>
    </div>`;

  return card;
}

/* ═══════ Toggle save ═════════════════════════════════════════ */
function toggleSave(event, id) {
  event.stopPropagation();
  const card = event.currentTarget.closest(".card");
  const btn = event.currentTarget;

  if (isSaved(id)) {
    unsaveItem(id);
    btn.classList.remove("saved");
    btn.textContent = "+";
    btn.setAttribute("aria-label", "Save hackathon");
    btn.title = "Save for later";
    if (currentPage === "saved") {
      card.style.transition = "opacity .25s, transform .25s";
      card.style.opacity = "0";
      card.style.transform = "scale(.95)";
      setTimeout(() => {
        card.remove();
        if (!document.querySelector("#savedResults .card")) renderSaved();
      }, 260);
    }
  } else {
    // Collect data directly from the card DOM (safe)
    const r = {
      title: card.querySelector(".card-title")?.textContent || "",
      date: card.querySelectorAll(".meta-row")[0]?.textContent.trim() || "",
      location: card.querySelectorAll(".meta-row")[1]?.textContent.trim() || "",
      prize: card.querySelector(".info-tag.prize")?.textContent.replace("🏆 ", "") || null,
      fee: card.querySelector(".info-tag.fee")?.textContent.replace("💳 ", "") || null,
      domains: Array.from(card.querySelectorAll(".info-tag.domain")).map(el => el.textContent),
      registration_url: card.querySelector("a.reg-btn:not(.alt-btn)")?.href || null,
      visit_url: card.querySelector("a.alt-btn")?.href || null,
    };
    saveItem(id, r);
    btn.classList.add("saved");
    btn.textContent = "−";
    btn.setAttribute("aria-label", "Remove from saved");
    btn.title = "Remove from saved";
  }
}

function expandTags(btn) {
  const container = btn.parentElement;
  container.querySelectorAll(".info-tag.domain.hidden").forEach(el => el.classList.remove("hidden"));
  btn.remove();
}

/* ═══════ Explore Page ════════════════════════════════════════ */
async function loadExplorePage(page) {
  const grid = document.getElementById("exploreResults");
  const emptyEl = document.getElementById("exploreEmptyState");
  
  grid.innerHTML = Array(6).fill(`
    <div class="skeleton">
      <div class="skel-line wide"></div>
      <div class="skel-line mid"></div>
      <div class="skel-line short" style="margin-top:6px"></div>
    </div>`).join("");
  emptyEl.style.display = "none";

  try {
    const res = await fetch(`${API}/explore?page=${page}&limit=${exploreState.limit}`);
    if (!res.ok) throw new Error("Failed to load events");
    const data = await res.json();
    
    exploreState.results = data.results;
    exploreState.total = data.total;
    exploreState.page = data.page;
    
    renderExplore();
  } catch (err) {
    grid.innerHTML = "";
    emptyEl.style.display = "block";
  }
}

function renderExplore() {
  const grid = document.getElementById("exploreResults");
  grid.innerHTML = "";
  
  if (exploreState.results.length === 0) {
    document.getElementById("exploreEmptyState").style.display = "block";
    return;
  }

  exploreState.results.forEach((r, i) => {
    grid.appendChild(buildCard(r, cardId(r), i));
  });

  document.getElementById("exploreMeta").textContent = `Showing ${exploreState.total} hackathons total`;

  updatePagination();
}

function updatePagination() {
  const pageNumbers = document.getElementById("pageNumbers");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  
  const totalPages = Math.ceil(exploreState.total / exploreState.limit);
  
  prevBtn.disabled = exploreState.page <= 1;
  nextBtn.disabled = exploreState.page >= totalPages;

  pageNumbers.innerHTML = "";
  
  // Show all pages if small, or a range if large
  // For now, let's just show all as the user specifically mentioned 4 pages
  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");
    btn.className = `page-num ${i === exploreState.page ? "active" : ""}`;
    btn.textContent = i;
    btn.onclick = () => goToPage(i);
    pageNumbers.appendChild(btn);
  }
}

function goToPage(n) {
  loadExplorePage(n);
}

function nextPage() {
  loadExplorePage(exploreState.page + 1);
}

function prevPage() {
  loadExplorePage(exploreState.page - 1);
}

/* ═══════ States ══════════════════════════════════════════════ */
function showLoading() {
  document.getElementById("resultsMeta").style.display = "none";
  document.getElementById("llmCard").style.display = "none";
  document.getElementById("searchEmptyState").style.display = "none";
  document.getElementById("results").innerHTML = Array(6).fill(`
    <div class="skeleton">
      <div class="skel-line wide"></div>
      <div class="skel-line mid"></div>
      <div class="skel-line short" style="margin-top:6px"></div>
      <div class="skel-line mid" style="margin-top:2px"></div>
    </div>`).join("");
}

function showError(msg) {
  document.getElementById("resultsMeta").style.display = "none";
  document.getElementById("results").innerHTML = `
    <div class="empty-state" style="grid-column:1/-1">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
      <h3>Connection failed</h3>
      <p>Could not reach the API — make sure the server is running.<br/>
         <small style="opacity:.6">${escHtml(msg)}</small></p>
    </div>`;
}

/* ═══════ Utils ═══════════════════════════════════════════════ */
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function escAttr(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

/* ═══════ Theme Toggle ════════════════════════════════════════ */
const THEME_KEY = "hf_theme";

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem(THEME_KEY, next);
}

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = saved || (prefersDark ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", theme);
}

/* ═══════ Init ════════════════════════════════════════════════ */
initTheme();
updateBadge();
