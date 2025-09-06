import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { addNotification } from '../store/slices/appSlice';
import { apiClient } from '../services/api';
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';
import type { Prediction, TechnicalAnalysis } from '../types';

const Dashboard: React.FC = () => {
  const { user } = useAppSelector(state => state.auth);
  const dispatch = useAppDispatch();
  
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [technicalAnalysis, setTechnicalAnalysis] = useState<TechnicalAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load recent predictions
      const predictionsData = await apiClient.getPredictions({ 
        page: 1, 
        per_page: 6 
      });
      setPredictions(predictionsData.items || []);
      
      // Load technical analysis
      try {
        const taData = await apiClient.getTechnicalAnalysis();
        setTechnicalAnalysis(taData);
      } catch (error) {
        console.warn('Technical analysis not available:', error);
      }
      
    } catch (error: any) {
      dispatch(addNotification({
        message: 'Dashboard verilerini yüklerken hata oluştu',
        type: 'error'
      }));
      console.error('Dashboard loading error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSubscriptionFeatures = () => {
    const level = user?.subscription_level;
    switch (level) {
      case 'enterprise':
        return {
          predictionsLimit: 'Sınırsız',
          analysisAccess: 'Gelişmiş AI Analizi',
          features: ['Gerçek zamanlı uyarılar', 'API erişimi', 'Özel raporlar', 'Öncelikli destek']
        };
      case 'premium':
        return {
          predictionsLimit: '50/gün',
          analysisAccess: 'Premium Analiz',
          features: ['Gelişmiş tahminler', 'Teknik analiz', 'Portfolio takibi']
        };
      case 'basic':
        return {
          predictionsLimit: '20/gün',
          analysisAccess: 'Temel Analiz',
          features: ['Temel tahminler', 'Günlük özetler']
        };
      default:
        return {
          predictionsLimit: '5/gün',
          analysisAccess: 'Deneme Sürümü',
          features: ['Sınırlı tahminler', '7 günlük erişim']
        };
    }
  };

  const subscriptionInfo = getSubscriptionFeatures();

  const topPredictions = predictions.slice(0, 3);
  const bullishCount = predictions.filter(p => p.trend_type === 'bullish').length;
  const bearishCount = predictions.filter(p => p.trend_type === 'bearish').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="loader"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Hoş Geldiniz, {user?.username}!
        </h1>
        <p className="text-gray-600">
          OrcaQuant analiz panonuza hoş geldiniz. Güncel kripto para tahminlerinizi burada görebilirsiniz.
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Aktif Tahminler</p>
              <p className="text-2xl font-bold text-gray-900">{predictions.length}</p>
            </div>
            <Activity className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Yükselen</p>
              <p className="text-2xl font-bold text-green-600">{bullishCount}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Düşen</p>
              <p className="text-2xl font-bold text-red-600">{bearishCount}</p>
            </div>
            <TrendingDown className="h-8 w-8 text-red-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Günlük Limit</p>
              <p className="text-2xl font-bold text-blue-600">{subscriptionInfo.predictionsLimit}</p>
            </div>
            <DollarSign className="h-8 w-8 text-blue-600" />
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Predictions */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Son Tahminler</h2>
            <p className="text-sm text-gray-600">En güncel kripto para tahminleriniz</p>
          </div>
          <div className="p-6">
            {topPredictions.length > 0 ? (
              <div className="space-y-4">
                {topPredictions.map((prediction) => (
                  <div key={prediction.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {prediction.symbol}
                      </h3>
                      <span className={`
                        px-2 py-1 rounded-full text-xs font-semibold uppercase
                        ${prediction.trend_type === 'bullish' ? 'bg-green-100 text-green-800' :
                          prediction.trend_type === 'bearish' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'}
                      `}>
                        {prediction.trend_type}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Hedef:</span>
                        <p className="font-semibold">${prediction.target_price}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Beklenen:</span>
                        <p className="font-semibold text-green-600">
                          %{prediction.expected_gain_pct}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Güven:</span>
                        <p className="font-semibold">
                          %{Math.round((prediction.confidence || prediction.confidence_score) * 100)}
                        </p>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm mt-2">{prediction.description}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Activity className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Henüz tahmin bulunmuyor</p>
                <p className="text-sm">Yeni tahminler için lütfen bekleyin</p>
              </div>
            )}
          </div>
        </div>

        {/* Technical Analysis & Subscription Info */}
        <div className="space-y-6">
          {/* Technical Analysis */}
          {technicalAnalysis && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Teknik Analiz</h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">BTC RSI:</span>
                  <span className="font-semibold">{technicalAnalysis.rsi}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">MACD:</span>
                  <span className="font-semibold">{technicalAnalysis.macd}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Sinyal:</span>
                  <span className={`
                    font-semibold
                    ${technicalAnalysis.signal === 'BUY' ? 'text-green-600' :
                      technicalAnalysis.signal === 'SELL' ? 'text-red-600' :
                      'text-gray-600'}
                  `}>
                    {technicalAnalysis.signal}
                  </span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-4">
                Son güncelleme: {new Date(technicalAnalysis.created_at).toLocaleString('tr-TR')}
              </p>
            </div>
          )}

          {/* Subscription Info */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Abonelik Bilgileri</h2>
            <div className="space-y-4">
              <div>
                <span className="text-sm text-gray-600">Mevcut Plan:</span>
                <p className="font-semibold text-lg capitalize">{user?.subscription_level}</p>
              </div>
              
              <div>
                <span className="text-sm text-gray-600">Günlük Limit:</span>
                <p className="font-semibold">{subscriptionInfo.predictionsLimit}</p>
              </div>

              <div>
                <span className="text-sm text-gray-600">Özellikler:</span>
                <ul className="text-sm space-y-1 mt-1">
                  {subscriptionInfo.features.map((feature, index) => (
                    <li key={index} className="flex items-center">
                      <span className="w-1 h-1 bg-blue-600 rounded-full mr-2"></span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              {user?.subscription_level === 'trial' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                  <p className="text-yellow-800 text-sm font-medium">
                    {user.trial_remaining_days} gün deneme süresi kaldı
                  </p>
                  <button 
                    onClick={() => window.location.href = '/abonelik'}
                    className="text-yellow-600 hover:text-yellow-800 text-sm underline mt-1"
                  >
                    Aboneliği yükselt
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;