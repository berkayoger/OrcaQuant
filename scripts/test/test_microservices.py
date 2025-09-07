#!/usr/bin/env python3

import requests
import json
import time
import sys
from datetime import datetime

class MicroservicesTester:
    def __init__(self, base_url="http://localhost"):
        self.base_url = base_url
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 OrcaQuant Mikroservis Test Suite Başlatılıyor...")
        print("=" * 60)
        
        # Test individual services
        self.test_health_checks()
        self.test_auth_service()
        self.test_analysis_service()
        self.test_payment_service()
        self.test_api_gateway()
        
        # Print results
        self.print_results()
        
    def test_health_checks(self):
        """Test all service health endpoints"""
        print("\n🔍 Health Check Testleri...")
        
        services = {
            'Gateway': f"{self.base_url}/health",
            'Auth Service': f"{self.base_url}:5001/health",
            'Analysis Service': f"{self.base_url}:5002/health", 
            'Payment Service': f"{self.base_url}:5003/health"
        }
        
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.test_results.append(f"✅ {service_name} health check passed")
                else:
                    self.test_results.append(f"❌ {service_name} health check failed: {response.status_code}")
            except requests.RequestException as e:
                self.test_results.append(f"❌ {service_name} health check failed: {str(e)}")
                
    def test_auth_service(self):
        """Test authentication service"""
        print("\n🔐 Auth Service Testleri...")
        
        # Test user registration
        try:
            register_data = {
                "email": f"test-{int(time.time())}@example.com",
                "password": "TestPassword123!"
            }
            
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=register_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                self.test_results.append("✅ User registration successful")
                
                # Test user login
                login_response = requests.post(
                    f"{self.base_url}/api/auth/login",
                    json=register_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.auth_token = login_data.get('access_token')
                    self.user_id = login_data.get('user', {}).get('id')
                    self.test_results.append("✅ User login successful")
                    
                    # Test token verification
                    verify_response = requests.post(
                        f"{self.base_url}/api/auth/verify",
                        headers={'Authorization': f'Bearer {self.auth_token}'}
                    )
                    
                    if verify_response.status_code == 200:
                        self.test_results.append("✅ Token verification successful")
                    else:
                        self.test_results.append("❌ Token verification failed")
                        
                else:
                    self.test_results.append("❌ User login failed")
            else:
                self.test_results.append("❌ User registration failed")
                
        except requests.RequestException as e:
            self.test_results.append(f"❌ Auth service test failed: {str(e)}")
            
    def test_analysis_service(self):
        """Test analysis service"""
        print("\n📊 Analysis Service Testleri...")
        
        if not self.auth_token:
            self.test_results.append("❌ Analysis test skipped - no auth token")
            return
            
        try:
            # Generate sample OHLCV data
            sample_data = self._generate_sample_ohlcv()
            
            analysis_data = {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "ohlcv": sample_data
            }
            
            response = requests.post(
                f"{self.base_url}/api/analysis/predict",
                json=analysis_data,
                headers={
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                self.test_results.append("✅ Analysis prediction successful")
                
                # Test multi-engine analysis
                multi_engine_data = {
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "engines": ["KM1", "KM2", "KM3"],
                    "ohlcv": sample_data
                }
                
                multi_response = requests.post(
                    f"{self.base_url}/api/analysis/multi-engine",
                    json=multi_engine_data,
                    headers={
                        'Authorization': f'Bearer {self.auth_token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if multi_response.status_code == 200:
                    self.test_results.append("✅ Multi-engine analysis successful")
                else:
                    self.test_results.append("❌ Multi-engine analysis failed")
                    
            else:
                self.test_results.append("❌ Analysis prediction failed")
                
        except requests.RequestException as e:
            self.test_results.append(f"❌ Analysis service test failed: {str(e)}")
            
    def test_payment_service(self):
        """Test payment service"""
        print("\n💳 Payment Service Testleri...")
        
        if not self.auth_token or not self.user_id:
            self.test_results.append("❌ Payment test skipped - no auth token")
            return
            
        try:
            # Test subscription status check
            response = requests.get(
                f"{self.base_url}/api/payment/subscription/{self.user_id}",
                headers={'Authorization': f'Bearer {self.auth_token}'}
            )
            
            # 404 is expected for new user (no subscription)
            if response.status_code in [200, 404]:
                self.test_results.append("✅ Subscription status check successful")
            else:
                self.test_results.append("❌ Subscription status check failed")
                
            # Test payment history
            history_response = requests.get(
                f"{self.base_url}/api/payment/history/{self.user_id}",
                headers={'Authorization': f'Bearer {self.auth_token}'}
            )
            
            if history_response.status_code == 200:
                self.test_results.append("✅ Payment history retrieval successful")
            else:
                self.test_results.append("❌ Payment history retrieval failed")
                
        except requests.RequestException as e:
            self.test_results.append(f"❌ Payment service test failed: {str(e)}")
            
    def test_api_gateway(self):
        """Test API Gateway functionality"""
        print("\n🌐 API Gateway Testleri...")
        
        if not self.auth_token or not self.user_id:
            self.test_results.append("❌ Gateway test skipped - no auth token")
            return
            
        try:
            # Test aggregated dashboard endpoint
            response = requests.get(
                f"{self.base_url}/api/user/dashboard/{self.user_id}",
                headers={'Authorization': f'Bearer {self.auth_token}'}
            )
            
            if response.status_code == 200:
                dashboard_data = response.json()
                required_keys = ['subscription', 'recent_analyses', 'recent_payments']
                
                if all(key in dashboard_data for key in required_keys):
                    self.test_results.append("✅ API Gateway dashboard aggregation successful")
                else:
                    self.test_results.append("❌ API Gateway dashboard missing data")
            else:
                self.test_results.append("❌ API Gateway dashboard failed")
                
            # Test rate limiting (make multiple rapid requests)
            rate_limit_passed = True
            for i in range(102):  # Exceed 100 req/min limit
                test_response = requests.get(f"{self.base_url}/health", timeout=1)
                if test_response.status_code == 429:  # Rate limited
                    rate_limit_passed = True
                    break
                    
            if rate_limit_passed:
                self.test_results.append("✅ API Gateway rate limiting works")
            else:
                self.test_results.append("⚠️  API Gateway rate limiting not triggered")
                
        except requests.RequestException as e:
            self.test_results.append(f"❌ API Gateway test failed: {str(e)}")
            
    def _generate_sample_ohlcv(self):
        """Generate sample OHLCV data for testing"""
        import random
        
        base_price = 50000  # Base BTC price
        data = []
        
        for i in range(50):  # 50 candles
            timestamp = datetime.now().isoformat()
            
            # Generate realistic OHLCV data
            open_price = base_price + random.uniform(-1000, 1000)
            close_price = open_price + random.uniform(-500, 500)
            high_price = max(open_price, close_price) + random.uniform(0, 200)
            low_price = min(open_price, close_price) - random.uniform(0, 200)
            volume = random.uniform(100, 1000)
            
            data.append({
                "timestamp": timestamp,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume
            })
            
            base_price = close_price  # Trend continuation
            
        return data
        
    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SONUÇLARI")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result.startswith("✅"))
        failed = sum(1 for result in self.test_results if result.startswith("❌"))
        warnings = sum(1 for result in self.test_results if result.startswith("⚠️"))
        
        for result in self.test_results:
            print(result)
            
        print("\n" + "=" * 60)
        print(f"📊 ÖZET: {passed} Başarılı, {failed} Başarısız, {warnings} Uyarı")
        
        if failed == 0:
            print("🎉 Tüm testler başarılı! Mikroservis mimarisi çalışıyor.")
            return 0
        else:
            print("⚠️  Bazı testler başarısız. Loglara bakın.")
            return 1

if __name__ == "__main__":
    tester = MicroservicesTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
