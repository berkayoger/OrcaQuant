import { Suspense } from 'react'
import { AppRoutes } from './routes/AppRoutes'
import { Toaster } from 'react-hot-toast'
import { useNotifications } from './lib/notifications'

export default function App() {
  useNotifications()

  return (
    <>
      <Suspense fallback={<div className="p-6">Yükleniyor…</div>}>
        <AppRoutes />
      </Suspense>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#1f2937', color: '#fff', border: '1px solid #374151' }
        }}
      />
    </>
  )
}
