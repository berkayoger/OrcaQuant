import React, { useState, useEffect } from 'react';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { addNotification } from '../store/slices/appSlice';
import { apiClient } from '../services/api';
import { TrendingUp, TrendingDown, Filter, RefreshCw } from 'lucide-react';
import type { Prediction, PredictionFilters, TechnicalAnalysis } from '../types';

const Predictions: React.FC = () => {
  const dispatch = useAppDispatch();
  
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [technicalAnalysis, setTechnicalAnalysis] = useState<TechnicalAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<'buy' | 'hold'>('buy');
  const [filters, setFilters] = useState<PredictionFilters>({
    page: 1,
    per_page: 20
  });

  useEffect(() => {
    loadPredictions();
    loadTechnicalAnalysis();
  }, [filters]);

  const loadPredictions = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getPredictions(filters);
      setPredictions(data.items || []);
    } catch (error: any) {
      dispatch(addNotification({
        message: 'Tahminler yüklenirken hata oluştu',
        type: 'error'
      }));
      console.error('Predictions loading error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTechnicalAnalysis = async () => {
    try {
      const data = await apiClient.getTechnicalAnalysis();
      setTechnicalAnalysis(data);
    } catch (error) {
      console.warn('Technical analysis not available:', error);
    }
  };

  const handleFilterChange = (field: keyof PredictionFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      page: 1 // Reset to first page when filters change
    }));
  };

  const handleRefresh = () => {
    loadPredictions();
    loadTechnicalAnalysis();
  };

  const getFilteredPredictions = () => {
    if (activeFilter === 'buy') {
      return predictions.filter(p => p.expected_gain_pct >= 10);
    }
    return predictions.filter(p => p.expected_gain_pct < 10);
  };

  const filteredPredictions = getFilteredPredictions();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Tahmin Fırsatları</h1>
            <p className="text-gray-600">
              Güncel kripto para tahminleri ve analizler
            </p>
          </div>
          <button
            onClick={handleRefresh}
            className="btn-base bg-blue-600 text-white hover:bg-blue-700 flex items-center space-x-2"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Yenile</span>
          </button>
        </div>
      </div>

      {/* Technical Analysis Summary */}
      {technicalAnalysis && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">📊 Teknik Analiz Özeti</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="font-medium text-gray-600">BTC RSI:</span>
              <span className="font-semibold">{technicalAnalysis.rsi}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium text-gray-600">MACD:</span>
              <span className="font-semibold">{technicalAnalysis.macd}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium text-gray-600">Signal:</span>
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
          <p className="text-xs text-gray-500 mt-2">
            Son güncelleme: {new Date(technicalAnalysis.created_at).toLocaleString('tr-TR')}
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Trend Type Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <select
              value={filters.trend_type || ''}
              onChange={(e) => handleFilterChange('trend_type', e.target.value || undefined)}
              className="input-field text-sm"
            >
              <option value="">Tüm Trendler</option>
              <option value="bullish">Yükseliş</option>
              <option value="bearish">Düşüş</option>
              <option value="neutral">Nötr</option>
            </select>
          </div>

          {/* Confidence Filter */}
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Min Güven:</label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="1"
              value={filters.min_confidence || ''}
              onChange={(e) => handleFilterChange('min_confidence', e.target.value ? parseFloat(e.target.value) : undefined)}
              className="input-field w-24 text-sm"
              placeholder="0.5"
            />
          </div>

          <button
            onClick={loadPredictions}
            className="btn-base bg-indigo-600 text-white hover:bg-indigo-700 text-sm px-4 py-2"
          >
            Uygula
          </button>
        </div>
      </div>

      {/* Strategic Predictions Tabs */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b border-gray-200">
          <div className="p-6 pb-0">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">📊 Stratejik Tahminler</h2>
            <div className="flex space-x-2 mb-4">
              <button
                className={`
                  tab-button px-4 py-2 text-sm font-medium rounded-md border transition-colors
                  ${activeFilter === 'buy'
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'}
                `}
                onClick={() => setActiveFilter('buy')}
              >
                <TrendingUp className="h-4 w-4 inline mr-1" />
                📈 Yükselenler
              </button>
              <button
                className={`
                  tab-button px-4 py-2 text-sm font-medium rounded-md border transition-colors
                  ${activeFilter === 'hold'
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'}
                `}
                onClick={() => setActiveFilter('hold')}
              >
                <TrendingDown className="h-4 w-4 inline mr-1" />
                🤝 Tutulması Önerilenler
              </button>
            </div>
          </div>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="loader"></div>
            </div>
          ) : filteredPredictions.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredPredictions.map((prediction) => (
                <div key={prediction.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-bold text-indigo-700">
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
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-600">Beklenen Getiri:</span>
                      <span className="font-semibold text-green-600">%{prediction.expected_gain_pct}</span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-600">Hedef Fiyat:</span>
                      <span className="font-semibold">${prediction.target_price}</span>
                    </div>
                    
                    {prediction.expected_gain_days && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-600">Getiri Süresi:</span>
                        <span className="font-semibold">{prediction.expected_gain_days} gün</span>
                      </div>
                    )}
                    
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-600">Güven:</span>
                      <span className="font-semibold">
                        %{Math.round((prediction.confidence || prediction.confidence_score) * 100)}
                      </span>
                    </div>
                    
                    {prediction.status && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-600">Durum:</span>
                        <span className={`
                          font-semibold capitalize
                          ${prediction.status === 'active' ? 'text-blue-600' :
                            prediction.status === 'completed' ? 'text-green-600' :
                            'text-gray-600'}
                        `}>
                          {prediction.status}
                        </span>
                      </div>
                    )}
                    
                    {prediction.remaining_time && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-600">Kalan Süre:</span>
                        <span className="font-semibold">{prediction.remaining_time}</span>
                      </div>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 mt-3 p-3 bg-gray-50 rounded">
                    {prediction.description}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">
                {activeFilter === 'buy' ? 'Yükselen tahmin bulunamadı' : 'Tutulması önerilen tahmin bulunamadı'}
              </p>
              <p className="text-sm">Filtrelerinizi değiştirerek daha fazla sonuç görebilirsiniz</p>
            </div>
          )}
        </div>
      </div>

      {/* Predictions Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Tüm Tahminler</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full table-auto">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sembol</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trend</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hedef Fiyat</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Beklenen Getiri %</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Güven %</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Durum</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Açıklama</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {predictions.map((prediction) => (
                <tr key={prediction.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {prediction.symbol}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <span className={`
                      inline-flex px-2 py-1 text-xs font-semibold rounded-full
                      ${prediction.trend_type === 'bullish' ? 'bg-green-100 text-green-800' :
                        prediction.trend_type === 'bearish' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'}
                    `}>
                      {prediction.trend_type || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${prediction.target_price}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                    %{prediction.expected_gain_pct}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                    %{Math.round((prediction.confidence || prediction.confidence_score) * 100)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <span className={`
                      inline-flex px-2 py-1 text-xs font-semibold rounded-full capitalize
                      ${prediction.status === 'active' ? 'bg-blue-100 text-blue-800' :
                        prediction.status === 'completed' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'}
                    `}>
                      {prediction.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600 max-w-xs truncate">
                    {prediction.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Predictions;