// OrcaQuant Admin Frontend
// Güvenlik: DOM'a yazarken her zaman textContent kullanıyoruz, innerHTML'den kaçınıyoruz.
// Hata kontrolü: fetch wrapper + timeout + demo fallback.

const API_BASE = window.__ADMIN_API_BASE__ || "/api/admin/panel";      // Backend admin API kökü (override edilebilir)
const LOGIN_PAGE = window.__ADMIN_LOGIN__ || "/login.html";
const TOKEN_PROVIDER = () => {
  // Tavsiye: Üretimde token'ı HttpOnly cookie olarak verin. Burada örnek amaçlı localStorage bakıyoruz.
  try { return localStorage.getItem("token") || ""; } catch { return ""; }
};
const bootstrapGlobal = window.bootstrap;
const adminFetch = window.__ADMIN_FETCH__ || fetch;

function getCsrfToken(){
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta?.getAttribute("content") || "";
}

let __csrfEnsured = false;
async function ensureCsrf(){
  if (getCsrfToken()) { __csrfEnsured = true; return; }
  try {
    const res = await adminFetch("/api/csrf", { credentials: "include" });
    if (res.ok) {
      const { token } = await res.json();
      const meta = document.querySelector('meta[name="csrf-token"]') || (() => {
        const el = document.createElement("meta");
        el.setAttribute("name", "csrf-token");
        document.head.appendChild(el);
        return el;
      })();
      meta.setAttribute("content", token || "");
      __csrfEnsured = true;
    }
  } catch (err) {
    console.warn("Failed to ensure CSRF token", err);
  }
}

let __ME = { email: null, roles: [] };
function hasRole(role){
  return Array.isArray(__ME.roles) && __ME.roles.includes(role);
}
async function loadMe(){
  if (Array.isArray(__ME.roles) && __ME.roles.length) return;
  try {
    const data = await tryApi(() => fetchJSON("/me"), () => ({ email: null, roles: ["admin"] }));
    __ME = data || { email: null, roles: [] };
  } catch {
    __ME = { email: null, roles: [] };
  }
}
function applyRBAC(){
  const adminOnly = ["#features", "#logs"];
  adminOnly.forEach(route => {
    const link = document.querySelector(`.nav-link[data-route="${route}"]`);
    if (link) link.classList.toggle("d-none", !hasRole("admin"));
  });
  ["#btnBulkBan", "#btnBulkUnban"].forEach(sel => {
    const btn = document.querySelector(sel);
    if (btn) btn.classList.toggle("d-none", !hasRole("admin"));
  });
}

// Basit toast (Bootstrap varsa onu kullan; yoksa graceful fallback)
function showToast(msg, variant = "info") {
  const toastHost = document.getElementById("toast");
  const el = document.createElement("div");
  el.className = "toast align-items-center text-bg-" + (variant==="error"?"danger":variant) + " border-0";
  el.setAttribute("role", "status");
  el.setAttribute("aria-live", "polite");
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body"></div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  el.querySelector(".toast-body").textContent = msg;
  toastHost.appendChild(el);
  if (bootstrapGlobal && bootstrapGlobal.Toast) {
    const t = new bootstrapGlobal.Toast(el, { delay: 3000 });
    t.show();
    el.addEventListener("hidden.bs.toast", () => el.remove());
  } else {
    setTimeout(() => el.remove(), 3200);
  }
}

// Fetch helper (timeout + JSON + hata yönetimi)
async function fetchJSON(path, opts = {}) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), opts.timeout || 10000);
  const headers = new Headers(opts.headers || {});
  headers.set("Accept", "application/json");
  if (!headers.has("Content-Type") && opts.body) headers.set("Content-Type","application/json");
  const token = TOKEN_PROVIDER();
  if (token) headers.set("Authorization", "Bearer " + token);
  const method = (opts.method || "GET").toUpperCase();
  if (method !== "GET" && !__csrfEnsured) {
    await ensureCsrf();
  }
  const csrf = getCsrfToken();
  if (csrf) headers.set("X-CSRF-Token", csrf);

  try {
    const res = await adminFetch(API_BASE + path, { ...opts, headers, signal: ctrl.signal, credentials: "include" });
    clearTimeout(id);
    if (!res.ok) {
      if (res.status === 401 && LOGIN_PAGE) {
        location.assign(LOGIN_PAGE + "?next=" + encodeURIComponent(location.href));
        throw new Error("HTTP 401");
      }
      throw new Error(`HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    clearTimeout(id);
    throw e;
  }
}

// Demo veriler (API yoksa kullanılır)
const Demo = {
  overview: {
    users: 1280, usersDelta: "+3.1%",
    plans: 4,    plansDelta: "+1 plan",
    api: 18422, errors: "0.67%"
  },
  health: [
    { name:"API", status:"healthy", latencyMs: 42 },
    { name:"DB", status:"healthy", latencyMs: 17 },
    { name:"Redis", status:"healthy", latencyMs: 5 },
    { name:"Worker", status:"degraded", latencyMs: 120 }
  ],
  users:[
    { id:1, name:"Ali Veli", email:"ali@example.com", plan:"Premium", status:"active" },
    { id:2, name:"Ayşe Demir", email:"ayse@example.com", plan:"Basic", status:"banned" },
    { id:3, name:"Mehmet Kaya", email:"mehmet@example.com", plan:"Enterprise", status:"active" },
  ],
  plans:[
    { name:"Free", price:0, limits:"günlük 50 istek", active:true },
    { name:"Basic", price:99, limits:"günlük 500 istek", active:true },
    { name:"Premium", price:299, limits:"günlük 5.000 istek", active:true },
    { name:"Enterprise", price:0, limits:"özel", active:true },
  ],
  limits:[
    { key:"api_requests_day", used: 18422, limit: 50000 },
    { key:"websocket_concurrent", used: 120, limit: 500 },
    { key:"prediction_jobs_day", used: 64, limit: 300 },
  ],
  features: { // kullanıcıya özel değil, global örnek
    rbac:{ enabled:true, roles:["admin","analyst","viewer"] },
    flags:{ "new_dashboard":true, "ai_explanations":true, "legacy_api":false }
  },
  logs:[
    { ts:"2025-09-18 20:12:03", level:"INFO", source:"api", msg:"GET /limits/status 200" },
    { ts:"2025-09-18 20:13:11", level:"WARNING", source:"worker", msg:"Queue delay 1.2s" },
    { ts:"2025-09-18 20:15:55", level:"ERROR", source:"db", msg:"Timeout on query id=482" },
  ]
};

// UI yardımcıları
const $ = (sel, root=document) => root.querySelector(sel);
const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
function setLoading(v){
  $("#loading").classList.toggle("d-none", !v);
}
function activateRoute(hash){
  $$(".route").forEach(s => s.classList.add("d-none"));
  const id = "route-" + (hash.replace("#","") || "dashboard");
  const sec = $("#" + id) || $("#route-dashboard");
  sec.classList.remove("d-none");
  // navbar aktiflik
  $$(".nav-link[data-route]").forEach(a => {
    a.classList.toggle("active", a.getAttribute("data-route") === ("#" + sec.id.replace("route-","")));
  });
}

// RENDER Fonksiyonları (XSS güvenli: textContent)
function renderOverview(data){
  $("#statUsers").textContent = data.users;
  $("#statUsersDelta").textContent = data.usersDelta;
  $("#statPlans").textContent = data.plans;
  $("#statPlansDelta").textContent = data.plansDelta;
  $("#statApi").textContent = data.api.toString();
  $("#statErr").textContent = data.errors;
}
function renderHealth(items){
  const host = $("#healthList");
  host.innerHTML = "";
  items.forEach(x=>{
    const col = document.createElement("div");
    col.className = "col-12 col-md-3";
    const card = document.createElement("div");
    card.className = "p-3 rounded border h-100";
    card.style.borderColor = x.status==="healthy"?"#1ea672": x.status==="degraded"?"#c8a234":"#c24848";
    const h = document.createElement("div");
    h.className = "fw-semibold";
    h.textContent = x.name;
    const s = document.createElement("div");
    s.textContent = `Durum: ${x.status} • ${x.latencyMs}ms`;
    card.append(h,s);
    col.append(card);
    host.append(col);
  });
}
function renderUsers(rows){
  const tb = $("#usersTbody");
  tb.innerHTML = "";
  rows.forEach(u=>{
    const tr = document.createElement("tr");
    const selectCell = document.createElement("td");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.className = "user-select";
    cb.dataset.id = String(u.id);
    cb.disabled = !hasRole("admin");
    selectCell.append(cb);
    tr.append(selectCell);
    const td = value => { const cell = document.createElement("td"); cell.textContent = value; return cell; };
    tr.append(td(String(u.id)), td(u.name), td(u.email), td(u.plan), td(u.status));
    const act = document.createElement("td");
    act.className = "text-end";
    const btnView = document.createElement("button");
    btnView.className = "btn btn-sm btn-outline-secondary me-2"; btnView.textContent = "Görüntüle";
    btnView.addEventListener("click", ()=>showToast("Detay modalı burada açılabilir.", "info"));
    const btnBan = document.createElement("button");
    btnBan.className = "btn btn-sm " + (u.status==="banned"?"btn-success":"btn-danger");
    btnBan.textContent = (u.status==="banned"?"Unban":"Ban");
    btnBan.addEventListener("click", async ()=>{
      try{
        if (!hasRole("admin")) { showToast("Yetkiniz yok.","error"); return; }
        if (!confirm(`Kullanıcıyı ${u.status==="banned"?"yeniden aktifleştirmek":"banlamak"} istediğinize emin misiniz?`)) return;
        // Örnek/Planlanan uç: PATCH /users/:id  {status:'banned'|'active'}
        await tryApi(()=>fetchJSON(`/users/${u.id}`, {
          method:"PATCH", body: JSON.stringify({ status: u.status==="banned"?"active":"banned" })
        }));
        u.status = (u.status==="banned"?"active":"banned");
        renderUsers(rows);
        showToast("Kullanıcı durumu güncellendi.","success");
      }catch(e){ showToast("Güncelleme başarısız: "+e.message,"error"); }
    });
    act.append(btnView, btnBan);
    tr.append(act);
    tb.append(tr);
  });
}
function renderPlans(rows){
  const tb = $("#plansTbody");
  tb.innerHTML = "";
  rows.forEach(p=>{
    const tr = document.createElement("tr");
    const td = (t)=>{ const x=document.createElement("td"); x.textContent = t; return x; };
    tr.append(td(p.name), td(`${p.price} ₺`), td(p.limits), td(p.active?"Evet":"Hayır"));
    const act = document.createElement("td");
    act.className = "text-end";
    const btnEdit = document.createElement("button");
    btnEdit.className = "btn btn-sm btn-outline-primary me-2"; btnEdit.textContent="Düzenle";
    btnEdit.addEventListener("click", ()=>showToast("Plan düzenleme modalı açılabilir.","info"));
    const btnToggle = document.createElement("button");
    btnToggle.className = "btn btn-sm " + (p.active?"btn-warning":"btn-success");
    btnToggle.textContent = p.active?"Pasifleştir":"Aktifleştir";
    btnToggle.addEventListener("click", async ()=>{
      try{
        if (!hasRole("admin")) { showToast("Yetkiniz yok.","error"); return; }
        await tryApi(()=>fetchJSON(`/plans/${encodeURIComponent(p.name)}`, {
          method:"PATCH", body: JSON.stringify({ active: !p.active })
        }));
        p.active = !p.active;
        renderPlans(rows);
      }catch(e){ showToast("Plan güncellenemedi: "+e.message,"error"); }
    });
    act.append(btnEdit, btnToggle);
    tr.append(act);
    tb.append(tr);
  });
}
function renderLimits(items){
  const host = $("#limitsBody");
  host.innerHTML = "";
  items.forEach(x=>{
    const wrap = document.createElement("div");
    wrap.className = "mb-3";
    const label = document.createElement("div");
    label.className = "d-flex justify-content-between small mb-1";
    const left = document.createElement("span");
    left.textContent = x.key;
    const right = document.createElement("span");
    right.textContent = `${x.used}/${x.limit}`;
    label.append(left, right);
    const progOuter = document.createElement("div");
    progOuter.className = "progress progress-sm";
    const prog = document.createElement("div");
    const pct = Math.min(100, Math.round((x.used/x.limit)*100));
    prog.className = "progress-bar";
    prog.style.width = pct + "%";
    prog.setAttribute("aria-valuemin","0");
    prog.setAttribute("aria-valuemax","100");
    prog.setAttribute("aria-valuenow", pct.toString());
    prog.textContent = pct + "%";
    progOuter.append(prog);
    wrap.append(label, progOuter);
    host.append(wrap);
  });
}
function renderLogs(rows, level=""){
  const tb = $("#logsTbody");
  tb.innerHTML = "";
  rows.filter(r=>!level || r.level===level).forEach(r=>{
    const tr = document.createElement("tr");
    const td = (t)=>{ const x=document.createElement("td"); x.textContent = t; return x; };
    tr.append(td(r.ts), td(r.level), td(r.source), td(r.msg));
    tb.append(tr);
  });
}

const State = {
  users: { page: 1, pageSize: 20, q: "", sort: "id", order: "desc", lastCount: 0 },
  logs: { page: 1, pageSize: 50, level: "", sort: "id", order: "desc", lastCount: 0 }
};
const Cache = { users: [], logs: [] };

function debounce(fn, delay = 300){
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// CSV export (Kullanıcılar için)
function exportCSV(filename, rows){
  const header = ["id","name","email","plan","status"];
  const esc = (v)=> `"${String(v).replace(/"/g,'""')}"`;
  const csv = [header.join(",")]
    .concat(rows.map(r=>[r.id,r.name,r.email,r.plan,r.status].map(esc).join(",")))
    .join("\n");
  const blob = new Blob([csv], {type:"text/csv;charset=utf-8;"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function exportLogsCSV(filename, rows){
  const header = ["ts","level","source","msg"];
  const esc = (v)=> `"${String(v).replace(/"/g,'""')}"`;
  const csv = [header.join(",")]
    .concat(rows.map(r=>[r.ts,r.level,r.source,r.msg].map(esc).join(",")))
    .join("\n");
  const blob = new Blob([csv], {type:"text/csv;charset=utf-8;"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// Basit API/dş. Mod yürütücü
async function tryApi(fn, demoFn){
  try { return await fn(); }
  catch(e){
    // API ulaşılamıyorsa Demo Modu
    if (demoFn) return demoFn();
    throw e;
  }
}

// Yükleme Akışı
async function loadDashboard(){
  setLoading(true);
  try{
    const overview = await tryApi(
      ()=>fetchJSON("/overview"),
      ()=>Demo.overview
    );
    renderOverview(overview);
    const health = await tryApi(
      ()=>fetchJSON("/health"),
      ()=>Demo.health
    );
    renderHealth(health);
  } finally { setLoading(false); }
}
async function loadUsers(){
  setLoading(true);
  try{
    const s = State.users;
    const params = new URLSearchParams({
      limit: String(s.pageSize),
      page: String(s.page),
      sort: s.sort,
      order: s.order,
    });
    if (s.q) params.set("q", s.q);
    const response = await tryApi(
      ()=>fetchJSON(`/users?${params.toString()}`),
      ()=>({ items: Demo.users, page: 1, page_size: Demo.users.length })
    );
    const rows = response.items || [];
    Cache.users = rows;
    renderUsers(rows);
    State.users.lastCount = rows.length;
    const search = $("#userSearch");
    if (search){
      search.value = s.q;
      search.oninput = debounce((e)=>{
        State.users.q = (e.target.value || "").trim();
        State.users.page = 1;
        loadUsers();
      });
    }
    const pageSizeSelect = $("#userPageSize");
    if (pageSizeSelect){
      pageSizeSelect.value = String(s.pageSize);
      pageSizeSelect.onchange = (e)=>{
        const nextSize = parseInt(e.target.value || "20", 10) || 20;
        State.users.pageSize = nextSize;
        State.users.page = 1;
        loadUsers();
      };
    }
    const exportBtn = $("#btnExportUsers");
    if (exportBtn) exportBtn.onclick = ()=>exportCSV("users.csv", Cache.users);
    const selectAll = $("#usersSelectAll");
    if (selectAll){
      selectAll.checked = false;
      selectAll.onchange = (e)=>{
        $$(".user-select").forEach(cb=>{ cb.checked = e.target.checked; });
      };
    }
    const bulkBan = $("#btnBulkBan");
    if (bulkBan) bulkBan.onclick = ()=>bulkUserStatus("banned");
    const bulkUnban = $("#btnBulkUnban");
    if (bulkUnban) bulkUnban.onclick = ()=>bulkUserStatus("active");
    installPager("users", loadUsers);
    installSortHandlers("users", loadUsers);
  } finally { setLoading(false); }
}
async function loadPlans(){
  setLoading(true);
  try{
    const plans = await tryApi(
      ()=>fetchJSON("/plans"),
      ()=>Demo.plans
    );
    renderPlans(plans);
    $("#btnNewPlan").onclick = ()=>showToast("Plan oluşturma akışını ekleyin (modal/form).","info");
  } finally { setLoading(false); }
}
async function loadLimits(){
  setLoading(true);
  try{
    const limits = await tryApi(
      ()=>fetchJSON("/limits/status"),
      ()=>Demo.limits
    );
    renderLimits(limits);
  } finally { setLoading(false); }
}
async function loadFeatures(){
  setLoading(true);
  try{
    const features = await tryApi(
      ()=>fetchJSON("/features"),
      ()=>Demo.features
    );
    const ta = $("#featuresJson");
    ta.value = JSON.stringify(features, null, 2);
    $("#btnSaveFeatures").onclick = async ()=>{
      const err = $("#featuresError");
      err.classList.add("d-none");
      try{
        const parsed = JSON.parse(ta.value);
        await tryApi(()=>fetchJSON("/features", {
          method:"PUT", body: JSON.stringify(parsed)
        }));
        showToast("Özel özellikler kaydedildi.","success");
      }catch(e){
        err.textContent = "JSON hatalı: " + e.message;
        err.classList.remove("d-none");
      }
    };
    $("#btnExportFeatures").onclick = ()=>{
      const blob = new Blob([$("#featuresJson").value], {type:"application/json"});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "features.json"; a.click();
      URL.revokeObjectURL(url);
    };
    $("#btnImportFeatures").onclick = ()=>{
      const inp = document.createElement("input");
      inp.type="file"; inp.accept="application/json";
      inp.onchange = async ()=>{
        const f = inp.files?.[0]; if(!f) return;
        const txt = await f.text();
        $("#featuresJson").value = txt;
      };
      inp.click();
    };
  } finally { setLoading(false); }
}
async function loadLogs(){
  setLoading(true);
  try{
    const s = State.logs;
    const params = new URLSearchParams({
      limit: String(s.pageSize),
      page: String(s.page),
      sort: s.sort,
      order: s.order,
    });
    if (s.level) params.set("level", s.level);
    const response = await tryApi(
      ()=>fetchJSON(`/logs?${params.toString()}`),
      ()=>({ items: Demo.logs, page: 1, page_size: Demo.logs.length })
    );
    const rows = response.items || [];
    Cache.logs = rows;
    renderLogs(rows, s.level);
    State.logs.lastCount = rows.length;
    const levelSelect = $("#logLevel");
    if (levelSelect){
      levelSelect.value = s.level;
      levelSelect.onchange = (e)=>{
        State.logs.level = e.target.value || "";
        State.logs.page = 1;
        loadLogs();
      };
    }
    const pageSizeSelect = $("#logPageSize");
    if (pageSizeSelect){
      pageSizeSelect.value = String(s.pageSize);
      pageSizeSelect.onchange = (e)=>{
        const nextSize = parseInt(e.target.value || "50", 10) || 50;
        State.logs.pageSize = nextSize;
        State.logs.page = 1;
        loadLogs();
      };
    }
    const exportBtn = $("#btnExportLogs");
    if (exportBtn) exportBtn.onclick = ()=>exportLogsCSV("logs.csv", Cache.logs);
    installPager("logs", loadLogs);
    installSortHandlers("logs", loadLogs);
  } finally { setLoading(false); }
}

function installPager(kind, reload){
  const state = State[kind];
  const hostId = `${kind}Pager`;
  let host = document.getElementById(hostId);
  if (!host){
    host = document.createElement("div");
    host.id = hostId;
    host.className = "d-flex justify-content-end gap-2 p-2";
    if (kind === "users") $("#route-users .card")?.appendChild(host);
    if (kind === "logs") $("#route-logs .card")?.appendChild(host);
  }
  host.innerHTML = "";
  const prev = document.createElement("button");
  prev.className = "btn btn-outline-secondary btn-sm";
  prev.textContent = "Önceki";
  prev.disabled = state.page <= 1;
  prev.onclick = ()=>{
    if (state.page > 1){ state.page -= 1; reload(); }
  };
  const next = document.createElement("button");
  next.className = "btn btn-outline-secondary btn-sm";
  next.textContent = "Sonraki";
  next.disabled = (state.lastCount || 0) < state.pageSize;
  next.onclick = ()=>{
    state.page += 1;
    reload();
  };
  const info = document.createElement("span");
  info.className = "align-self-center text-muted small";
  info.textContent = `Sayfa ${state.page}`;
  host.append(prev, next, info);
}

function installSortHandlers(kind, reload){
  const root = kind === "users" ? $("#route-users") : $("#route-logs");
  if (!root) return;
  const state = State[kind];
  $$(".th-sort", root).forEach(th => {
    const key = th.dataset.sort;
    th.classList.remove("active", "asc", "desc");
    if (key === state.sort){
      th.classList.add("active", state.order === "asc" ? "asc" : "desc");
    }
    th.onclick = ()=>{
      if (!key) return;
      if (state.sort === key){
        state.order = state.order === "asc" ? "desc" : "asc";
      } else {
        state.sort = key;
        state.order = "asc";
      }
      state.page = 1;
      reload();
    };
  });
}

function getSelectedUserIds(){
  return $$(".user-select").filter(cb => cb.checked).map(cb => parseInt(cb.dataset.id || "0", 10)).filter(Boolean);
}

async function bulkUserStatus(status){
  if (!hasRole("admin")) { showToast("Yetkiniz yok.", "error"); return; }
  const ids = getSelectedUserIds();
  if (!ids.length){ showToast("Seçili kullanıcı yok.", "info"); return; }
  const label = status === "banned" ? "banlamak" : "aktifleştirmek";
  if (!confirm(`${ids.length} kullanıcıyı ${label} istediğinize emin misiniz?`)) return;
  for (const id of ids){
    try{
      await tryApi(()=>fetchJSON(`/users/${id}`, { method:"PATCH", body: JSON.stringify({ status }) }));
    }catch(err){
      showToast(`ID ${id} güncellenemedi: ${err.message || err}`, "error");
    }
  }
  showToast("Toplu işlem tamamlandı.", "success");
  loadUsers();
}

// Tema toggler
function initTheme(){
  try{
    const saved = localStorage.getItem("admin.theme") || "dark";
    document.body.setAttribute("data-theme", saved);
  }catch{}
  $("#btnToggleTheme").onclick = ()=>{
    const cur = document.body.getAttribute("data-theme")==="dark" ? "light":"dark";
    document.body.setAttribute("data-theme", cur);
    try{ localStorage.setItem("admin.theme", cur); }catch{}
  };
}

// Router
async function handleRoute(){
  await loadMe();
  applyRBAC();
  const hash = location.hash || "#dashboard";
  activateRoute(hash);
  if (hash==="#dashboard") await loadDashboard();
  else if (hash==="#users") await loadUsers();
  else if (hash==="#plans") await loadPlans();
  else if (hash==="#limits") await loadLimits();
  else if (hash==="#features") await loadFeatures();
  else if (hash==="#logs") await loadLogs();
}

// Health check butonu
$("#btnHealthCheck")?.addEventListener("click", async ()=>{
  try{
    const h = await tryApi(()=>fetchJSON("/health"), ()=>Demo.health);
    renderHealth(h); showToast("Health check tamam.","success");
  }catch(e){ showToast("Health check başarısız: "+e.message, "error"); }
});

$("#btnRefresh").addEventListener("click", handleRoute);
window.addEventListener("hashchange", handleRoute);

initTheme();
handleRoute();
ensureCsrf();
