import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '../hooks/useAppSelector';
import type { ProtectedRouteProps } from '../types';

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredSubscription 
}) => {
  const { isAuthenticated, user, isLoading } = useAppSelector(state => state.auth);
  const location = useLocation();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loader"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check subscription level if required
  if (requiredSubscription) {
    const subscriptionLevels = ['trial', 'basic', 'premium', 'enterprise'];
    const userLevel = subscriptionLevels.indexOf(user.subscription_level);
    const requiredLevel = subscriptionLevels.indexOf(requiredSubscription);

    if (userLevel < requiredLevel) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="card p-8 max-w-md text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">
              Erişim Engellendi
            </h2>
            <p className="text-gray-600 mb-4">
              Bu özelliği kullanmak için {requiredSubscription} veya üzeri bir aboneliğe sahip olmanız gerekiyor.
            </p>
            <p className="text-sm text-gray-500">
              Mevcut aboneliğiniz: <span className="font-semibold">{user.subscription_level}</span>
            </p>
            <button 
              onClick={() => window.location.href = '/abonelik'}
              className="btn-base btn-gradient mt-4"
            >
              Aboneliği Yükselt
            </button>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;