import { io } from 'socket.io-client';
const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000';
export const socket = io(SOCKET_URL, {
    autoConnect: false,
    transports: ['websocket'],
    auth: (cb) => {
        const token = localStorage.getItem('admin_token');
        cb({ token });
    }
});
socket.on('connect_error', (err) => {
    console.error('Socket connection error:', err.message);
});
