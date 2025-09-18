// Real-time bildirimler: Socket.IO varsa onu kullan, yoksa EventSource veya no-op
(function () {
  function onMsg(title, body) {
    if (window.UI) UI.toast(`${title}: ${body}`, true);
    else console.log(title, body);
  }
  function trySocketIO() {
    if (!window.io) return false;
    const s = window.io({transports:['websocket','polling']});
    s.on('connect', ()=>onMsg('RT', 'bağlandı'));
    s.on('notice', (data)=>onMsg('Bildirim', (data && data.message) || 'Mesaj'));
    s.on('disconnect', ()=>onMsg('RT', 'koptu'));
    return true;
  }
  function trySSE() {
    if (!window.EventSource) return false;
    try {
      const es = new EventSource('/api/stream');
      es.onmessage = (ev)=>onMsg('SSE', ev.data);
      es.onerror   = ()=>onMsg('SSE', 'bağlantı hatası');
      return true;
    } catch { return false; }
  }
  document.addEventListener('DOMContentLoaded', () => {
    if (trySocketIO()) return;
    if (trySSE()) return;
    console.log('Real-time altyapısı devre dışı');
  });
})();
