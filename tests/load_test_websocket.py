#!/usr/bin/env python3
"""
WebSocket load testing scripti
"""

import asyncio
import time
import logging
import statistics
from concurrent.futures import ThreadPoolExecutor
import socketio
from datetime import datetime
import argparse
import json
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketLoadTester:
    
    def __init__(self, url='http://localhost:5000', namespace='/'):
        self.url = url
        self.namespace = namespace
        self.results = []
        self.active_connections = 0
        self.total_messages_received = 0
        self.start_time = None
        self.end_time = None
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Graceful shutdown handler"""
        logger.info("Received shutdown signal, stopping load test...")
        self.stop_all_clients()
        sys.exit(0)
    
    async def single_client_test(self, client_id, duration=60, symbols=None):
        """Tek client için test senaryosu"""
        if symbols is None:
            symbols = ['BTCUSDT', 'ETHUSDT']
            
        start_time = time.time()
        messages_received = 0
        connection_time = None
        errors = 0
        
        client = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=3,
            reconnection_delay=1
        )
        
        @client.event
        async def connect():
            nonlocal connection_time
            connection_time = time.time() - start_time
            logger.debug(f"Client {client_id} connected in {connection_time:.3f}s")
            
            # Subscribe to price updates
            await client.emit('subscribe_price', {'symbols': symbols})
        
        @client.event
        async def disconnect():
            logger.debug(f"Client {client_id} disconnected")
        
        @client.event
        async def price_update(data):
            nonlocal messages_received
            messages_received += 1
            self.total_messages_received += 1
        
        @client.event
        async def subscription_confirmed(data):
            logger.debug(f"Client {client_id} subscription confirmed: {data}")
        
        @client.event
        async def connect_error(data):
            nonlocal errors
            errors += 1
            logger.error(f"Client {client_id} connection error: {data}")
        
        @client.event
        async def error(data):
            nonlocal errors
            errors += 1
            logger.error(f"Client {client_id} error: {data}")
        
        try:
            # Connection attempt
            conn_start = time.time()
            await client.connect(self.url)
            self.active_connections += 1
            
            # Wait for test duration
            await asyncio.sleep(duration)
            
        except Exception as e:
            errors += 1
            logger.error(f"Client {client_id} exception: {e}")
        finally:
            try:
                await client.disconnect()
                self.active_connections -= 1
            except:
                pass
        
        test_duration = time.time() - start_time
        
        return {
            'client_id': client_id,
            'connection_time': connection_time,
            'messages_received': messages_received,
            'errors': errors,
            'duration': test_duration,
            'messages_per_second': messages_received / test_duration if test_duration > 0 else 0
        }
    
    async def run_load_test(self, num_clients=50, duration=60, symbols=None):
        """Load test çalıştır"""
        logger.info(f"Starting load test: {num_clients} clients for {duration}s")
        self.start_time = time.time()
        
        # Concurrent client'ları başlat
        tasks = []
        for i in range(num_clients):
            task = asyncio.create_task(
                self.single_client_test(i, duration, symbols)
            )
            tasks.append(task)
            
            # Rate limit connection attempts (10 connections per second max)
            if i % 10 == 9:
                await asyncio.sleep(1)
        
        # Tüm client'ları bekle
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.end_time = time.time()
        
        # Sonuçları analiz et
        successful_results = [r for r in results if isinstance(r, dict) and not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        return self.analyze_results(successful_results, failed_results, num_clients)
    
    def analyze_results(self, successful_results, failed_results, total_clients):
        """Test sonuçlarını analiz et"""
        total_test_time = self.end_time - self.start_time
        
        if successful_results:
            connection_times = [r['connection_time'] for r in successful_results if r['connection_time']]
            message_counts = [r['messages_received'] for r in successful_results]
            error_counts = [r['errors'] for r in successful_results]
            
            report = {
                'test_summary': {
                    'total_clients': total_clients,
                    'successful_connections': len(successful_results),
                    'failed_connections': len(failed_results),
                    'success_rate': len(successful_results) / total_clients * 100,
                    'test_duration': total_test_time
                },
                'connection_performance': {
                    'avg_connection_time': statistics.mean(connection_times) if connection_times else 0,
                    'min_connection_time': min(connection_times) if connection_times else 0,
                    'max_connection_time': max(connection_times) if connection_times else 0,
                    'connection_time_std': statistics.stdev(connection_times) if len(connection_times) > 1 else 0
                },
                'message_performance': {
                    'total_messages': self.total_messages_received,
                    'avg_messages_per_client': statistics.mean(message_counts) if message_counts else 0,
                    'messages_per_second': self.total_messages_received / total_test_time,
                    'min_messages': min(message_counts) if message_counts else 0,
                    'max_messages': max(message_counts) if message_counts else 0
                },
                'error_analysis': {
                    'total_errors': sum(error_counts),
                    'avg_errors_per_client': statistics.mean(error_counts) if error_counts else 0,
                    'error_rate': sum(error_counts) / len(successful_results) if successful_results else 0
                },
                'detailed_results': successful_results
            }
        else:
            report = {
                'test_summary': {
                    'total_clients': total_clients,
                    'successful_connections': 0,
                    'failed_connections': len(failed_results),
                    'success_rate': 0,
                    'test_duration': total_test_time
                },
                'error': 'No successful connections',
                'failed_results': failed_results
            }
        
        return report
    
    def print_results(self, report):
        """Test sonuçlarını yazdır"""
        print("\n" + "="*80)
        print("WebSocket Load Test Results")
        print("="*80)
        
        # Test Summary
        summary = report['test_summary']
        print(f"📊 Test Summary:")
        print(f"   Total Clients: {summary['total_clients']}")
        print(f"   Successful Connections: {summary['successful_connections']}")
        print(f"   Failed Connections: {summary['failed_connections']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Test Duration: {summary['test_duration']:.2f}s")
        
        if 'connection_performance' in report:
            # Connection Performance
            conn_perf = report['connection_performance']
            print(f"\n🔌 Connection Performance:")
            print(f"   Average Connection Time: {conn_perf['avg_connection_time']:.3f}s")
            print(f"   Min Connection Time: {conn_perf['min_connection_time']:.3f}s")
            print(f"   Max Connection Time: {conn_perf['max_connection_time']:.3f}s")
            print(f"   Connection Time Std Dev: {conn_perf['connection_time_std']:.3f}s")
            
            # Message Performance
            msg_perf = report['message_performance']
            print(f"\n📨 Message Performance:")
            print(f"   Total Messages Received: {msg_perf['total_messages']:,}")
            print(f"   Messages per Second: {msg_perf['messages_per_second']:.2f}")
            print(f"   Average Messages per Client: {msg_perf['avg_messages_per_client']:.1f}")
            print(f"   Min Messages per Client: {msg_perf['min_messages']}")
            print(f"   Max Messages per Client: {msg_perf['max_messages']}")
            
            # Error Analysis
            error_analysis = report['error_analysis']
            print(f"\n⚠️  Error Analysis:")
            print(f"   Total Errors: {error_analysis['total_errors']}")
            print(f"   Average Errors per Client: {error_analysis['avg_errors_per_client']:.1f}")
            print(f"   Error Rate: {error_analysis['error_rate']:.3f}")
        
        # Performance Assessment
        self.assess_performance(report)
        
        print("="*80)
    
    def assess_performance(self, report):
        """Performans değerlendirmesi"""
        print(f"\n🎯 Performance Assessment:")
        
        if 'connection_performance' not in report:
            print("   ❌ Test failed - no performance data available")
            return
        
        success_rate = report['test_summary']['success_rate']
        avg_conn_time = report['connection_performance']['avg_connection_time']
        messages_per_sec = report['message_performance']['messages_per_second']
        error_rate = report['error_analysis']['error_rate']
        
        # Success rate assessment
        if success_rate >= 95:
            print(f"   ✅ Connection Success Rate: Excellent ({success_rate:.1f}%)")
        elif success_rate >= 90:
            print(f"   🟡 Connection Success Rate: Good ({success_rate:.1f}%)")
        else:
            print(f"   ❌ Connection Success Rate: Poor ({success_rate:.1f}%)")
        
        # Connection time assessment
        if avg_conn_time <= 0.1:
            print(f"   ✅ Connection Time: Excellent ({avg_conn_time:.3f}s)")
        elif avg_conn_time <= 0.5:
            print(f"   🟡 Connection Time: Good ({avg_conn_time:.3f}s)")
        else:
            print(f"   ❌ Connection Time: Poor ({avg_conn_time:.3f}s)")
        
        # Message throughput assessment
        if messages_per_sec >= 1000:
            print(f"   ✅ Message Throughput: Excellent ({messages_per_sec:.2f}/s)")
        elif messages_per_sec >= 100:
            print(f"   🟡 Message Throughput: Good ({messages_per_sec:.2f}/s)")
        else:
            print(f"   ❌ Message Throughput: Poor ({messages_per_sec:.2f}/s)")
        
        # Error rate assessment
        if error_rate <= 0.01:
            print(f"   ✅ Error Rate: Excellent ({error_rate:.3f})")
        elif error_rate <= 0.05:
            print(f"   🟡 Error Rate: Good ({error_rate:.3f})")
        else:
            print(f"   ❌ Error Rate: Poor ({error_rate:.3f})")
    
    def save_results(self, report, filename=None):
        """Sonuçları dosyaya kaydet"""
        if filename is None:
            filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def stop_all_clients(self):
        """Tüm client'ları durdur"""
        logger.info("Stopping all clients...")

async def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description='WebSocket Load Tester')
    parser.add_argument('--clients', type=int, default=50, 
                       help='Number of concurrent clients (default: 50)')
    parser.add_argument('--duration', type=int, default=30, 
                       help='Test duration in seconds (default: 30)')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='WebSocket server URL (default: http://localhost:5000)')
    parser.add_argument('--symbols', nargs='+', default=['BTCUSDT', 'ETHUSDT'],
                       help='Symbols to subscribe to (default: BTCUSDT ETHUSDT)')
    parser.add_argument('--save', action='store_true',
                       help='Save results to JSON file')
    parser.add_argument('--output', type=str,
                       help='Output filename for results')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting WebSocket Load Test")
    print(f"   Server: {args.url}")
    print(f"   Clients: {args.clients}")
    print(f"   Duration: {args.duration}s")
    print(f"   Symbols: {args.symbols}")
    
    tester = WebSocketLoadTester(args.url)
    
    try:
        report = await tester.run_load_test(
            num_clients=args.clients,
            duration=args.duration,
            symbols=args.symbols
        )
        
        tester.print_results(report)
        
        if args.save:
            tester.save_results(report, args.output)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())