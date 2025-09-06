import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAppDispatch } from './hooks/useAppDispatch';
import { useAppSelector } from './hooks/useAppSelector';
import { checkAuthAsync } from './store/slices/authSlice';

// Components
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import NotificationManager from './components/NotificationManager';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Predictions from './pages/Predictions';

// Loading component
const LoadingScreen: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="loader mx-auto mb-4"></div>
      <p className="text-gray-600">Yükleniyor...</p>
    </div>
  </div>
);

// Not found component
const NotFound: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
      <p className="text-gray-600 mb-8">Aradığınız sayfa bulunamadı</p>
      <a 
        href="/" 
        className="btn-base btn-gradient text-decoration-none"
      >
        Ana Sayfaya Dön
      </a>
    </div>
  </div>
);

const App: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, isLoading } = useAppSelector(state => state.auth);

  useEffect(() => {
    // Check if user is authenticated when app starts
    dispatch(checkAuthAsync());
  }, [dispatch]);

  // Show loading screen while checking authentication
  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <div className="App">
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        
        {/* Protected routes with layout */}
        <Route path="/" element={<Layout />}>
          <Route 
            index 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="predictions" 
            element={
              <ProtectedRoute>
                <Predictions />
              </ProtectedRoute>
            } 
          />
          
          {/* Premium features - require higher subscription */}
          <Route 
            path="analytics" 
            element={
              <ProtectedRoute requiredSubscription="premium">
                <div className="text-center py-8">
                  <h1 className="text-2xl font-bold mb-4">Gelişmiş Analitik</h1>
                  <p className="text-gray-600">Bu özellik yakında eklenecek.</p>
                </div>
              </ProtectedRoute>
            } 
          />
          
          {/* Enterprise features */}
          <Route 
            path="api-access" 
            element={
              <ProtectedRoute requiredSubscription="enterprise">
                <div className="text-center py-8">
                  <h1 className="text-2xl font-bold mb-4">API Erişimi</h1>
                  <p className="text-gray-600">Bu özellik yakında eklenecek.</p>
                </div>
              </ProtectedRoute>
            } 
          />
          
          {/* Redirects for legacy URLs */}
          <Route path="index.html" element={<Navigate to="/" replace />} />
          <Route path="giris.html" element={<Navigate to="/login" replace />} />
          <Route path="prediction-display.html" element={<Navigate to="/predictions" replace />} />
          <Route path="dashboard.html" element={<Navigate to="/dashboard" replace />} />
          
          {/* 404 for protected routes */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
      
      {/* Global notification manager */}
      <NotificationManager />
    </div>
  );
};

export default App;