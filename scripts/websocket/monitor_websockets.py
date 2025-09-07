#!/usr/bin/env python3
"""
WebSocket bağlantılarını ve performansını izleme scripti
"""

import sys
import os
import time
import json
import logging
import psutil
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Proje yolunu sys.path'e ekle
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.core.redis_manager import redis_manager
    from backend.monitoring.prometheus_metrics import metrics_collector
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketMonitor:
    def __init__(self, api_url='http://localhost:5000'):
        self.api_url = api_url
        self.redis_client = redis_manager.client
        self.metrics = metrics_collector
        
    def get_system_metrics(self):
        """Sistem metriklerini toplar"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_io': psutil.net_io_counters()._asdict(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"System metrics error: {e}")
            return {}
    
    def get_redis_metrics(self):
        """Redis metriklerini toplar"""
        try:
            info = self.redis_client.info()
            return {
                'connected_clients': info['connected_clients'],
                'used_memory_human': info['used_memory_human'],
                'keyspace_hits': info['keyspace_hits'],
                'keyspace_misses': info['keyspace_misses'],
                'total_commands_processed': info['total_commands_processed'],
                'expired_keys': info['expired_keys'],
                'instantaneous_ops_per_sec': info['instantaneous_ops_per_sec']
            }
        except Exception as e:
            logger.error(f"Redis metrics error: {e}")
            return {}
    
    def get_websocket_metrics(self):
        """WebSocket metriklerini API'den alır"""
        try:
            response = requests.get(f"{self.api_url}/api/websocket/stats", timeout=5)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"WebSocket API error: {e}")
            return {}
        except Exception as e:
            logger.error(f"WebSocket metrics error: {e}")
            return {}
    
    def get_application_health(self):
        """Uygulama sağlık durumunu kontrol eder"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            return {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'health_data': response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check error: {e}")
            return {
                'status_code': 0,
                'response_time': 0,
                'health_data': {'status': 'unreachable', 'error': str(e)}
            }
        except Exception as e:
            logger.error(f"Health check parsing error: {e}")
            return {
                'status_code': 0,
                'response_time': 0,
                'health_data': {'status': 'error', 'error': str(e)}
            }
    
    def check_price_stream_health(self):
        """Fiyat stream'inin sağlığını kontrol eder"""
        try:
            # Son 2 dakikada fiyat güncellemesi var mı?
            latest_price = self.redis_client.get('price:BTCUSDT')
            if latest_price:
                price_data = json.loads(latest_price)
                last_update = datetime.fromisoformat(price_data['timestamp'])
                time_diff = datetime.utcnow() - last_update
                
                return {
                    'status': 'healthy' if time_diff < timedelta(minutes=2) else 'stale',
                    'last_update': last_update.isoformat(),
                    'minutes_since_update': time_diff.total_seconds() / 60,
                    'last_price': price_data.get('price', 0)
                }
            else:
                return {'status': 'no_data', 'last_update': None}
        except Exception as e:
            logger.error(f"Price stream health check error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_prometheus_metrics(self):
        """Prometheus metriklerini toplar"""
        try:
            return {
                'active_connections': self.metrics.get_connection_count(),
                'total_messages': self.metrics.get_total_messages(),
                'total_errors': self.metrics.get_error_count()
            }
        except Exception as e:
            logger.error(f"Prometheus metrics error: {e}")
            return {}
    
    def generate_report(self):
        """Comprehensive monitoring raporu oluşturur"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': self.get_system_metrics(),
            'redis': self.get_redis_metrics(),
            'websocket': self.get_websocket_metrics(),
            'application': self.get_application_health(),
            'price_stream': self.check_price_stream_health(),
            'prometheus': self.get_prometheus_metrics()
        }
        
        # Alert'leri kontrol et
        alerts = []
        
        # CPU alert
        if report['system'].get('cpu_percent', 0) > 80:
            alerts.append(f"High CPU usage: {report['system']['cpu_percent']:.1f}%")
        
        # Memory alert
        if report['system'].get('memory_percent', 0) > 85:
            alerts.append(f"High memory usage: {report['system']['memory_percent']:.1f}%")
        
        # WebSocket connection alert
        ws_connections = report['websocket'].get('total_connections', 0)
        if ws_connections > 1000:
            alerts.append(f"High WebSocket connections: {ws_connections}")
        elif ws_connections == 0:
            alerts.append("No active WebSocket connections")
        
        # Application health alert
        if report['application']['status_code'] != 200:
            alerts.append(f"Application unhealthy: {report['application']['health_data'].get('status', 'unknown')}")
        
        # Price stream alert
        if report['price_stream']['status'] != 'healthy':
            alerts.append(f"Price stream issue: {report['price_stream']['status']}")
        
        # Redis alert
        redis_clients = report['redis'].get('connected_clients', 0)
        if redis_clients > 100:
            alerts.append(f"High Redis connections: {redis_clients}")
        
        report['alerts'] = alerts
        report['alert_count'] = len(alerts)
        
        return report
    
    def save_report_to_redis(self, report):
        """Raporu Redis'e kaydet"""
        try:
            self.redis_client.setex(
                'monitoring:websocket:latest',
                300,  # 5 dakika
                json.dumps(report)
            )
            
            # Historical data için
            timestamp_key = f"monitoring:websocket:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            self.redis_client.setex(timestamp_key, 3600, json.dumps(report))  # 1 saat
            
        except Exception as e:
            logger.error(f"Error saving report to Redis: {e}")
    
    def print_report(self, report):
        """Raporu konsola yazdır"""
        print("\n" + "="*80)
        print(f"WebSocket Monitoring Report - {report['timestamp']}")
        print("="*80)
        
        # System metrics
        if report['system']:
            print(f"🖥️  System:")
            print(f"   CPU: {report['system'].get('cpu_percent', 0):.1f}% | "
                  f"Memory: {report['system'].get('memory_percent', 0):.1f}% | "
                  f"Disk: {report['system'].get('disk_percent', 0):.1f}%")
        
        # Application health
        if report['application']:
            health_status = report['application']['health_data'].get('status', 'unknown')
            response_time = report['application'].get('response_time', 0)
            print(f"🏥 Application Health: {health_status} ({response_time:.3f}s)")
        
        # WebSocket metrics
        if report['websocket']:
            print(f"🔌 WebSocket:")
            print(f"   Connections: {report['websocket'].get('total_connections', 0)} | "
                  f"Subscriptions: {report['websocket'].get('active_subscriptions', 0)}")
        
        # Price stream
        if report['price_stream']:
            stream_status = report['price_stream']['status']
            last_update = report['price_stream'].get('minutes_since_update', 0)
            print(f"📈 Price Stream: {stream_status} (last update: {last_update:.1f}m ago)")
        
        # Redis metrics
        if report['redis']:
            print(f"🔴 Redis:")
            print(f"   Clients: {report['redis'].get('connected_clients', 0)} | "
                  f"Memory: {report['redis'].get('used_memory_human', 'unknown')} | "
                  f"Ops/sec: {report['redis'].get('instantaneous_ops_per_sec', 0)}")
        
        # Prometheus metrics
        if report['prometheus']:
            print(f"📊 Metrics:")
            print(f"   Messages: {report['prometheus'].get('total_messages', 0)} | "
                  f"Errors: {report['prometheus'].get('total_errors', 0)}")
        
        # Alerts
        if report['alerts']:
            print(f"\n⚠️  ALERTS ({report['alert_count']}):")
            for i, alert in enumerate(report['alerts'], 1):
                print(f"   {i}. {alert}")
        else:
            print(f"\n✅ All systems healthy")
        
        print("="*80)
    
    def run_monitoring_loop(self, interval=60, max_iterations=None):
        """Monitoring loop'unu başlatır"""
        logger.info("Starting WebSocket monitoring...")
        iteration = 0
        
        try:
            while True:
                if max_iterations and iteration >= max_iterations:
                    break
                
                try:
                    report = self.generate_report()
                    
                    # Raporu Redis'e kaydet
                    self.save_report_to_redis(report)
                    
                    # Raporu konsola yazdır
                    self.print_report(report)
                    
                    # Alert varsa log'la
                    if report['alerts']:
                        logger.warning(f"ALERTS: {', '.join(report['alerts'])}")
                    else:
                        logger.info("All systems healthy")
                    
                    iteration += 1
                    
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                
                if max_iterations is None or iteration < max_iterations:
                    time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")

def main():
    """Ana fonksiyon"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WebSocket Monitoring Script')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('--iterations', type=int, 
                       help='Max iterations (default: unlimited)')
    parser.add_argument('--api-url', default='http://localhost:5000',
                       help='API URL (default: http://localhost:5000)')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit')
    
    args = parser.parse_args()
    
    monitor = WebSocketMonitor(api_url=args.api_url)
    
    if args.once:
        # Tek seferlik çalıştırma
        report = monitor.generate_report()
        monitor.print_report(report)
        monitor.save_report_to_redis(report)
    else:
        # Sürekli monitoring
        monitor.run_monitoring_loop(
            interval=args.interval,
            max_iterations=args.iterations
        )

if __name__ == '__main__':
    main()