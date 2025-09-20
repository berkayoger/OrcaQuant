# Admin Batch UI

Yeni admin sayfası:

- Route: `/admin/batch`
- Form alanları: asset, timeframe, limit, symbols (textarea)
- Progress bar: status polling `/api/draks/batch/status/{jobId}`
- Result listesi: `/api/draks/batch/results/{jobId}` filtreleriyle

Giriş için JWT + (opsiyonel) API key gereklidir.

## Gerçek zamanlı yönetim akışı

- `/assets/admin.js` otomatik olarak `/api/admin/dashboard/stream` uç noktasına bir Server-Sent Events (SSE) bağlantısı açar.
- Bağlantı oluşturulurken erişim jetonu sırasıyla `localStorage`, `sessionStorage` ve çerezlerden okunur ve `?token=` parametresi olarak URL'ye eklenir.
- Bağlantı durumu ve gelen veriler `oq:sse`, `oq:sse:open`, `oq:sse:message`, `oq:sse:error`, `oq:sse:reconnecting` ve `oq:sse:close` özel olaylarıyla yayınlanır; dinleyiciler hem `window` hem de `document` üzerinde çalışır.
- Hata durumunda bağlantı 1 saniyeden başlayıp 30 saniyeye kadar artan aralıklarla otomatik olarak yeniden denenir ve jeton değişikliklerinde bağlantı yeniden başlatılır.
- `window.__oqAdminSSE` denetleyicisi elle yeniden bağlanma (`reconnect()`), bağlantıyı kesme (`disconnect()`) ve anlık durum (`state`) sorguları için kullanılabilir.
