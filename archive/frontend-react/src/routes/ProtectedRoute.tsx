import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface ProtectedRouteProps {
  requireAdmin?: boolean;
  children?: JSX.Element;
}

export const ProtectedRoute = ({ requireAdmin = false, children }: ProtectedRouteProps): JSX.Element => {
  const location = useLocation();
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);

  if (!hasHydrated) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  if (children) {
    return children;
  }

  return <Outlet />;
};
