import { useEffect } from 'react';
import toast from 'react-hot-toast';
import { socket } from './socket';
export function useNotifications() {
    useEffect(() => {
        if (!socket.connected) {
            socket.connect();
        }
        const handler = (data) => {
            switch (data?.type) {
                case 'success':
                    toast.success(data.message);
                    break;
                case 'error':
                    toast.error(data.message);
                    break;
                case 'warning':
                    toast(data.message, { icon: '⚠️' });
                    break;
                default:
                    toast(data?.message || 'Bildirim');
            }
        };
        socket.on('admin:notification', handler);
        return () => {
            socket.off('admin:notification', handler);
        };
    }, []);
}
