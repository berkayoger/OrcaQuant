import asyncio
import websockets
import json
import logging
from typing import Callable, Optional, Dict, Any
import threading
import time

logger = logging.getLogger(__name__)

class ExternalWebSocketClient:
    """Harici WebSocket API'lerine bağlanmak için generic client"""
    
    def __init__(self, url: str, headers: Optional[Dict] = None):
        self.url = url
        self.headers = headers or {}
        self.is_connected = False
        self.websocket = None
        self.message_handlers = []
        self.reconnect_interval = 5
        self.max_reconnect_attempts = 10
        self.reconnect_count = 0
        
    def add_message_handler(self, handler: Callable[[Dict], None]):
        """Mesaj handler ekle"""
        self.message_handlers.append(handler)
    
    async def connect(self):
        """WebSocket bağlantısını kur"""
        try:
            self.websocket = await websockets.connect(
                self.url,
                extra_headers=self.headers,
                ping_interval=20,
                ping_timeout=10
            )
            self.is_connected = True
            self.reconnect_count = 0
            logger.info(f"Connected to {self.url}")
            
            # Message listening loop
            await self._listen_for_messages()
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.is_connected = False
            await self._handle_reconnect()
    
    async def _listen_for_messages(self):
        """Gelen mesajları dinle"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    # Tüm handlers'a mesajı gönder
                    for handler in self.message_handlers:
                        try:
                            handler(data)
                        except Exception as e:
                            logger.error(f"Handler error: {e}")
                            
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message[:100]}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
            await self._handle_reconnect()
        except Exception as e:
            logger.error(f"Listen error: {e}")
            self.is_connected = False
            await self._handle_reconnect()
    
    async def _handle_reconnect(self):
        """Yeniden bağlanma işlemini yönet"""
        if self.reconnect_count < self.max_reconnect_attempts:
            self.reconnect_count += 1
            wait_time = min(self.reconnect_interval * (2 ** self.reconnect_count), 60)
            
            logger.info(f"Reconnecting in {wait_time}s (attempt {self.reconnect_count})")
            await asyncio.sleep(wait_time)
            await self.connect()
        else:
            logger.error("Max reconnection attempts reached")
    
    async def send_message(self, message: Dict[str, Any]):
        """Mesaj gönder"""
        if not self.is_connected or not self.websocket:
            logger.warning("Cannot send message: not connected")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    def start_in_thread(self):
        """Ayrı thread'de başlat"""
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect())
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread
    
    async def close(self):
        """Bağlantıyı kapat"""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()

class BinanceWebSocketClient(ExternalWebSocketClient):
    """Binance özelinde WebSocket client"""
    
    def __init__(self, streams: list):
        stream_url = self._build_stream_url(streams)
        super().__init__(stream_url)
        self.streams = streams
    
    def _build_stream_url(self, streams: list) -> str:
        """Binance stream URL'ini oluştur"""
        base_url = "wss://stream.binance.com:9443/ws/"
        stream_names = "/".join(streams)
        return f"{base_url}{stream_names}"
    
    def subscribe_to_symbol(self, symbol: str, stream_type: str = "ticker"):
        """Yeni sembole abone ol"""
        stream = f"{symbol.lower()}@{stream_type}"
        if stream not in self.streams:
            self.streams.append(stream)
            # Yeni URL ile yeniden bağlan
            new_url = self._build_stream_url(self.streams)
            self.url = new_url

class CoinbaseWebSocketClient(ExternalWebSocketClient):
    """Coinbase Pro WebSocket client"""
    
    def __init__(self, channels: list, product_ids: list):
        super().__init__("wss://ws-feed.pro.coinbase.com")
        self.channels = channels
        self.product_ids = product_ids
    
    async def connect(self):
        """Coinbase özelinde bağlantı"""
        await super().connect()
        
        # Subscribe message gönder
        subscribe_msg = {
            "type": "subscribe",
            "channels": self.channels,
            "product_ids": self.product_ids
        }
        await self.send_message(subscribe_msg)