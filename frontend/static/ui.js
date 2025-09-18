// Basit, erişilebilir loading & toast & güvenli fetch yardımcıları
(function () {
  const spinner = document.createElement('div');
  spinner.id = 'global-spinner';
  spinner.style.cssText = `
    position:fixed;inset:0;display:none;align-items:center;justify-content:center;
    background:rgba(0,0,0,.35);z-index:9999;color:#fff;font:16px/1.4 system-ui,sans-serif
  `;
  spinner.innerHTML = '<div role="status" aria-live="polite">Yükleniyor...</div>';
  document.addEventListener('DOMContentLoaded', () => document.body.appendChild(spinner));

  window.UI = {
    showLoading() { spinner.style.display = 'flex'; },
    hideLoading() { spinner.style.display = 'none'; },
    toast(msg, ok=true) {
      const el = document.createElement('div');
      el.setAttribute('role','status');
      el.style.cssText = `
        position:fixed;right:16px;bottom:16px;background:${ok?'#16a34a':'#b91c1c'};
        color:#fff;padding:12px 14px;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:9999
      `;
      el.textContent = msg;
      document.body.appendChild(el);
      setTimeout(()=>el.remove(), 3200);
    },
    async fetchWithStatus(input, init={}) {
      try {
        UI.showLoading();
        const res = await fetch(input, init);
        if (!res.ok) {
          const text = await res.text();
          UI.toast(`Hata: ${res.status} ${text.slice(0,80)}`, false);
          throw new Error(`HTTP ${res.status}`);
        }
        return res;
      } catch (e) {
        console.error(e);
        throw e;
      } finally {
        UI.hideLoading();
      }
    }
  };
})();
