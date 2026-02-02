import { Link } from 'react-router-dom';
import { SubscriptionCard } from '@/components/SubscriptionCard';

const plans = [
  {
    title: 'Başlangıç',
    price: '$29',
    description: 'Bireysel yatırımcılar için temel sinyaller.',
    features: ['Günlük 10 tahmin', 'Temel portföy analizi', 'E-posta bildirimleri'],
    ctaLabel: 'Başla',
  },
  {
    title: 'Profesyonel',
    price: '$79',
    description: 'Aktif traderlar için gelişmiş modeller.',
    features: ['Sınırsız tahmin', 'Gerçek zamanlı fiyat akışı', 'Gelişmiş risk raporları'],
    ctaLabel: 'Yükselt',
    highlighted: true,
  },
  {
    title: 'Kurumsal',
    price: '$199',
    description: 'Ekipler için API erişimi ve özel destek.',
    features: ['Çoklu kullanıcı', 'Özel entegrasyonlar', 'Öncelikli destek'],
    ctaLabel: 'Satış ile görüş',
  },
] as const;

export const HomePage = (): JSX.Element => (
  <div className="space-y-16">
    <section className="grid gap-8 lg:grid-cols-2 lg:items-center">
      <div className="space-y-6">
        <span className="rounded-full bg-accent/10 px-4 py-1 text-xs font-semibold uppercase tracking-widest text-accent">
          OrcaQuant AI Platformu
        </span>
        <h1 className="text-4xl font-extrabold leading-tight text-white sm:text-5xl">
          Yapay zeka destekli piyasa öngörüleri ile karar hızınızı artırın.
        </h1>
        <p className="text-lg text-slate-300">
          OrcaQuant, kurumsal düzeyde makine öğrenimi modelleri ile hisse ve kripto piyasasında
          gerçek zamanlı tahminler sunar. Riskinizi yönetin, fırsatları yakalayın.
        </p>
        <div className="flex flex-wrap gap-4">
          <Link
            to="/register"
            className="rounded-xl bg-accent px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-400"
          >
            Ücretsiz dene
          </Link>
          <Link
            to="/dashboard"
            className="rounded-xl border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-accent/60 hover:text-white"
          >
            Canlı demoyu izle
          </Link>
        </div>
      </div>
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl">
        <p className="text-sm uppercase tracking-widest text-slate-400">Performans Özeti</p>
        <div className="mt-6 grid grid-cols-2 gap-6 text-white">
          <div>
            <p className="text-3xl font-bold">92%</p>
            <p className="text-sm text-slate-400">Model doğruluk oranı</p>
          </div>
          <div>
            <p className="text-3xl font-bold">+18%</p>
            <p className="text-sm text-slate-400">Ortalama portföy getirisi</p>
          </div>
          <div>
            <p className="text-3xl font-bold">120k</p>
            <p className="text-sm text-slate-400">Canlı fiyat güncellemesi</p>
          </div>
          <div>
            <p className="text-3xl font-bold">45</p>
            <p className="text-sm text-slate-400">Desteklenen piyasa</p>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2 className="text-3xl font-bold text-white">Planlar</h2>
      <p className="mt-2 max-w-2xl text-slate-400">
        İster bireysel ister kurumsal olun, portföyünüzü büyütmeniz için ihtiyacınız olan araçları
        sağlıyoruz.
      </p>
      <div className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {plans.map((plan) => (
          <SubscriptionCard key={plan.title} {...plan} />
        ))}
      </div>
    </section>

    <section className="grid gap-10 lg:grid-cols-3">
      <div className="lg:col-span-2 space-y-4">
        <h3 className="text-2xl font-semibold text-white">Neden OrcaQuant?</h3>
        <ul className="space-y-3 text-slate-300">
          <li>• Dakikalar içinde gerçeğe yakın fiyat tahminleri alın.</li>
          <li>• API ile mevcut altyapınıza kolayca entegre edin.</li>
          <li>• Gelişmiş risk yönetimi ve portföy simülasyonları.</li>
        </ul>
      </div>
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 text-slate-300">
        <p className="text-sm uppercase tracking-widest text-slate-400">Veri Güvenliği</p>
        <p className="mt-3 text-sm">
          Tüm verileriniz SOC2 uyumlu altyapımızda şifreli olarak saklanır. İki faktörlü kimlik
          doğrulama ve IP kısıtlama özellikleriyle hesabınızı güvene alırsınız.
        </p>
      </div>
    </section>
  </div>
);
