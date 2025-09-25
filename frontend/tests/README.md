# Frontend test notları

## Admin SSE davranışı

- `frontend/assets/admin.js`, admin paneli yüklendiğinde `/api/admin/dashboard/stream` için bir `EventSource` başlatır.
- Testlerde bu modül yükleniyorsa `window.EventSource` ve `CustomEvent` nesnelerini stub'lamak veya `oq:sse` olaylarını dinlemek gerekir. Her olay, hem `window` hem de `document` üzerinde `oq:sse` ve aşama bazlı (`oq:sse:open`, `oq:sse:message`, vb.) olarak yayınlanır.
- SSE istemcisi jetonu `localStorage` → `sessionStorage` → çerez sırası ile çözümler ve `?token=` parametresi olarak ekler; hata durumlarında bağlantı 1–30 saniye aralığında artan gecikmelerle yeniden kurulur. Bu davranış, testlerde beklenen yan etkileri (ör. yeniden bağlanma sayaçları) simüle etmek için dikkate alınmalıdır.
