#!/bin/bash

set -euo pipefail

echo "📊 Monitoring Stack Kurulumu Başlatılıyor..."

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install Prometheus
echo "🔍 Prometheus kuruluyor..."
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config-volume
          mountPath: /etc/prometheus
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus/'
          - '--web.console.libraries=/etc/prometheus/console_libraries'
          - '--web.console.templates=/etc/prometheus/consoles'
          - '--web.enable-lifecycle'
      volumes:
      - name: config-volume
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: monitoring
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
    nodePort: 30090
  type: NodePort
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'orcaquant-services'
        kubernetes_sd_configs:
        - role: pod
          namespaces:
            names:
            - orcaquant
        relabel_configs:
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
          action: keep
          regex: true
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
          action: replace
          target_label: __metrics_path__
          regex: (.+)
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scheme]
          action: replace
          target_label: __scheme__
          regex: (https?)
        - source_labels: [__meta_kubernetes_pod_ip, __meta_kubernetes_pod_annotation_prometheus_io_port]
          action: replace
          separator: ':'
          regex: (.+);(\d+)
          replacement: $1:$2
          target_label: __address__
        - action: labelmap
          regex: __meta_kubernetes_pod_label_(.+)
        - source_labels: [__meta_kubernetes_namespace]
          action: replace
          target_label: kubernetes_namespace
        - source_labels: [__meta_kubernetes_pod_name]
          action: replace
          target_label: kubernetes_pod_name
EOF

# Grafana setup
echo "📈 Grafana kuruluyor..."

# Create admin password secret
kubectl create secret generic grafana-admin \
  --from-literal=admin-password="${GRAFANA_PASSWORD:-admin}" \
  -n monitoring \
  --dry-run=client -o yaml | kubectl apply -f -

# Datasource provisioning
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: monitoring
  labels:
    grafana_datasource: '1'
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus-service.monitoring.svc.cluster.local:9090
        isDefault: true
        jsonData:
          timeInterval: 15s
EOF

# Optional basic dashboard (service health)
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
  labels:
    grafana_dashboard: '1'
data:
  orcaquant-overview.json: |
    {
      "annotations": {"list": []},
      "editable": true,
      "gnetId": null,
      "graphTooltip": 0,
      "panels": [
        {
          "type": "stat",
          "title": "Prometheus Up",
          "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
          "targets": [{"expr": "up", "refId": "A"}],
          "options": {"reduceOptions": {"calcs": ["mean"]}}
        },
        {
          "type": "graph",
          "title": "Request Rate (scraped)",
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
          "targets": [{"expr": "rate(process_cpu_seconds_total[5m])", "refId": "A"}]
        }
      ],
      "schemaVersion": 36,
      "style": "dark",
      "tags": ["orcaquant"],
      "templating": {"list": []},
      "time": {"from": "now-6h", "to": "now"},
      "timezone": "",
      "title": "OrcaQuant Overview",
      "version": 1
    }
EOF

# Grafana Deployment + Service
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_USER
          value: admin
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-admin
              key: admin-password
        - name: GF_AUTH_ANONYMOUS_ENABLED
          value: "false"
        volumeMounts:
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources
        - name: grafana-dashboards
          mountPath: /var/lib/grafana/dashboards
        - name: grafana-provisioning
          mountPath: /etc/grafana/provisioning/dashboards
      volumes:
      - name: grafana-datasources
        configMap:
          name: grafana-datasources
      - name: grafana-dashboards
        configMap:
          name: grafana-dashboards
      - name: grafana-provisioning
        configMap:
          name: grafana-provisioning
---
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: monitoring
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
    nodePort: 30300
  type: NodePort
EOF

# Grafana dashboard provisioning rules
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-provisioning
  namespace: monitoring
data:
  dashboards.yaml: |
    apiVersion: 1
    providers:
    - name: 'default'
      orgId: 1
      folder: ''
      type: file
      disableDeletion: false
      editable: true
      options:
        path: /var/lib/grafana/dashboards
EOF

echo "✅ Monitoring kurulumu tamamlandı."
echo "Prometheus: NodePort 30090, Grafana: NodePort 30300"
echo "Grafana admin kullanıcı: admin, parola: (grafana-admin secret)"
