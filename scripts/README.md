# OrcaQuant Deployment & Testing Scripts

Bu dizin OrcaQuant mikroservis mimarisinin deployment, test ve monitoring işlemlerini otomatikleştiren scriptleri içerir.

## 📁 Dizin Yapısı

```
scripts/
├── README.md                    # Bu dosya
├── test/                        # Test scriptleri
│   ├── test_microservices.py   # Comprehensive microservice test suite
│   └── load_test.py            # Performance load testing
├── deployment/                  # Deployment scriptleri
│   ├── deploy_k8s.sh           # Kubernetes deployment
│   ├── build_images.sh         # Docker image build script
│   └── deploy_docker.sh        # Docker Compose deployment
├── monitoring/                  # Monitoring setup
│   └── setup_monitoring.sh     # Prometheus, Grafana, AlertManager setup
└── utilities/                   # Utility scripts
    ├── cleanup.sh              # Cleanup deployments
    ├── backup.sh               # Database backup
    └── health_check.sh         # Quick health check
```

## 🚀 Quick Start

### 1. Test Suite Çalıştırma

```bash
# Tüm mikroservisleri test et
python3 scripts/test/test_microservices.py --base-url http://localhost

# Load test çalıştır (30 saniye, 10 kullanıcı)
python3 scripts/test/load_test.py --duration 30 --users 10
```

### 2. Kubernetes Deployment

```bash
# Environment variables ayarla
export POSTGRES_PASSWORD="secure_password"
export JWT_SECRET_KEY="your-jwt-secret"
export STRIPE_SECRET_KEY="your-stripe-key"

# Deploy et
./scripts/deployment/deploy_k8s.sh
```

### 3. Monitoring Setup

```bash
# Monitoring stack kurulumu
./scripts/monitoring/setup_monitoring.sh

# Grafana: http://localhost:30030 (admin/admin_password)
# Prometheus: http://localhost:30090
```

## 📋 Script Detayları

### Test Scripts

#### `test_microservices.py`
- **Amaç**: Tüm mikroservislerin fonksiyonellik testleri
- **Özellikler**:
  - Health check testleri
  - Auth service testleri (register, login, token verification)
  - Analysis service testleri (prediction, multi-engine)
  - Payment service testleri (subscription, history)
  - API Gateway testleri (aggregation, rate limiting)
  - WebSocket service testleri
  - Cross-service integration testleri

- **Kullanım**:
  ```bash
  python3 scripts/test/test_microservices.py --help
  python3 scripts/test/test_microservices.py --base-url http://your-server --verbose
  ```

#### `load_test.py`
- **Amaç**: Sistem performansını yük altında test etme
- **Özellikler**:
  - Gerçekçi kullanıcı davranışları simülasyonu
  - Concurrent user desteği
  - Ramp-up period
  - Detaylı performans metrikleri (RPS, latency, percentiles)
  - Otomatik test kullanıcısı oluşturma
  - Status code analizi

- **Kullanım**:
  ```bash
  python3 scripts/test/load_test.py --duration 60 --users 20 --ramp-up 10
  ```

### Deployment Scripts

#### `deploy_k8s.sh`
- **Amaç**: Kubernetes üzerinde production-ready deployment
- **Özellikler**:
  - Namespace ve resource yönetimi
  - Secret ve ConfigMap oluşturma
  - PostgreSQL ve Redis deployment
  - Tüm mikroservislerin deployment
  - Health check ve readiness probe
  - Horizontal Pod Autoscaler (HPA)
  - Network policies (güvenlik)
  - Database migration

- **Environment Variables**:
  ```bash
  export POSTGRES_PASSWORD="secure_password"
  export JWT_SECRET_KEY="your-jwt-secret"
  export STRIPE_SECRET_KEY="your-stripe-key"
  export DOCKER_REGISTRY="your-registry"
  export IMAGE_TAG="latest"
  ```

### Monitoring Scripts

#### `setup_monitoring.sh`
- **Amaç**: Comprehensive monitoring stack kurulumu
- **Bileşenler**:
  - **Prometheus**: Metrics toplama ve alerting
  - **Grafana**: Visualization ve dashboard
  - **AlertManager**: Alert yönetimi
  
- **Özellikler**:
  - Otomatik service discovery
  - OrcaQuant-specific metrics
  - Pre-configured dashboards
  - Alert rules (service down, high error rate, high latency)
  - Kubernetes integration

## 🔧 Prerequisites

### Python Dependencies
```bash
pip install requests aiohttp
```

### Kubernetes Tools
```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Minikube (local development)
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
```

### Docker
```bash
# Docker installation
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

## 📊 Monitoring ve Metrics

### Prometheus Metrics
OrcaQuant servisleri aşağıdaki metrikleri expose eder:
- `flask_http_request_total`: HTTP request sayısı
- `flask_http_request_duration_seconds`: Request latency
- `flask_http_request_exceptions_total`: Exception sayısı
- Custom business metrics (analysis_predictions_total, user_registrations_total, etc.)

### Grafana Dashboards
- **OrcaQuant Services**: Ana dashboard
- Request rate, response time, error rate
- Service-specific metrics
- Infrastructure metrics (CPU, Memory)

### Alert Rules
- **ServiceDown**: Servis erişilemez durumda
- **HighErrorRate**: Yüksek hata oranı (>10%)
- **HighLatency**: Yüksek latency (>1s)
- **HighMemoryUsage**: Yüksek memory kullanımı (>90%)
- **HighCPUUsage**: Yüksek CPU kullanımı (>80%)

## 🛡️ Security Considerations

### Secrets Management
- Kubernetes secrets kullanımı
- Environment variable'lar için .env.example template
- Production'da AWS Secrets Manager/Azure Key Vault önerilir

### Network Security
- Network policies ile pod-to-pod communication kontrolü
- TLS termination
- RBAC (Role-Based Access Control)

### Image Security
- Multi-stage Docker builds
- Non-root user kullanımı
- Security scanning (Trivy, Snyk)

## 🔍 Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**
   ```bash
   kubectl logs -f deployment/service-name -n orcaquant
   kubectl describe pod <pod-name> -n orcaquant
   ```

2. **Database Connection Issues**
   ```bash
   kubectl exec -it deployment/postgres -n orcaquant -- psql -U orcaquant_user -d orcaquant
   ```

3. **Service Discovery Problems**
   ```bash
   kubectl get svc -n orcaquant
   kubectl get endpoints -n orcaquant
   ```

### Health Check Commands
```bash
# Service health
curl http://localhost/health
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health

# Database connectivity test
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -- psql -h postgres -U orcaquant_user -d orcaquant
```

## 📈 Performance Tuning

### Resource Requests/Limits
Scripts'lerde tanımlanan resource limits'leri workload'unuza göre ayarlayın:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### HPA Configuration
Horizontal Pod Autoscaler ayarlarını traffic pattern'lerinize göre optimize edin.

### Database Optimization
- Connection pooling
- Index optimization
- Query performance monitoring

## 🤝 Contributing

Script'lere katkıda bulunmak için:
1. Fork the repository
2. Create feature branch
3. Test your changes
4. Submit pull request

## 📝 License

Bu script'ler OrcaQuant projesinin bir parçası olarak aynı license altında dağıtılmaktadır.