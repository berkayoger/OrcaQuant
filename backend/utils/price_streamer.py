import asyncio
try:
    import websockets  # type: ignore
    HAS_WEBSOCKETS = True
except Exception:
    websockets = None  # type: ignore
    HAS_WEBSOCKETS = False
import json
import logging
import threading
from typing import Dict, List, Callable
import redis
from datetime import datetime
import time
import requests

logger = logging.getLogger(__name__)

class BinancePriceStreamer:
    """Binance WebSocket API'den real-time fiyat verileri çeker"""
    
    def __init__(self, redis_client, symbols: List[str]):
        self.redis_client = redis_client
        self.symbols = [s.lower() for s in symbols]
        self.ws_url = "wss://stream.binance.com:9443/ws/"
        self.is_running = False
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 10
        self.callbacks: List[Callable] = []
        
    def add_callback(self, callback: Callable):
        """Fiyat güncellemesi callback'i ekler"""
        self.callbacks.append(callback)
    
    async def _create_stream_url(self):
        """WebSocket stream URL'sini oluşturur"""
        streams = [f"{symbol}@ticker" for symbol in self.symbols]
        stream_names = "/".join(streams)
        return f"{self.ws_url}{stream_names}"
    
    async def _handle_message(self, message: str):
        """Gelen mesajları işler"""
        try:
            data = json.loads(message)
            
            if 'stream' in data:
                stream_data = data['data']
                symbol = stream_data['s']
                
                price_update = {
                    'symbol': symbol,
                    'price': float(stream_data['c']),
                    'change': float(stream_data['p']),
                    'change_percent': float(stream_data['P']),
                    'volume': float(stream_data['v']),
                    'high_24h': float(stream_data['h']),
                    'low_24h': float(stream_data['l']),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Redis'e publish et
                if self.redis_client:
                    try:
                        self.redis_client.publish(
                            'price_updates',
                            json.dumps({
                                'symbol': symbol,
                                'data': price_update
                            })
                        )
                    except Exception as e:
                        logger.error(f"Redis publish error: {e}")
                
                # Callback'leri çağır
                for callback in self.callbacks:
                    try:
                        callback(symbol, price_update)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from Binance WebSocket")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _connect_and_listen(self):
        """WebSocket bağlantısı kurar ve dinler"""
        if not HAS_WEBSOCKETS:
            logger.warning("websockets package not available; Binance streamer disabled in this environment")
            return
        url = await self._create_stream_url()
        attempt = 0
        
        while self.is_running and attempt < self.max_reconnect_attempts:
            try:
                async with websockets.connect(url) as websocket:
                    logger.info(f"Connected to Binance WebSocket: {self.symbols}")
                    attempt = 0  # Reset attempt counter on successful connection
                    
                    while self.is_running:
                        try:
                            message = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=30
                            )
                            await self._handle_message(message)
                            
                        except asyncio.TimeoutError:
                            # Ping/pong için
                            await websocket.ping()
                            
            except Exception as e:
                attempt += 1
                logger.error(f"WebSocket connection error (attempt {attempt}): {e}")
                if self.is_running and attempt < self.max_reconnect_attempts:
                    await asyncio.sleep(self.reconnect_delay * attempt)
                    
        if attempt >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached for Binance WebSocket")
    
    def start(self):
        """Price streamer'ı başlatır"""
        self.is_running = True
        
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._connect_and_listen())
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        logger.info("Binance price streamer started")
    
    def stop(self):
        """Price streamer'ı durdurur"""
        self.is_running = False
        logger.info("Binance price streamer stopped")

class CoinGeckoPriceStreamer:
    """CoinGecko API'den fiyat verileri çeker (fallback)"""
    
    def __init__(self, redis_client, symbols: List[str]):
        self.redis_client = redis_client
        self.symbols = symbols
        self.is_running = False
        self.update_interval = 30  # 30 saniye
        self.api_url = "https://api.coingecko.com/api/v3/simple/price"
        
        # CoinGecko için sembol mapping'i
        self.symbol_mapping = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'ADAUSDT': 'cardano',
            'DOTUSDT': 'polkadot',
            'LINKUSDT': 'chainlink',
            'BNBUSDT': 'binancecoin',
            'XRPUSDT': 'ripple',
            'LTCUSDT': 'litecoin'
        }
    
    def start(self):
        """Polling tabanlı fiyat güncellemelerini başlatır"""
        
        def fetch_prices():
            while self.is_running:
                try:
                    # CoinGecko coin ID'lerini hazırla
                    coin_ids = []
                    for symbol in self.symbols:
                        coin_id = self.symbol_mapping.get(symbol)
                        if coin_id:
                            coin_ids.append(coin_id)
                    
                    if not coin_ids:
                        time.sleep(self.update_interval)
                        continue
                    
                    # CoinGecko API call
                    symbols_str = ','.join(coin_ids)
                    params = {
                        'ids': symbols_str,
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_24hr_vol': 'true'
                    }
                    
                    response = requests.get(self.api_url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Reverse mapping için
                    id_to_symbol = {v: k for k, v in self.symbol_mapping.items()}
                    
                    for coin_id, price_data in data.items():
                        symbol = id_to_symbol.get(coin_id)
                        if not symbol:
                            continue
                            
                        price_update = {
                            'symbol': symbol,
                            'price': price_data['usd'],
                            'change_percent': price_data.get('usd_24h_change', 0),
                            'volume': price_data.get('usd_24h_vol', 0),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                        # Redis'e publish et
                        if self.redis_client:
                            try:
                                self.redis_client.publish(
                                    'price_updates',
                                    json.dumps({
                                        'symbol': symbol,
                                        'data': price_update
                                    })
                                )
                            except Exception as e:
                                logger.error(f"CoinGecko Redis publish error: {e}")
                
                except requests.exceptions.RequestException as e:
                    logger.error(f"CoinGecko API request error: {e}")
                except Exception as e:
                    logger.error(f"CoinGecko fetch error: {e}")
                
                time.sleep(self.update_interval)
        
        self.is_running = True
        thread = threading.Thread(target=fetch_prices, daemon=True)
        thread.start()
        logger.info("CoinGecko price streamer started")
    
    def stop(self):
        """Price streamer'ı durdurur"""
        self.is_running = False
        logger.info("CoinGecko price streamer stopped")

class PriceStreamManager:
    """Birden fazla price streamer'ı yöneten manager"""
    
    def __init__(self, redis_client, symbols: List[str]):
        self.redis_client = redis_client
        self.symbols = symbols
        self.streamers = []
        self.is_running = False
        
    def add_binance_streamer(self):
        """Binance streamer ekler"""
        binance_streamer = BinancePriceStreamer(self.redis_client, self.symbols)
        self.streamers.append(binance_streamer)
        return binance_streamer
        
    def add_coingecko_streamer(self):
        """CoinGecko streamer ekler (fallback)"""
        coingecko_streamer = CoinGeckoPriceStreamer(self.redis_client, self.symbols)
        self.streamers.append(coingecko_streamer)
        return coingecko_streamer
    
    def start_all(self):
        """Tüm streamer'ları başlatır"""
        if not self.streamers:
            logger.warning("No streamers configured")
            return
            
        self.is_running = True
        for streamer in self.streamers:
            try:
                streamer.start()
                logger.info(f"Started {streamer.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to start {streamer.__class__.__name__}: {e}")
    
    def stop_all(self):
        """Tüm streamer'ları durdurur"""
        self.is_running = False
        for streamer in self.streamers:
            try:
                streamer.stop()
                logger.info(f"Stopped {streamer.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to stop {streamer.__class__.__name__}: {e}")
    
    def get_health_status(self):
        """Streamer'ların sağlık durumunu döndürür"""
        status = {
            'total_streamers': len(self.streamers),
            'running_streamers': len([s for s in self.streamers if getattr(s, 'is_running', False)]),
            'symbols': self.symbols,
            'timestamp': datetime.utcnow().isoformat()
        }
        return status
