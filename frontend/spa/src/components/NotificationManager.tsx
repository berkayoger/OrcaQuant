import React, { useEffect } from 'react';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { removeNotification } from '../store/slices/appSlice';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

const NotificationManager: React.FC = () => {
  const notifications = useAppSelector(state => state.app.notifications);
  const dispatch = useAppDispatch();

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-5 w-5" />;
      case 'error':
        return <AlertCircle className="h-5 w-5" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getColorClasses = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-500 text-white';
      case 'error':
        return 'bg-red-500 text-white';
      case 'warning':
        return 'bg-yellow-500 text-white';
      default:
        return 'bg-blue-500 text-white';
    }
  };

  useEffect(() => {
    // Auto-remove notifications after 5 seconds
    const timers = notifications.map(notification => 
      setTimeout(() => {
        dispatch(removeNotification(notification.id));
      }, 5000)
    );

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [notifications, dispatch]);

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map(notification => (
        <div
          key={notification.id}
          className={`
            flex items-center justify-between p-4 rounded-lg shadow-lg min-w-[300px] max-w-md
            transform transition-all duration-300 ease-in-out
            ${getColorClasses(notification.type)}
          `}
        >
          <div className="flex items-center space-x-3">
            {getIcon(notification.type)}
            <p className="text-sm font-medium">{notification.message}</p>
          </div>
          
          <button
            onClick={() => dispatch(removeNotification(notification.id))}
            className="ml-4 flex-shrink-0 hover:bg-black hover:bg-opacity-20 rounded p-1 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
};

export default NotificationManager;