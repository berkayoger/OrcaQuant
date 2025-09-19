'use strict'

const API_ROOT = '/api/admin/dashboard'

async function api(path, opts = {}) {
  const token = localStorage.getItem('jwt')
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
})
