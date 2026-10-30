// OrderFlow · utilidades compartidas del portal de clientes.

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...opts,
  });
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  return { ok: res.ok, status: res.status, data };
}

function money(n) {
  if (n === null || n === undefined || isNaN(n)) return "-";
  return "$ " + Number(n).toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function esc(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function fmtDate(s, withTime = false) {
  if (!s) return "-";
  const d = new Date(s);
  if (isNaN(d)) return esc(s);
  const opts = { day: "2-digit", month: "short", year: "numeric" };
  const day = d.toLocaleDateString("es-AR", opts).replace(/\./g, "").replace(/ de /g, " ");
  if (!withTime) return day;
  return `${day}, ${d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false })} h`;
}

const STATUS_LABELS = {
  pendiente: "Pendiente",
  procesando: "En proceso",
  enviado: "Enviado",
  entregado: "Entregado",
  preparando: "En preparación",
  en_transito: "En tránsito",
};

function statusLabel(s) {
  const k = (s || "").toLowerCase();
  return STATUS_LABELS[k] || (s ? s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, " ") : "-");
}

function statusTag(s) {
  const k = (s || "").toLowerCase();
  return `<span class="tag tag-${esc(k)}"><i></i>${esc(statusLabel(s))}</span>`;
}

function initials(name) {
  const words = String(name || "").replace(/[^\p{L}\s]/gu, "").trim().split(/\s+/).filter(Boolean);
  return (words.slice(0, 2).map(w => w[0]).join("") || "?").toUpperCase();
}

function skeletonRows(n, cols) {
  const row = `<tr>${'<td><span class="skel"></span></td>'.repeat(cols)}</tr>`;
  return row.repeat(n);
}

function emptyRow(cols, text) {
  return `<tr><td colspan="${cols}"><div class="empty">
    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/></svg>
    <span>${esc(text)}</span></div></td></tr>`;
}

// Menú de usuario y sidebar mobile.
document.addEventListener("click", (e) => {
  const menu = document.querySelector(".usermenu");
  if (menu) {
    if (e.target.closest(".usermenu-btn")) menu.classList.toggle("open");
    else if (!e.target.closest(".usermenu-pop")) menu.classList.remove("open");
  }
  if (e.target.closest(".nav-toggle")) document.body.classList.toggle("nav-open");
  else if (e.target.closest(".scrim")) document.body.classList.remove("nav-open");
});
