# CMF Kubernetes Deployment Installation Guide

This guide provides step-by-step instructions to deploy the Common Metadata Framework (CMF) on Kubernetes using Helm.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Building Docker Images](#building-docker-images)
- [Configuration](#configuration)
- [Deployment Steps](#deployment-steps)
- [Verification](#verification)
- [Accessing Services](#accessing-services)
- [Uninstallation](#uninstallation)

---

## Prerequisites

Before starting the installation, ensure you have:

1. **Kubernetes Cluster** (v1.19+)
   - Minikube, kind, or a cloud-based cluster (EKS, GKE, AKS)
   - Verify: `kubectl cluster-info`

2. **Helm** (v3.0+)
   - Install from: https://helm.sh/docs/intro/install/
   - Verify: `helm version`

3. **Docker** or **Podman** (for building images)
   - Verify: `docker version` or `podman version`

4. **kubectl** configured to access your cluster
   - Verify: `kubectl get nodes`

5. **Storage provisioner** (for persistent volumes)
   - For Minikube: enabled by default
   - For cloud providers: ensure default storage class exists
   - Verify: `kubectl get storageclass`

---

## Architecture Overview

The CMF deployment consists of the following components:

- **CMF Server**: Backend API server for metadata management
- **UI**: React-based web interface
- **PostgreSQL**: Metadata database
- **Neo4j**: Graph database for metadata relationships
- **Nginx**: Reverse proxy and load balancer
- **TensorBoard** (optional): ML experiment visualization

---

## Building Docker Images

### 1. Build CMF Server Image

```bash
# Navigate to the repository root
cd /home/user_name/testing/deployment_k8s

# Build the CMF server image
docker build -f server/Dockerfile -t cmf-server:latest .

# Tag for your registry (replace with your registry URL)
docker tag cmf-server:latest <your-registry>/cmf-server:latest

# Push to registry
docker push <your-registry>/cmf-server:latest
```

**Alternative for Minikube:**
```bash
# Use Minikube's Docker daemon to avoid pushing to external registry
eval $(minikube docker-env)
docker build -f server/Dockerfile -t cmf-server:latest .
```

### 2. Build UI Image

```bash
# Build the UI image
docker build -f ui/Dockerfile -t cmf-ui:latest ./ui

# Tag for your registry
docker tag cmf-ui:latest <your-registry>/cmf-ui:latest

# Push to registry
docker push <your-registry>/cmf-ui:latest
```

**Alternative for Minikube:**
```bash
eval $(minikube docker-env)
docker build -f ui/Dockerfile -t cmf-ui:latest ./ui
```

### 3. Third-Party Images

The following images are pulled from public registries automatically:
- **Neo4j**: `neo4j:latest`
- **PostgreSQL**: `postgres:13`
- **Nginx**: `nginx:alpine`
- **TensorBoard**: `tensorflow/tensorflow:latest`

---

## Configuration

### 1. Update values.yaml

Edit `k8s-deployment/values.yaml` to configure your deployment:

```bash
vi k8s-deployment/values.yaml
```

**Key configurations to update:**

```yaml
# Update the CMF server image repository
cmf_service:
  image:
    repository: "<your-registry>/cmf-server"  # Replace with your image name
    tag: latest

# Update storage class if needed (leave empty for static PV binding)
storage:
  storageClassName: ""  # or "standard", "gp2", etc.

# Configure service types based on your cluster
service:
  type: NodePort  # or LoadBalancer, ClusterIP

# Neo4j authentication
neo4j_service:
  neo4jAuth: "neo4j/test1234"  # Change password for production

# Database configuration
common_env:
  POSTGRES_HOST: "postgres"
  POSTGRES_DB: "mlmd"
  POSTGRES_PORT: "5432"
```

### 2. Configure Secrets

Edit `k8s-deployment/secrets.yaml` with your database credentials:

```bash
vi k8s-deployment/secrets.yaml
```

**Update the following:**

```yaml
secrets:
  POSTGRES_USER: "myuser"          # Change for production
  POSTGRES_PASSWORD: "mypassword"  # Use a strong password
```

**Note:** For production, use Kubernetes secrets management or external secret stores (e.g., HashiCorp Vault, AWS Secrets Manager).

### 3. Storage Configuration

**For Static Persistent Volumes:**

If using pre-created PVs, ensure they exist before deployment:

```bash
kubectl get pv
```

Set `storage.storageClassName: ""` in `values.yaml`.

**For Dynamic Provisioning:**

Set the appropriate storage class:

```yaml
storage:
  storageClassName: "standard"  # or your cluster's storage class
```

Verify available storage classes:
```bash
kubectl get storageclass
```

---

## Deployment Steps

### 1. Create Namespace

```bash
export NAMESPACE="k8s-namespace"
kubectl create namespace $NAMESPACE
```

### 2. Deploy Using Helm Script

Use the provided deployment script:

```bash
chmod +x helm-deployment.sh
./helm-deployment.sh
```

**Manual Deployment (Alternative):**

```bash
helm upgrade --install cmf-deployment ./k8s-deployment \
  --namespace $NAMESPACE \
  -f ./k8s-deployment/values.yaml \
  -f ./k8s-deployment/secrets.yaml \
  --create-namespace
```

### 3. Monitor Deployment

Watch pods being created:

```bash
kubectl get pods -n $NAMESPACE -w
```

Wait for all pods to reach `Running` state:

```bash
kubectl get pods -n $NAMESPACE
```

Expected output:
```
NAME                          READY   STATUS    RESTARTS   AGE
cmf-server-xxx                1/1     Running   0          2m
neo4j-xxx                     1/1     Running   0          2m
nginx-xxx                     1/1     Running   0          2m
postgres-xxx                  1/1     Running   0          2m
ui-xxx                        1/1     Running   0          2m
```

---

## Verification

### 1. Check All Resources

```bash
# Check pods
kubectl get pods -n $NAMESPACE

# Check services
kubectl get svc -n $NAMESPACE

# Check persistent volume claims
kubectl get pvc -n $NAMESPACE

# Check persistent volumes
kubectl get pv
```

### 2. View Logs

```bash
# CMF Server logs
kubectl logs -n $NAMESPACE -l app=cmf-server --tail=50

# UI logs
kubectl logs -n $NAMESPACE -l app=ui --tail=50

# PostgreSQL logs
kubectl logs -n $NAMESPACE -l app=postgres --tail=50

# Neo4j logs
kubectl logs -n $NAMESPACE -l app=neo4j --tail=50
```

### 3. Check Pod Status

```bash
# Describe a pod for detailed information
kubectl describe pod -n $NAMESPACE <pod-name>
```

---

## Accessing Services

### 1. Get Service URLs

```bash
kubectl get svc -n $NAMESPACE
```

### 2. Access via NodePort (default)

For **Minikube**:

```bash
# Get Minikube IP
minikube ip

# Get service NodePort
kubectl get svc -n $NAMESPACE nginx -o jsonpath='{.spec.ports[0].nodePort}'

# Access UI
minikube service nginx -n $NAMESPACE
```

For **Regular Cluster**:

```bash
# Get any node IP
kubectl get nodes -o wide

# Access using: http://<node-ip>:<nodeport>
```

### 3. Access Neo4j Browser

```bash
# Get Neo4j NodePort
kubectl get svc -n $NAMESPACE neo4j -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}'

# Access: http://<node-ip>:<nodeport>
# Login with credentials from values.yaml (default: neo4j/test1234)
```

### 4. Port Forwarding (Alternative)

For local development/testing:

```bash
# Forward CMF server
kubectl port-forward -n $NAMESPACE svc/cmf-server 8080:8080

# Forward UI
kubectl port-forward -n $NAMESPACE svc/nginx 3000:80

# Forward Neo4j
kubectl port-forward -n $NAMESPACE svc/neo4j 7474:7474 7687:7687

# Forward PostgreSQL
kubectl port-forward -n $NAMESPACE svc/postgres 5432:5432
```

Access services at:
- UI: http://localhost:3000
- CMF API: http://localhost:8080
- Neo4j Browser: http://localhost:7474
- PostgreSQL: localhost:5432

---

## Uninstallation

### Remove Helm Release

```bash
helm uninstall cmf-deployment -n $NAMESPACE
```

### Delete Namespace

```bash
kubectl delete namespace $NAMESPACE
```

### Delete Persistent Volumes (Optional)

**Warning:** This will delete all data permanently.

```bash
# List PVs
kubectl get pv

# Delete specific PV
kubectl delete pv <pv-name>
```

### Clean Up Minikube Docker Images (If applicable)

```bash
eval $(minikube docker-env)
docker rmi cmf-server:latest cmf-ui:latest
```

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [CMF Documentation](https://hewlettpackard.github.io/cmf/)
- [Neo4j Kubernetes Guide](https://neo4j.com/docs/operations-manual/current/kubernetes/)

---
