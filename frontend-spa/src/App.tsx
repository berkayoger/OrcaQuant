import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import { useAuthStore } from './store/auth';
import LoadingSpinner from './components/ui/LoadingSpinner';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Portfolio = lazy(() => import('./pages/Portfolio'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Subscription = lazy(() => import('./pages/Subscription'));
const AdminLayout = lazy(() => import('./pages/Admin/AdminLayout'));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="subscription" element={<Subscription />} />
          <Route path="admin/*" element={<AdminLayout />} />
        </Route>
        
        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
