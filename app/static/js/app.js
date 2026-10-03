// Utilidades compartidas del front de OrderFlow.
// El front consume la API REST (/api/...) que es la superficie de ataque del lab.

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
  return "$ " + Number(n).toLocaleString("es-AR", { minimumFractionDigits: 2 });
}

function esc(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function statusTag(s) {
  const k = (s || "").toLowerCase();
  return `<span class="tag tag-${esc(k)}">${esc(s)}</span>`;
}
