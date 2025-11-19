# Production Deployment Guide

This guide covers deploying Codex Prime Agent OS to production environments using Docker, Kubernetes, and cloud platforms.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Docker Deployment](#docker-deployment)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Platform Deployment](#cloud-platform-deployment)
6. [Security Considerations](#security-considerations)
7. [Monitoring & Observability](#monitoring--observability)
8. [Scaling](#scaling)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Deployment Options

### Quick Comparison

| Method | Best For | Complexity | Scalability |
|--------|----------|------------|-------------|
| Single Docker Container | Development, Testing | Low | Limited |
| Docker Compose | Small Production, Staging | Medium | Medium |
| Kubernetes | Enterprise, High-Traffic | High | High |
| Managed Cloud | Quick Start, Auto-scaling | Medium | Very High |

## Docker Deployment

### Simple Single Container

```bash
# Build the image
docker build -t codex-prime:latest .

# Run with environment variables
docker run -d \
  --name codex-prime \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e ANTHROPIC_API_KEY=your_key_here \
  -v codex-data:/home/codex/.codex_prime \
  --restart unless-stopped \
  codex-prime:latest
```

### With Custom Configuration

```bash
# Create config directory
mkdir -p ./config

# Copy personas and config files
cp personas/*.yaml ./config/

# Run with mounted config
docker run -d \
  --name codex-prime \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -v codex-data:/home/codex/.codex_prime \
  -v $(pwd)/config:/app/config:ro \
  --restart unless-stopped \
  codex-prime:latest
```

## Docker Compose Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 20GB+ disk space

### Step 1: Prepare Environment

```bash
# Clone repository
git clone https://github.com/yourusername/agent-OS.git
cd agent-OS

# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GRAFANA_PASSWORD=secure_password
EOF

# Secure the .env file
chmod 600 .env
```

### Step 2: Deploy Stack

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Step 3: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check WebSocket
wscat -c ws://localhost:8001

# Access Web UI
open http://localhost:3000
```

### Services Included

- **API Server** (port 8000) - Main application
- **WebSocket Server** (port 8001) - Real-time collaboration
- **PostgreSQL** (port 5432) - Primary database
- **Redis** (port 6379) - Cache and pub/sub
- **ChromaDB** (port 8002) - Vector storage
- **Web UI** (port 3000) - React frontend
- **Prometheus** (port 9090) - Metrics collection
- **Grafana** (port 3001) - Visualization

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.24+
- kubectl configured
- 8GB+ RAM across cluster
- 100GB+ storage
- LoadBalancer or Ingress controller

### Step 1: Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### Step 2: Create Secrets

```bash
# Create secrets from .env file
kubectl create secret generic codex-prime-secrets \
  --from-literal=OPENAI_API_KEY=your_key \
  --from-literal=ANTHROPIC_API_KEY=your_key \
  --from-literal=POSTGRES_PASSWORD=secure_password \
  --from-literal=GRAFANA_PASSWORD=admin_password \
  --namespace=codex-prime

# Verify secrets
kubectl get secrets -n codex-prime
```

### Step 3: Deploy Storage

```bash
# Create persistent volumes
kubectl apply -f k8s/persistent-volume.yaml

# Verify PVCs
kubectl get pvc -n codex-prime
```

### Step 4: Deploy Database Layer

```bash
# Deploy PostgreSQL
kubectl apply -f k8s/postgres-deployment.yaml

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n codex-prime --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n codex-prime --timeout=300s
```

### Step 5: Deploy Application

```bash
# Apply ConfigMap
kubectl apply -f k8s/configmap.yaml

# Deploy API server
kubectl apply -f k8s/api-deployment.yaml

# Verify deployment
kubectl get pods -n codex-prime
kubectl get svc -n codex-prime
```

### Step 6: Configure Ingress

Create `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: codex-prime-ingress
  namespace: codex-prime
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.codex-prime.com
    secretName: codex-prime-tls
  rules:
  - host: api.codex-prime.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: codex-prime-api-service
            port:
              number: 80
```

Apply:

```bash
kubectl apply -f k8s/ingress.yaml
```

### Step 7: Verify Deployment

```bash
# Check all resources
kubectl get all -n codex-prime

# Check logs
kubectl logs -f deployment/codex-prime-api -n codex-prime

# Port forward for testing
kubectl port-forward -n codex-prime svc/codex-prime-api-service 8000:80
curl http://localhost:8000/health
```

## Cloud Platform Deployment

### AWS (EKS)

```bash
# Create EKS cluster
eksctl create cluster \
  --name codex-prime \
  --version 1.27 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed

# Deploy application
kubectl apply -f k8s/

# Create load balancer
kubectl apply -f k8s/ingress-aws.yaml
```

### Google Cloud (GKE)

```bash
# Create GKE cluster
gcloud container clusters create codex-prime \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 5

# Get credentials
gcloud container clusters get-credentials codex-prime --zone us-central1-a

# Deploy application
kubectl apply -f k8s/
```

### Azure (AKS)

```bash
# Create resource group
az group create --name codex-prime-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group codex-prime-rg \
  --name codex-prime \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group codex-prime-rg --name codex-prime

# Deploy application
kubectl apply -f k8s/
```

## Security Considerations

### 1. API Keys & Secrets

```bash
# Use external secret management
# Example with AWS Secrets Manager
kubectl create secret generic codex-prime-secrets \
  --from-literal=OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
    --secret-id openai-api-key --query SecretString --output text)

# Or use Sealed Secrets
kubeseal --format=yaml < secrets.yaml > sealed-secrets.yaml
kubectl apply -f sealed-secrets.yaml
```

### 2. Network Policies

Create `k8s/network-policy.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: codex-prime-network-policy
  namespace: codex-prime
spec:
  podSelector:
    matchLabels:
      app: codex-prime-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web-ui
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### 3. TLS/SSL Configuration

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f k8s/cert-issuer.yaml
```

### 4. RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: codex-prime-role
  namespace: codex-prime
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
```

## Monitoring & Observability

### Prometheus Metrics

Access Prometheus:

```bash
kubectl port-forward -n codex-prime svc/prometheus 9090:9090
# Open http://localhost:9090
```

### Grafana Dashboards

Access Grafana:

```bash
kubectl port-forward -n codex-prime svc/grafana 3001:3000
# Open http://localhost:3001
# Default credentials: admin / [GRAFANA_PASSWORD from secrets]
```

### Application Logs

```bash
# Stream logs from all API pods
kubectl logs -f deployment/codex-prime-api -n codex-prime --all-containers=true

# View logs from specific pod
kubectl logs -n codex-prime <pod-name>

# Export logs to file
kubectl logs -n codex-prime deployment/codex-prime-api > api-logs.txt
```

### Health Checks

```bash
# Check health endpoint
curl https://api.codex-prime.com/health

# Check metrics endpoint
curl https://api.codex-prime.com/metrics
```

## Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: codex-prime-api-hpa
  namespace: codex-prime
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: codex-prime-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

Apply:

```bash
kubectl apply -f k8s/hpa.yaml
kubectl get hpa -n codex-prime
```

### Vertical Pod Autoscaling

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: codex-prime-api-vpa
  namespace: codex-prime
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: codex-prime-api
  updatePolicy:
    updateMode: "Auto"
```

## Backup & Recovery

### Database Backups

```bash
# Backup PostgreSQL
kubectl exec -n codex-prime deployment/postgres -- \
  pg_dump -U codex codexprime > backup-$(date +%Y%m%d).sql

# Restore PostgreSQL
kubectl exec -i -n codex-prime deployment/postgres -- \
  psql -U codex codexprime < backup-20240101.sql
```

### Volume Snapshots

```bash
# Create volume snapshot
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: codex-prime-snapshot-$(date +%Y%m%d)
  namespace: codex-prime
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: codex-prime-pvc
EOF
```

### Automated Backups

Create a CronJob:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: codex-prime
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgres-service -U codex codexprime | \
              gzip > /backup/backup-$(date +\%Y\%m\%d).sql.gz
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
```

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl get pods -n codex-prime

# Describe pod for events
kubectl describe pod <pod-name> -n codex-prime

# Check logs
kubectl logs <pod-name> -n codex-prime
```

#### 2. Database Connection Errors

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -n codex-prime -- \
  psql -h postgres-service -U codex -d codexprime

# Check service endpoints
kubectl get endpoints -n codex-prime
```

#### 3. High Memory Usage

```bash
# Check resource usage
kubectl top pods -n codex-prime

# Adjust resource limits
kubectl set resources deployment/codex-prime-api \
  --limits=memory=4Gi,cpu=2000m \
  --requests=memory=2Gi,cpu=1000m \
  -n codex-prime
```

#### 4. Slow Performance

```bash
# Check HPA status
kubectl get hpa -n codex-prime

# Scale manually if needed
kubectl scale deployment/codex-prime-api --replicas=5 -n codex-prime
```

### Debug Commands

```bash
# Get all resources
kubectl get all -n codex-prime

# Check events
kubectl get events -n codex-prime --sort-by='.lastTimestamp'

# Exec into pod
kubectl exec -it <pod-name> -n codex-prime -- /bin/bash

# Check resource quotas
kubectl describe resourcequota -n codex-prime
```

## Performance Tuning

### Database Optimization

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
```

### Redis Optimization

```bash
# Redis config
kubectl edit configmap redis-config -n codex-prime

# Add:
# maxmemory 512mb
# maxmemory-policy allkeys-lru
```

### Application Tuning

```yaml
# In deployment
env:
- name: WORKERS
  value: "4"
- name: WORKER_CONNECTIONS
  value: "1000"
- name: KEEPALIVE
  value: "5"
```

## Maintenance

### Rolling Updates

```bash
# Update image
kubectl set image deployment/codex-prime-api \
  api=codex-prime:v2.0.0 \
  -n codex-prime

# Check rollout status
kubectl rollout status deployment/codex-prime-api -n codex-prime

# Rollback if needed
kubectl rollout undo deployment/codex-prime-api -n codex-prime
```

### Cluster Maintenance

```bash
# Drain node for maintenance
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Uncordon when ready
kubectl uncordon <node-name>
```

---

**Production deployment complete!** Your Codex Prime Agent OS is now running in a scalable, monitored production environment.

For additional help, see:
- [Getting Started Guide](GETTING_STARTED.md)
- [Security Guide](SECURITY.md)
- [Architecture Guide](ARCHITECTURE.md)
