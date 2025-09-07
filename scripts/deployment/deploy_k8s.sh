#!/bin/bash

set -e

echo "🚀 Kubernetes Deployment Başlatılıyor..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl bulunamadı. Kubernetes CLI'yi yükleyin."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster'a erişim yok. Bağlantınızı kontrol edin."
    exit 1
fi

# Create namespace
echo "📦 Namespace oluşturuluyor..."
kubectl apply -f infrastructure/kubernetes/namespace.yaml

# Create secrets
echo "🔐 Secrets oluşturuluyor..."
kubectl create secret generic postgres-secret \
    --from-literal=password=${POSTGRES_PASSWORD:-secure_password} \
    --namespace=orcaquant \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic app-secrets \
    --from-literal=jwt-secret-key=${JWT_SECRET_KEY:-dev-secret-key} \
    --from-literal=stripe-secret-key=${STRIPE_SECRET_KEY:-sk_test_dummy} \
    --namespace=orcaquant \
    --dry-run=client -o yaml | kubectl apply -f -

# Create ConfigMap
echo "⚙️  ConfigMap oluşturuluyor..."
kubectl apply -f infrastructure/kubernetes/configmap.yaml

# Create PersistentVolumes
echo "💾 Persistent volumes oluşturuluyor..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: orcaquant
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: orcaquant
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
EOF

# Deploy database services
echo "🗄️  Database servisleri deploy ediliyor..."
kubectl apply -f infrastructure/kubernetes/postgres.yaml
kubectl apply -f infrastructure/kubernetes/redis.yaml

# Wait for databases to be ready
echo "⏳ Database'lerin hazır olması bekleniyor..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s --namespace=orcaquant
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s --namespace=orcaquant

# Deploy application services
echo "�� Uygulama servisleri deploy ediliyor..."

# Auth Service
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: orcaquant
spec:
  replicas: 2
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: orcaquant-auth:latest
        ports:
        - containerPort: 5001
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: orcaquant-config
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: orcaquant-config
              key: REDIS_URL
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: jwt-secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: orcaquant
spec:
  selector:
    app: auth-service
  ports:
  - port: 5001
    targetPort: 5001
EOF

# Analysis Service
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analysis-service
  namespace: orcaquant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analysis-service
  template:
    metadata:
      labels:
        app: analysis-service
    spec:
      containers:
      - name: analysis-service
        image: orcaquant-analysis:latest
        ports:
        - containerPort: 5002
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: orcaquant-config
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: orcaquant-config
              key: REDIS_URL
        - name: AUTH_SERVICE_URL
          value: "http://auth-service:5001"
        livenessProbe:
          httpGet:
            path: /health
            port: 5002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5002
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: analysis-service
  namespace: orcaquant
spec:
  selector:
    app: analysis-service
  ports:
  - port: 5002
    targetPort: 5002
EOF

# Payment Service
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: orcaquant
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
      - name: payment-service
        image: orcaquant-payment:latest
        ports:
        - containerPort: 5003
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: orcaquant-config
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: orcaquant-config
              key: REDIS_URL
        - name: AUTH_SERVICE_URL
          value: "http://auth-service:5001"
        - name: STRIPE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: stripe-secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 5003
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5003
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: payment-service
  namespace: orcaquant
spec:
  selector:
    app: payment-service
  ports:
  - port: 5003
    targetPort: 5003
EOF

# Gateway Service with LoadBalancer
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway-service
  namespace: orcaquant
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gateway-service
  template:
    metadata:
      labels:
        app: gateway-service
    spec:
      containers:
      - name: gateway-service
        image: orcaquant-gateway:latest
        ports:
        - containerPort: 80
        env:
        - name: AUTH_SERVICE_URL
          value: "http://auth-service:5001"
        - name: ANALYSIS_SERVICE_URL
          value: "http://analysis-service:5002"
        - name: PAYMENT_SERVICE_URL
          value: "http://payment-service:5003"
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: orcaquant-config
              key: REDIS_URL
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: gateway-service
  namespace: orcaquant
spec:
  selector:
    app: gateway-service
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
EOF

# Wait for all services to be ready
echo "⏳ Servislerin hazır olması bekleniyor..."
kubectl wait --for=condition=ready pod -l app=auth-service --timeout=300s --namespace=orcaquant
kubectl wait --for=condition=ready pod -l app=analysis-service --timeout=300s --namespace=orcaquant
kubectl wait --for=condition=ready pod -l app=payment-service --timeout=300s --namespace=orcaquant
kubectl wait --for=condition=ready pod -l app=gateway-service --timeout=300s --namespace=orcaquant

# Run database migrations
echo "📊 Database migration çalıştırılıyor..."
kubectl run migration-job --rm -i --restart=Never --image=orcaquant-auth:latest --namespace=orcaquant -- python3 -c "
import os
os.system('python3 /app/scripts/migration/migrate_to_microservices.py')
"

echo "✅ Kubernetes deployment tamamlandı!"
echo ""
echo "📋 DEPLOY EDİLEN SERVİSLER:"
kubectl get pods --namespace=orcaquant
echo ""
echo "🌐 GATEWAY SERVICE URL:"
kubectl get service gateway-service --namespace=orcaquant -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo ""
echo "🔍 Servisleri izlemek için:"
echo "   kubectl logs -f deployment/auth-service --namespace=orcaquant"
echo "   kubectl logs -f deployment/analysis-service --namespace=orcaquant"
echo "   kubectl logs -f deployment/payment-service --namespace=orcaquant"
