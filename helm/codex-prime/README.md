# Codex Prime Helm Chart

Official Helm chart for deploying Codex Prime Agent OS to Kubernetes.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- PV provisioner support in the underlying infrastructure
- At least 8GB RAM across cluster
- 100GB+ storage available

## Quick Start

### 1. Add Helm Repository

```bash
# Add repo (once available)
helm repo add codex-prime https://charts.codex-prime.dev
helm repo update
```

### 2. Install

```bash
# Install with default values
helm install my-codex-prime codex-prime/codex-prime

# Or install from local chart
helm install my-codex-prime ./helm/codex-prime
```

### 3. Access

```bash
# Get the service URL
export SERVICE_IP=$(kubectl get svc --namespace codex-prime my-codex-prime-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Codex Prime API: http://$SERVICE_IP"
```

## Configuration

### Using values file

Create `my-values.yaml`:

```yaml
api:
  replicaCount: 5
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"

secrets:
  openaiApiKey: "sk-your-key-here"
  anthropicApiKey: "sk-ant-your-key-here"

ingress:
  enabled: true
  hosts:
    - host: api.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
```

Install with custom values:

```bash
helm install my-codex-prime codex-prime/codex-prime -f my-values.yaml
```

### Using set flags

```bash
helm install my-codex-prime codex-prime/codex-prime \
  --set api.replicaCount=5 \
  --set secrets.openaiApiKey="sk-your-key" \
  --set ingress.enabled=true
```

## Parameters

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespace` | Kubernetes namespace | `codex-prime` |

### API Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api.replicaCount` | Number of API replicas | `3` |
| `api.image.repository` | API image repository | `codex-prime/agent-os` |
| `api.image.tag` | API image tag | `latest` |
| `api.service.type` | Service type | `LoadBalancer` |
| `api.service.port` | Service port | `80` |
| `api.resources.requests.memory` | Memory request | `512Mi` |
| `api.resources.requests.cpu` | CPU request | `250m` |
| `api.resources.limits.memory` | Memory limit | `2Gi` |
| `api.resources.limits.cpu` | CPU limit | `1000m` |

### Autoscaling Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api.autoscaling.enabled` | Enable HPA | `true` |
| `api.autoscaling.minReplicas` | Minimum replicas | `3` |
| `api.autoscaling.maxReplicas` | Maximum replicas | `10` |
| `api.autoscaling.targetCPUUtilizationPercentage` | Target CPU % | `70` |
| `api.autoscaling.targetMemoryUtilizationPercentage` | Target Memory % | `80` |

### PostgreSQL Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL | `true` |
| `postgresql.auth.username` | Database username | `codex` |
| `postgresql.auth.database` | Database name | `codexprime` |
| `postgresql.persistence.size` | PVC size | `20Gi` |

### Redis Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Enable Redis | `true` |
| `redis.persistence.size` | PVC size | `5Gi` |

### ChromaDB Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `chromadb.enabled` | Enable ChromaDB | `true` |
| `chromadb.persistence.size` | PVC size | `50Gi` |

### Secrets Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `secrets.create` | Create secrets from values | `true` |
| `secrets.existingSecret` | Use existing secret | `""` |
| `secrets.openaiApiKey` | OpenAI API key | `""` |
| `secrets.anthropicApiKey` | Anthropic API key | `""` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class | `nginx` |
| `ingress.hosts` | Ingress hosts | `[]` |
| `ingress.tls` | TLS configuration | `[]` |

## Examples

### Production Deployment

```yaml
# production-values.yaml
api:
  replicaCount: 10
  image:
    tag: "1.0.0"
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"

  autoscaling:
    enabled: true
    minReplicas: 5
    maxReplicas: 20

secrets:
  # Use existing secret in production
  create: false
  existingSecret: "codex-prime-prod-secrets"

postgresql:
  persistence:
    size: 100Gi
    storageClass: "fast-ssd"

chromadb:
  persistence:
    size: 500Gi
    storageClass: "fast-ssd"

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.codex-prime.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: codex-prime-tls
      hosts:
        - api.codex-prime.com

monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
```

Deploy:

```bash
helm install codex-prime codex-prime/codex-prime \
  -f production-values.yaml \
  --namespace codex-prime-prod \
  --create-namespace
```

### Development Deployment

```yaml
# dev-values.yaml
api:
  replicaCount: 1
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"

  autoscaling:
    enabled: false

postgresql:
  persistence:
    size: 5Gi

redis:
  persistence:
    size: 1Gi

chromadb:
  persistence:
    size: 10Gi

ingress:
  enabled: false
```

## Upgrading

### Upgrade to new version

```bash
# Update repo
helm repo update

# Upgrade release
helm upgrade my-codex-prime codex-prime/codex-prime \
  -f my-values.yaml
```

### Rollback

```bash
# View history
helm history my-codex-prime

# Rollback to previous
helm rollback my-codex-prime

# Rollback to specific revision
helm rollback my-codex-prime 3
```

## Uninstalling

```bash
# Uninstall release
helm uninstall my-codex-prime

# Delete namespace
kubectl delete namespace codex-prime
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n codex-prime

# Describe pod
kubectl describe pod <pod-name> -n codex-prime

# View logs
kubectl logs <pod-name> -n codex-prime
```

### Database connection issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -n codex-prime -- \
  psql -h my-codex-prime-postgresql -U codex -d codexprime
```

### Check Helm values

```bash
# Get computed values
helm get values my-codex-prime

# Get all values
helm get values my-codex-prime --all
```

## Best Practices

1. **Always use specific image tags in production**
   ```yaml
   api:
     image:
       tag: "1.0.0"  # Not "latest"
   ```

2. **Use external secrets management**
   ```yaml
   secrets:
     create: false
     existingSecret: "my-secrets"
   ```

3. **Enable resource limits**
   ```yaml
   api:
     resources:
       limits:
         memory: "2Gi"
         cpu: "1000m"
   ```

4. **Enable monitoring**
   ```yaml
   monitoring:
     enabled: true
   ```

5. **Use persistent storage for databases**
   ```yaml
   postgresql:
     persistence:
       enabled: true
       size: 100Gi
   ```

## Support

- [Documentation](https://docs.codex-prime.dev)
- [GitHub Issues](https://github.com/yourusername/agent-OS/issues)
- [Discussions](https://github.com/yourusername/agent-OS/discussions)

## License

MIT
