#!/usr/bin/env python3

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import statistics

class LoadTester:
    def __init__(self, base_url="http://localhost", concurrent_users=10):
        self.base_url = base_url
        self.concurrent_users = concurrent_users
        self.results = {
            'requests_sent': 0,
            'requests_succeeded': 0,
            'requests_failed': 0,
            'response_times': [],
            'errors': []
        }
        
    async def run_load_test(self, duration_seconds=60):
        """Run load test for specified duration"""
        print(f"🚀 Load Test Başlatılıyor: {self.concurrent_users} kullanıcı, {duration_seconds}s süre")
        
        async with aiohttp.ClientSession() as session:
            # Create tasks for concurrent users
            tasks = []
            for user_id in range(self.concurrent_users):
                task = asyncio.create_task(
                    self._simulate_user(session, user_id, duration_seconds)
                )
                tasks.append(task)
                
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
        self._print_results()
        
    async def _simulate_user(self, session, user_id, duration):
        """Simulate a single user's behavior"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Simulate different API calls
                await self._make_health_check(session)
                await asyncio.sleep(0.1)  # Small delay between requests
                
            except Exception as e:
                self.results['errors'].append(str(e))
                
    async def _make_health_check(self, session):
        """Make a health check request"""
        start_time = time.time()
        
        try:
            async with session.get(f"{self.base_url}/health") as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                self.results['requests_sent'] += 1
                self.results['response_times'].append(response_time)
                
                if response.status == 200:
                    self.results['requests_succeeded'] += 1
                else:
                    self.results['requests_failed'] += 1
                    
        except Exception as e:
            self.results['requests_failed'] += 1
            self.results['errors'].append(str(e))
            
    def _print_results(self):
        """Print load test results"""
        print("\n" + "=" * 60)
        print("📊 LOAD TEST SONUÇLARI")
        print("=" * 60)
        
        total_requests = self.results['requests_sent']
        success_rate = (self.results['requests_succeeded'] / total_requests * 100) if total_requests > 0 else 0
        
        print(f"📈 Toplam İstek: {total_requests}")
        print(f"✅ Başarılı: {self.results['requests_succeeded']}")
        print(f"❌ Başarısız: {self.results['requests_failed']}")
        print(f"📊 Başarı Oranı: {success_rate:.2f}%")
        
        if self.results['response_times']:
            avg_response_time = statistics.mean(self.results['response_times'])
            min_response_time = min(self.results['response_times'])
            max_response_time = max(self.results['response_times'])
            p95_response_time = statistics.quantiles(self.results['response_times'], n=20)[18]  # 95th percentile
            
            print(f"⏱️  Ortalama Yanıt Süresi: {avg_response_time:.3f}s")
            print(f"⚡ En Hızlı: {min_response_time:.3f}s")
            print(f"🐌 En Yavaş: {max_response_time:.3f}s")
            print(f"📈 95th Percentile: {p95_response_time:.3f}s")
            
        if self.results['errors']:
            print(f"\n⚠️  Hatalar ({len(self.results['errors'])}):")
            for error in set(self.results['errors'][:10]):  # Show unique errors, max 10
                print(f"   - {error}")

if __name__ == "__main__":
    import sys
    
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    concurrent_users = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    tester = LoadTester(concurrent_users=concurrent_users)
    asyncio.run(tester.run_load_test(duration))
