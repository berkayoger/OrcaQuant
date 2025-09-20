'use strict'

const API_ROOT = '/api/admin/dashboard'
const SSE_ENDPOINT = `${API_ROOT}/stream`
const TOKEN_CANDIDATES = ['jwt', 'auth_token', 'access_token', 'admin_token', 'oq_jwt', 'token']
const TOKEN_CANDIDATE_SET = new Set(TOKEN_CANDIDATES.map(k => k.toLowerCase()))
const SSE_RETRY_BASE = 1000
const SSE_RETRY_MAX = 30000

let sseSource = null
let sseReconnectTimer = null
let sseRetryDelay = SSE_RETRY_BASE
let sseShouldReconnect = true
let sseInitialized = false
let sseCurrentMeta = {url: null, token: null}
let sseConnectAttempts = 0
let sseScheduledDelay = null

function readTokenFromStorage(storage){
  if (!storage) return null
  try {
    for (const key of TOKEN_CANDIDATES) {
      const value = storage.getItem(key)
      if (value) return value
    }
  } catch (_) {
    return null
  }
  return null
}

function readTokenFromCookies(){
  if (typeof document === 'undefined' || !document.cookie) return null
  const parts = document.cookie.split(';')
  for (const part of parts) {
    const [rawKey, ...rest] = part.split('=')
    if (!rawKey) continue
    const key = rawKey.trim()
    if (!key) continue
    if (!TOKEN_CANDIDATE_SET.has(key.toLowerCase())) continue
    const value = rest.join('=')
    if (value) return decodeURIComponent(value.trim())
  }
  return null
}

function getStoredToken(){
  const storages = []
  try { storages.push(window.localStorage) } catch (_) { /* ignore */ }
  try { storages.push(window.sessionStorage) } catch (_) { /* ignore */ }
  for (const storage of storages) {
    const value = readTokenFromStorage(storage)
    if (value) return value
  }
  return readTokenFromCookies()
}

function createCustomEvt(name, detail){
  try {
    return new CustomEvent(name, {detail})
  } catch (_) {
    const evt = document.createEvent('CustomEvent')
    evt.initCustomEvent(name, false, false, detail)
    return evt
  }
}

function emitSseEvent(phase, extra = {}){
  const detail = {...extra, phase}
  const targets = [window, document]
  for (const target of targets) {
    try {
      target.dispatchEvent(createCustomEvt('oq:sse', detail))
      target.dispatchEvent(createCustomEvt(`oq:sse:${phase}`, detail))
    } catch (_) {
      /* ignore dispatch failures */
    }
  }
}

function parseSseData(raw){
  if (raw == null) return raw
  if (typeof raw !== 'string') return raw
  const trimmed = raw.trim()
  if (!trimmed) return ''
  try {
    return JSON.parse(trimmed)
  } catch (_) {
    return raw
  }
}

function buildSseMeta(){
  const token = getStoredToken()
  try {
    const url = new URL(SSE_ENDPOINT, window.location.origin)
    if (token) url.searchParams.set('token', token)
    return {url: url.toString(), token: token || null}
  } catch (_) {
    if (token) {
      const sep = SSE_ENDPOINT.includes('?') ? '&' : '?'
      return {url: `${SSE_ENDPOINT}${sep}token=${encodeURIComponent(token)}`, token}
    }
    return {url: SSE_ENDPOINT, token: null}
  }
}

function closeSseSource(){
  if (!sseSource) return
  try { sseSource.close() } catch (_) { /* ignore */ }
  sseSource = null
}

function resetSseTimers(){
  if (sseReconnectTimer) {
    clearTimeout(sseReconnectTimer)
    sseReconnectTimer = null
  }
  sseScheduledDelay = null
}

function scheduleSseReconnect(reason, context = {}){
  if (!sseShouldReconnect || sseReconnectTimer) return
  const delay = Math.min(sseRetryDelay, SSE_RETRY_MAX)
  const detail = {...sseCurrentMeta, reason, delay, ...context}
  emitSseEvent('reconnecting', detail)
  sseScheduledDelay = delay
  sseReconnectTimer = setTimeout(() => {
    sseReconnectTimer = null
    connectSse()
  }, delay)
  sseRetryDelay = Math.min(sseRetryDelay * 2, SSE_RETRY_MAX)
}

function connectSse(){
  if (!sseShouldReconnect) return null
  if (typeof window === 'undefined' || !window.EventSource) {
    emitSseEvent('unsupported', {reason: 'no-eventsource'})
    return null
  }

  resetSseTimers()
  closeSseSource()

  const meta = buildSseMeta()
  sseCurrentMeta = {...meta}
  sseConnectAttempts += 1
  const connectionMeta = {...sseCurrentMeta, attempt: sseConnectAttempts}
  emitSseEvent('connecting', connectionMeta)

  try {
    sseSource = new EventSource(meta.url, {withCredentials: true})
  } catch (error) {
    emitSseEvent('error', {...connectionMeta, error})
    scheduleSseReconnect('constructor-error', {error})
    return null
  }

  sseSource.onopen = () => {
    sseRetryDelay = SSE_RETRY_BASE
    emitSseEvent('open', {...connectionMeta, source: sseSource})
  }

  sseSource.onmessage = (event) => {
    const data = parseSseData(event.data)
    const detail = {
      ...connectionMeta,
      source: sseSource,
      data,
      raw: event.data,
      lastEventId: event.lastEventId || null,
      event: event.type || 'message'
    }
    emitSseEvent('message', detail)
  }

  sseSource.onerror = (event) => {
    const detail = {
      ...connectionMeta,
      source: sseSource,
      error: event,
      readyState: sseSource?.readyState
    }
    emitSseEvent('error', detail)
    closeSseSource()
    scheduleSseReconnect('error', detail)
  }

  return sseSource
}

function restartSse(reason = 'manual-restart'){
  if (typeof window === 'undefined' || !window.EventSource) return
  sseShouldReconnect = true
  sseRetryDelay = SSE_RETRY_BASE
  resetSseTimers()
  emitSseEvent('reconnecting', {...sseCurrentMeta, reason, delay: 0})
  connectSse()
}

function stopSse(reason = 'manual-stop'){
  sseShouldReconnect = false
  resetSseTimers()
  closeSseSource()
  emitSseEvent('close', {...sseCurrentMeta, reason})
}

function handleTokenStorageChange(event){
  if (!event || !event.key) return
  const key = String(event.key).toLowerCase()
  if (!TOKEN_CANDIDATE_SET.has(key)) return
  const token = getStoredToken()
  if (token === sseCurrentMeta.token) return
  restartSse('token-changed')
}

if (typeof window !== 'undefined' && !window.__oqAdminSSE) {
  window.__oqAdminSSE = {
    reconnect: (reason) => restartSse(reason || 'manual-reconnect'),
    disconnect: (reason) => stopSse(reason || 'manual-stop'),
    connect: () => {
      sseShouldReconnect = true
      sseRetryDelay = SSE_RETRY_BASE
      return connectSse()
    },
    getToken: () => getStoredToken(),
    get source(){ return sseSource },
    get state(){
      return {
        connected: !!sseSource,
        retryDelay: sseScheduledDelay ?? sseRetryDelay,
        meta: {...sseCurrentMeta}
      }
    },
    get initialized(){ return sseInitialized }
  }
}

function initDashboardSse(){
  if (sseInitialized) return
  sseInitialized = true

  if (typeof window === 'undefined' || !window.EventSource) {
    emitSseEvent('unsupported', {reason: 'no-eventsource'})
    return
  }

  sseShouldReconnect = true
  sseRetryDelay = SSE_RETRY_BASE
  connectSse()

  window.addEventListener('storage', handleTokenStorageChange)
  window.addEventListener('beforeunload', () => stopSse('page-unload'))
}

async function api(path, opts = {}) {
  const token = getStoredToken()
  const headers = new Headers({'Accept': 'application/json'})
  if (opts.body && !(opts.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const method = (opts.method || 'GET').toUpperCase()
  if (!['GET', 'HEAD'].includes(method)) {
    let csrf = sessionStorage.getItem('csrf')
    if (!csrf) {
      const r = await fetch('/api/csrf', {headers, credentials: 'include', cache: 'no-store'})
      csrf = r.headers.get('X-CSRF-Token')
      if (csrf) sessionStorage.setItem('csrf', csrf)
    }
    if (csrf) headers.set('X-CSRF-Token', csrf)
  }

  const res = await fetch(path, {...opts, headers, credentials: 'include', cache: 'no-store'})
  if (res.status === 401) {
    toast('Oturum gerekli. Lütfen giriş yapın.', true)
    throw new Error('Unauthorized')
  }
  if (res.status === 304) {
    return {notModified: true}
  }
  if (!res.ok) {
    let msg = res.statusText
    try {
      const j = await res.json()
      msg = j.message || j.detail || j.error || msg
    } catch (_) {
      /* ignore */
    }
    throw new Error(msg)
  }
  return res.json()
}

function $(sel){ return document.querySelector(sel) }
function $$(sel){ return Array.from(document.querySelectorAll(sel)) }

function toast(message, isError=false){
  const t = $('#toast')
  if (!t) return
  t.textContent = message
  t.classList.toggle('err', !!isError)
  t.hidden = false
  setTimeout(() => { t.hidden = true }, 3000)
}

function toCSV(rows) {
  if (!rows || !rows.length) return ''
  const keys = Object.keys(rows[0])
  const esc = v => `"${String(v ?? '').replaceAll('"','""')}"`
  return [keys.join(','), ...rows.map(r => keys.map(k => esc(r[k])).join(','))].join('\n')
}

const state = {
  page: 1,
  per_page: 25,
  plan: '',
  search: '',
  sort: 'created_at:desc',
  total: 0,
  items: [],
}

function setBusy(on){
  $('#app')?.setAttribute('aria-busy', on ? 'true' : 'false')
  $('#status').textContent = on ? 'Yükleniyor…' : 'Hazır'
}

function renderUsers() {
  const tbody = $('#usersBody')
  if (!tbody) return
  tbody.innerHTML = ''

  if (!state.items.length) {
    const tr = document.createElement('tr')
    const td = document.createElement('td')
    td.colSpan = 5
    td.className = 'muted'
    td.textContent = 'Kayıt bulunamadı.'
    tr.appendChild(td)
    tbody.appendChild(tr)
    return
  }

  for (const u of state.items) {
    const tr = document.createElement('tr')

    const planTag = document.createElement('span')
    const planName = (u.plan || 'free').toLowerCase()
    planTag.className = `tag ${planName}`
    planTag.textContent = planName.toUpperCase()

    const tdId = document.createElement('td')
    tdId.textContent = u.id

    const tdEmail = document.createElement('td')
    tdEmail.textContent = u.email || ''

    const tdPlan = document.createElement('td')
    tdPlan.appendChild(planTag)

    const tdCreated = document.createElement('td')
    tdCreated.textContent = u.created_at ? new Date(u.created_at).toLocaleString() : ''

    const tdAct = document.createElement('td')
    tdAct.className = 'right'

    const btn = document.createElement('button')
    btn.textContent = 'Premium Yap'
    btn.addEventListener('click', async () => {
      try {
        btn.disabled = true
        await api(`${API_ROOT}/users/${u.id}/plan`, {
          method: 'PATCH',
          body: JSON.stringify({plan: 'premium'})
        })
        toast(`#${u.id} premium yapıldı`)
        u.plan = 'premium'
        renderUsers()
      } catch (err) {
        toast(err.message || 'İşlem başarısız', true)
      } finally {
        btn.disabled = false
      }
    })

    tdAct.appendChild(btn)

    tr.appendChild(tdId)
    tr.appendChild(tdEmail)
    tr.appendChild(tdPlan)
    tr.appendChild(tdCreated)
    tr.appendChild(tdAct)

    tbody.appendChild(tr)
  }

  $('#pageState').textContent = `Sayfa ${state.page} — Toplam ${state.total}`
}

async function fetchUsers(){
  setBusy(true)
  try {
    const url = new URL(`${API_ROOT}/users`, window.location.origin)
    url.searchParams.set('page', state.page)
    url.searchParams.set('per_page', state.per_page)
    if (state.plan) url.searchParams.set('plan', state.plan)
    if (state.search) url.searchParams.set('search', state.search)
    url.searchParams.set('sort', state.sort)

    const data = await api(url.toString())
    if (data?.notModified) {
      setBusy(false)
      return
    }

    state.items = data.items || []
    state.total = data.total || 0
    state.page = data.page || state.page
    state.per_page = data.per_page || state.per_page
    renderUsers()
  } catch (err) {
    toast(err.message || 'Yükleme hatası', true)
  } finally {
    setBusy(false)
  }
}

function bindUI(){
  $('#refresh')?.addEventListener('click', () => {
    state.page = 1
    fetchUsers()
  })

  $('#exportCsv')?.addEventListener('click', () => {
    const csv = toCSV(state.items)
    const blob = new Blob([csv], {type: 'text/csv'})
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `users_page${state.page}.csv`
    a.click()
  })

  $('#prev')?.addEventListener('click', () => {
    if (state.page > 1) {
      state.page -= 1
      fetchUsers()
    }
  })

  $('#next')?.addEventListener('click', () => {
    const maxPage = Math.ceil((state.total || 0) / state.per_page)
    if (state.page < maxPage) {
      state.page += 1
      fetchUsers()
    }
  })

  $('#plan')?.addEventListener('change', (e) => {
    state.plan = e.target.value
    state.page = 1
    fetchUsers()
  })

  let searchTimer
  $('#search')?.addEventListener('input', (e) => {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      state.search = e.target.value.trim()
      state.page = 1
      fetchUsers()
    }, 300)
  })
}

document.addEventListener('DOMContentLoaded', () => {
  bindUI()
  fetchUsers()
  initDashboardSse()
})
