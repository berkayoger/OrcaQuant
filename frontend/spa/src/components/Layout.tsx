import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { logoutAsync } from '../store/slices/authSlice';
import { LogOut, User, BarChart3 } from 'lucide-react';

const Layout: React.FC = () => {
  const { user, isAuthenticated } = useAppSelector(state => state.auth);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await dispatch(logoutAsync());
    navigate('/login');
  };

  if (!isAuthenticated) {
    return <Outlet />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo and main nav */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <BarChart3 className="h-8 w-8 text-blue-600" />
                <span className="text-xl font-bold text-gray-900">OrcaQuant</span>
              </Link>
              
              <div className="hidden md:flex ml-10 space-x-8">
                <Link 
                  to="/" 
                  className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/predictions" 
                  className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium transition-colors"
                >
                  Tahminler
                </Link>
              </div>
            </div>

            {/* User menu */}
            <div className="flex items-center space-x-4">
              {/* Subscription badge */}
              <span className={`
                px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide
                ${user?.subscription_level === 'premium' ? 'bg-yellow-100 text-yellow-800' :
                  user?.subscription_level === 'enterprise' ? 'bg-purple-100 text-purple-800' :
                  user?.subscription_level === 'basic' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'}
              `}>
                {user?.subscription_level}
              </span>

              {/* User info */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <User className="h-5 w-5 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">
                    {user?.username}
                  </span>
                </div>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 text-gray-500 hover:text-red-600 transition-colors"
                  title="Çıkış Yap"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden md:inline text-sm">Çıkış</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <Outlet />
      </main>

      {/* Trial warning */}
      {user?.trial_remaining_days && user.trial_remaining_days <= 7 && (
        <div className="fixed bottom-4 right-4 bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded shadow-lg">
          <div className="flex items-center">
            <div className="text-sm">
              <strong>Trial uyarısı:</strong> {user.trial_remaining_days} gününüz kaldı.{' '}
              <Link to="/abonelik" className="underline font-semibold hover:text-yellow-800">
                Aboneliği yükseltin
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;