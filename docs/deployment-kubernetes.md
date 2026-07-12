# Kubernetes Deployment

## Shape

```text
Namespace
  ->
Secrets
  ->
ConfigMaps
  ->
Adapter Deployments
  ->
Service Endpoints
```

## Rules

- Keep secrets in Kubernetes secrets, not in repo files
- Restrict network access to approved systems
- Separate read-only and write-capable adapters when possible

## Apply the manifests

```bash
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/persistentvolumeclaim.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
```

The deployment exposes the same `/healthz` endpoint that the local container uses.
