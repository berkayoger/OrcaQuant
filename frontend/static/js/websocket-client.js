class OrcaQuantWebSocket {
    constructor(serverUrl = 'http://localhost:5000') {
        this.serverUrl = serverUrl;
        this.socket = null;
        this.isConnected = false;
        this.subscribers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.connect();
    }
    
    connect() {
        try {
            this.socket = io(this.serverUrl, {
                transports: ['websocket', 'polling'],
                timeout: 20000,
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: this.reconnectDelay
            });
            
            this.setupEventListeners();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleReconnect();
        }
    }
    
    setupEventListeners() {
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.onConnectionChange?.(true);
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.isConnected = false;
            this.onConnectionChange?.(false);
            
            if (reason === 'io server disconnect') {
                // Server initiated disconnect, try to reconnect
                this.handleReconnect();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.handleReconnect();
        });
        
        this.socket.on('price_update', (data) => {
            this.handlePriceUpdate(data);
        });
        
        this.socket.on('subscription_confirmed', (data) => {
            console.log('Subscription confirmed:', data.symbols);
        });
        
        this.socket.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
        
        this.socket.on('pong', (data) => {
            console.log('Pong received:', data);
        });
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.onConnectionError?.('Max reconnection attempts reached');
        }
    }
    
    subscribeToPrices(symbols) {
        if (!this.isConnected) {
            console.warn('WebSocket not connected, cannot subscribe');
            return false;
        }
        
        this.socket.emit('subscribe_price', { symbols });
        return true;
    }
    
    unsubscribeFromPrices(symbols) {
        if (!this.isConnected) {
            console.warn('WebSocket not connected, cannot unsubscribe');
            return false;
        }
        
        this.socket.emit('unsubscribe_price', { symbols });
        return true;
    }
    
    ping() {
        if (!this.isConnected) {
            console.warn('WebSocket not connected, cannot ping');
            return false;
        }
        
        this.socket.emit('ping');
        return true;
    }
    
    handlePriceUpdate(data) {
        const { symbol, data: priceData } = data;
        
        // Subscribers'a bildir
        if (this.subscribers.has(symbol)) {
            this.subscribers.get(symbol).forEach(callback => {
                try {
                    callback(priceData);
                } catch (error) {
                    console.error('Error in price update callback:', error);
                }
            });
        }
        
        // Global callback
        this.onPriceUpdate?.(symbol, priceData);
    }
    
    addPriceSubscriber(symbol, callback) {
        if (!this.subscribers.has(symbol)) {
            this.subscribers.set(symbol, new Set());
        }
        this.subscribers.get(symbol).add(callback);
    }
    
    removePriceSubscriber(symbol, callback) {
        if (this.subscribers.has(symbol)) {
            this.subscribers.get(symbol).delete(callback);
            
            if (this.subscribers.get(symbol).size === 0) {
                this.subscribers.delete(symbol);
            }
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
    
    // Event handlers (can be overridden)
    onConnectionChange = null;
    onPriceUpdate = null;
    onConnectionError = null;
}

// Price Dashboard Component
class PriceDashboard {
    constructor(containerId, websocket) {
        this.container = document.getElementById(containerId);
        this.websocket = websocket;
        this.priceElements = new Map();
        
        this.setupUI();
        this.setupWebSocketHandlers();
    }
    
    setupUI() {
        this.container.innerHTML = `
            <div class="price-dashboard">
                <div class="connection-status" id="connectionStatus">
                    <span class="status-indicator"></span>
                    <span class="status-text">Connecting...</span>
                </div>
                <div class="price-grid" id="priceGrid">
                    <!-- Price cards will be added here -->
                </div>
                <div class="controls">
                    <input type="text" id="symbolInput" placeholder="Symbol (e.g., BTCUSDT)" />
                    <button id="addSymbol">Add Symbol</button>
                    <button id="pingServer">Ping Server</button>
                </div>
            </div>
        `;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        const addButton = document.getElementById('addSymbol');
        const symbolInput = document.getElementById('symbolInput');
        const pingButton = document.getElementById('pingServer');
        
        addButton.addEventListener('click', () => {
            const symbol = symbolInput.value.trim().toUpperCase();
            if (symbol) {
                this.addSymbol(symbol);
                symbolInput.value = '';
            }
        });
        
        symbolInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addButton.click();
            }
        });
        
        pingButton.addEventListener('click', () => {
            this.websocket.ping();
        });
    }
    
    setupWebSocketHandlers() {
        this.websocket.onConnectionChange = (isConnected) => {
            this.updateConnectionStatus(isConnected);
        };
        
        this.websocket.onPriceUpdate = (symbol, priceData) => {
            this.updatePriceDisplay(symbol, priceData);
        };
    }
    
    updateConnectionStatus(isConnected) {
        const statusElement = document.getElementById('connectionStatus');
        const indicator = statusElement.querySelector('.status-indicator');
        const text = statusElement.querySelector('.status-text');
        
        if (isConnected) {
            indicator.className = 'status-indicator connected';
            text.textContent = 'Connected';
        } else {
            indicator.className = 'status-indicator disconnected';
            text.textContent = 'Disconnected';
        }
    }
    
    addSymbol(symbol) {
        if (this.priceElements.has(symbol)) {
            console.log(`Symbol ${symbol} already added`);
            return;
        }
        
        // UI element oluştur
        const priceCard = this.createPriceCard(symbol);
        document.getElementById('priceGrid').appendChild(priceCard);
        this.priceElements.set(symbol, priceCard);
        
        // WebSocket subscription
        this.websocket.subscribeToPrices([symbol]);
    }
    
    createPriceCard(symbol) {
        const card = document.createElement('div');
        card.className = 'price-card';
        card.innerHTML = `
            <div class="price-card-header">
                <h3>${symbol}</h3>
                <button class="remove-btn" onclick="dashboard.removeSymbol('${symbol}')">×</button>
            </div>
            <div class="price-info">
                <div class="current-price">$--</div>
                <div class="price-change">
                    <span class="change-amount">--</span>
                    <span class="change-percent">(--)</span>
                </div>
                <div class="additional-info">
                    <div class="volume">Vol: --</div>
                    <div class="high-low">H: -- L: --</div>
                </div>
            </div>
            <div class="last-update">Last update: --</div>
        `;
        
        return card;
    }
    
    updatePriceDisplay(symbol, priceData) {
        const card = this.priceElements.get(symbol);
        if (!card) return;
        
        const priceElement = card.querySelector('.current-price');
        const changeAmountElement = card.querySelector('.change-amount');
        const changePercentElement = card.querySelector('.change-percent');
        const volumeElement = card.querySelector('.volume');
        const highLowElement = card.querySelector('.high-low');
        const updateElement = card.querySelector('.last-update');
        
        // Fiyat animasyonu için mevcut değeri kontrol et
        const currentPriceText = priceElement.textContent.replace('$', '').replace(/,/g, '');
        const currentPrice = parseFloat(currentPriceText);
        const newPrice = priceData.price;
        
        // Fiyat güncellemesi
        priceElement.textContent = `$${newPrice.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 8
        })}`;
        
        // Fiyat değişim animasyonu
        if (!isNaN(currentPrice) && currentPrice > 0) {
            if (newPrice > currentPrice) {
                priceElement.classList.add('price-up');
                setTimeout(() => priceElement.classList.remove('price-up'), 1000);
            } else if (newPrice < currentPrice) {
                priceElement.classList.add('price-down');
                setTimeout(() => priceElement.classList.remove('price-down'), 1000);
            }
        }
        
        // Değişim yüzdesi
        const changePercent = priceData.change_percent || 0;
        const changeAmount = priceData.change || 0;
        
        changeAmountElement.textContent = changeAmount >= 0 ? `+${changeAmount.toFixed(2)}` : changeAmount.toFixed(2);
        changePercentElement.textContent = `(${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
        
        const changeContainer = card.querySelector('.price-change');
        changeContainer.className = `price-change ${changePercent >= 0 ? 'positive' : 'negative'}`;
        
        // Ek bilgiler
        if (priceData.volume) {
            volumeElement.textContent = `Vol: ${this.formatLargeNumber(priceData.volume)}`;
        }
        
        if (priceData.high_24h && priceData.low_24h) {
            highLowElement.textContent = `H: ${priceData.high_24h.toFixed(2)} L: ${priceData.low_24h.toFixed(2)}`;
        }
        
        // Son güncelleme zamanı
        updateElement.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
    }
    
    formatLargeNumber(num) {
        if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
        return num.toFixed(2);
    }
    
    removeSymbol(symbol) {
        const card = this.priceElements.get(symbol);
        if (card) {
            card.remove();
            this.priceElements.delete(symbol);
            this.websocket.unsubscribeFromPrices([symbol]);
        }
    }
}

// CSS Styles
const dashboardStyles = `
<style>
.price-dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.connection-status {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 8px;
}

.status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #dc3545;
}

.status-indicator.connected {
    background: #28a745;
}

.price-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.price-card {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

.price-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.price-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.price-card-header h3 {
    margin: 0;
    color: #495057;
    font-size: 1.2em;
}

.remove-btn {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.current-price {
    font-size: 2em;
    font-weight: bold;
    color: #212529;
    margin-bottom: 10px;
    transition: all 0.3s ease;
}

.current-price.price-up {
    color: #28a745;
    transform: scale(1.05);
}

.current-price.price-down {
    color: #dc3545;
    transform: scale(1.05);
}

.price-change {
    margin-bottom: 15px;
}

.price-change.positive {
    color: #28a745;
}

.price-change.negative {
    color: #dc3545;
}

.additional-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-size: 0.9em;
    color: #6c757d;
}

.last-update {
    font-size: 0.8em;
    color: #adb5bd;
    text-align: right;
}

.controls {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}

.controls input {
    flex: 1;
    padding: 10px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    font-size: 16px;
}

.controls button {
    padding: 10px 20px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
}

.controls button:hover {
    background: #0056b3;
}

@media (max-width: 768px) {
    .price-grid {
        grid-template-columns: 1fr;
    }
    
    .controls {
        flex-direction: column;
    }
}
</style>
`;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add styles to head
    document.head.insertAdjacentHTML('beforeend', dashboardStyles);
    
    // Initialize WebSocket connection
    const websocket = new OrcaQuantWebSocket();
    
    // Initialize dashboard
    window.dashboard = new PriceDashboard('price-dashboard', websocket);
    
    // Add some default symbols after connection is established
    websocket.onConnectionChange = (isConnected) => {
        // Update dashboard connection status
        window.dashboard.updateConnectionStatus(isConnected);
        
        // Add default symbols when connected
        if (isConnected) {
            setTimeout(() => {
                window.dashboard.addSymbol('BTCUSDT');
                window.dashboard.addSymbol('ETHUSDT');
                window.dashboard.addSymbol('ADAUSDT');
            }, 1000);
        }
    };
});