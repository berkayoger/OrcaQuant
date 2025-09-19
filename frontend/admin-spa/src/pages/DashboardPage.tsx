import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useAuthStore } from '../store/auth'
import { api } from '../lib/axios'

type DashboardMetrics = {
  users: { active: number; new: number; total: number }
  revenue: { total: number; monthly: number }
  predictions: { count: number; accuracy: number }
  system: { cpu: number; memory: number; uptime: string }
}

type Activity = { id: string; description: string; timestamp: string }

type GrowthPoint = { date: string; users: number }

export default function DashboardPage() {
  const isSession = useAuthStore((state) => state.isSession)
  const loadMe = useAuthStore((state) => state.loadMe)
  const nav = useNavigate()

  useEffect(() => {
    if (!isSession) {
      loadMe().catch(() => nav('/login'))
    }
  }, [isSession, loadMe, nav])

  const { data: metrics } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => (await api.get<DashboardMetrics>('/admin/analytics/dashboard')).data,
    refetchInterval: 30_000
  })

  const { data: chartData } = useQuery({
    queryKey: ['user-growth-chart'],
    queryFn: async () => (await api.get<GrowthPoint[]>('/admin/analytics/user-growth')).data,
    staleTime: 60_000
  })

  const { data: activities } = useQuery({
    queryKey: ['recent-activities'],
    queryFn: async () => (await api.get<Activity[]>('/admin/activities/recent')).data,
    refetchInterval: 10_000
  })

  return (
    <div className="p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-neutral-400">Son 24 saatteki önemli metrikler</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Aktif Kullanıcılar" value={metrics?.users.active ?? 0} />
        <MetricCard title="Yeni Kayıtlar" value={metrics?.users.new ?? 0} />
        <MetricCard
          title="Toplam Gelir"
          value={(metrics?.revenue.total ?? 0).toLocaleString('en-US', {
            style: 'currency',
            currency: 'USD'
          })}
        />
        <MetricCard title="Tahmin Doğruluğu" value={`${metrics?.predictions.accuracy ?? 0}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-medium mb-4">Kullanıcı Büyümesi</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData || []}>
                <XAxis dataKey="date" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ background: '#111827', border: '1px solid #1f2937', color: '#f9fafb' }}
                />
                <Line type="monotone" dataKey="users" stroke="#60a5fa" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h3 className="font-medium mb-4">Sistem Durumu</h3>
          <div className="space-y-3">
            <SystemMetric label="CPU" value={metrics?.system.cpu ?? 0} unit="%" />
            <SystemMetric label="RAM" value={metrics?.system.memory ?? 0} unit="%" />
            <div className="flex justify-between">
              <span>Uptime</span>
              <span className="text-green-400">{metrics?.system.uptime || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="font-medium mb-4">Son Aktiviteler</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {(activities || []).map((activity) => (
            <div key={activity.id} className="flex items-center gap-3 p-2 rounded bg-neutral-800/50">
              <div className="w-2 h-2 bg-blue-500 rounded-full" />
              <div className="flex-1">
                <span className="text-sm">{activity.description}</span>
                <div className="text-xs text-neutral-400">{activity.timestamp}</div>
              </div>
            </div>
          ))}
          {(!activities || activities.length === 0) && (
            <div className="text-sm text-neutral-400">Kayıt bulunamadı.</div>
          )}
        </div>
      </div>
    </div>
  )
}

type MetricCardProps = { title: string; value: string | number }

function MetricCard({ title, value }: MetricCardProps) {
  return (
    <div className="card">
      <h3 className="text-sm text-neutral-400 mb-1">{title}</h3>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  )
}

type SystemMetricProps = { label: string; value: number; unit: string }

function SystemMetric({ label, value, unit }: SystemMetricProps) {
  const color = value > 80 ? 'bg-red-500' : value > 60 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center justify-between">
      <span>{label}</span>
      <div className="flex items-center gap-2">
        <div className="w-24 bg-neutral-700 rounded-full h-2">
          <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
        </div>
        <span className="text-sm w-12 text-right">
          {value}
          {unit}
        </span>
      </div>
    </div>
  )
}
