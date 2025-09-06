import React, { useState, useEffect } from 'react';
import { Navigate, useLocation, Link } from 'react-router-dom';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { useAppSelector } from '../hooks/useAppSelector';
import { loginAsync, clearError } from '../store/slices/authSlice';
import { Eye, EyeOff, BarChart3 } from 'lucide-react';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{ [key: string]: string }>({});
  
  const dispatch = useAppDispatch();
  const { isAuthenticated, isLoading, error } = useAppSelector(state => state.auth);
  const location = useLocation();

  // Clear errors when component mounts or unmounts
  useEffect(() => {
    dispatch(clearError());
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  // Redirect if already authenticated
  if (isAuthenticated) {
    const from = location.state?.from?.pathname || '/';
    return <Navigate to={from} replace />;
  }

  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    
    if (!username.trim()) {
      errors.username = 'Kullanıcı adı gereklidir';
    }
    
    if (!password.trim()) {
      errors.password = 'Şifre gereklidir';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    dispatch(clearError());
    await dispatch(loginAsync({ username, password }));
  };

  return (
    <div className="min-h-screen crypto-bg flex items-center justify-center p-4">
      <div className="card backdrop-blur-md bg-slate-800/85 p-8 sm:p-10 max-w-md w-full">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <BarChart3 className="h-10 w-10 text-blue-400" />
            <span className="text-2xl font-bold text-white">OrcaQuant</span>
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">Giriş Yap</h2>
          <p className="text-sm text-slate-300">
            Analizlere erişmek için hesabınıza giriş yapın.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Username Field */}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
              Kullanıcı Adı:
            </label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={`
                input-field bg-slate-700 text-white placeholder-slate-400 border-slate-600
                focus:border-blue-400 focus:ring-blue-400/25
                ${validationErrors.username ? 'border-red-500' : ''}
              `}
              placeholder="kullanici_adiniz"
              autoComplete="username"
              autoFocus
            />
            {validationErrors.username && (
              <p className="error-message">{validationErrors.username}</p>
            )}
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
              Şifre:
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`
                  input-field bg-slate-700 text-white placeholder-slate-400 border-slate-600
                  focus:border-blue-400 focus:ring-blue-400/25 pr-10
                  ${validationErrors.password ? 'border-red-500' : ''}
                `}
                placeholder="Şifreniz"
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-300"
                aria-label="Şifreyi göster veya gizle"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {validationErrors.password && (
              <p className="error-message">{validationErrors.password}</p>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-md">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="btn-base btn-gradient w-full py-3 disabled:opacity-50"
          >
            <span>{isLoading ? 'Giriş Yapılıyor...' : 'Giriş Yap'}</span>
            {isLoading && <div className="loader ml-2"></div>}
          </button>

          {/* Links */}
          <div className="text-center text-sm text-slate-400 space-y-2">
            <p>
              Hesabın yok mu?{' '}
              <Link to="/register" className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors">
                Şimdi üye ol
              </Link>
            </p>
            <p>
              <button
                type="button"
                onClick={() => alert('Şifre sıfırlama özelliği yakında eklenecek.')}
                className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors"
              >
                Şifremi Unuttum?
              </button>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;