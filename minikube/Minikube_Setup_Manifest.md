# Minikube + Kubernetes Setup Guide

This document provides step-by-step instructions to verify system requirements, install Minikube and Kubernetes components, deploy services, and access the application.

---

## 1. Check whether your machine supports virtualization

Check OS, CPU, memory, Docker installation, and virtualization support.

```bash
echo "---- OS Info ----" && \
lsb_release -a 2>/dev/null || cat /etc/os-release && \
echo -e "\n---- CPU & Memory ----" && \
lscpu | grep -E 'Model name|CPU\(s\)' && \
free -h | grep Mem && \
echo -e "\n---- Docker ----" && \
if command -v docker >/dev/null 2>&1; then docker --version; sudo docker info --format '{{.ServerVersion}}' 2>/dev/null || echo "Docker found but not running"; else echo "Docker not installed"; fi && \
echo -e "\n---- Virtualization Support ----" && \
egrep -wo 'vmx|svm' /proc/cpuinfo | sort | uniq || echo "No virtualization flag found"
````

---

## 2. Download and install Minikube + kubectl + start cluster

Install Minikube, kubectl, and start your Kubernetes cluster using Docker driver.

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && \
sudo install minikube-linux-amd64 /usr/local/bin/minikube && \
rm minikube-linux-amd64 && \
sudo apt-get update -y && sudo apt-get install -y conntrack curl apt-transport-https ca-certificates && \
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && rm kubectl && \
minikube start --driver=docker --cpus=4 --memory=8192 --kubernetes-version=v1.31.0 -v=7 2>&1 | tee minikube_start_verbose.log
```

---

## 3. Get all pods ready

List all pods across namespaces.

```bash
minikube kubectl -- get pods -A
```

---

## 4. Check status of Minikube and nodes

Verify Minikube, nodes, and cluster info.

```bash
minikube status
kubectl get nodes
kubectl cluster-info
```

---

## 5. Reinstall Minikube if needed

Delete all existing Minikube data and purge.

```bash
minikube delete --all –purge
```

---

## 6. Check if Docker is running

Verify Docker service status.

```bash
sudo systemctl status docker --no-pager
```

---

## 7. Build images inside Minikube cluster

Use Minikube’s Docker environment to build images.

**Build Server image:**

```bash
cd cmf/
eval $(minikube docker-env)
docker build -t cmf-server:latest -f ./server/Dockerfile .
```

**Build UI image:**

```bash
cd cmf/ui/
eval $(minikube docker-env)
docker build -t ui:latest -f ./Dockerfile .
```

---

## 8. Apply Kubernetes manifests

Deploy all required services.

**Postgres:**

```bash
kubectl apply -f kubernetes/postgres/postgres-pv.yaml
kubectl apply -f kubernetes/postgres/postgres-pvc.yaml
kubectl apply -f kubernetes/postgres/postgres-deployment.yaml
```

**Server:**

```bash
kubectl apply -f kubernetes/server/cmfserver-pv.yaml
kubectl apply -f kubernetes/server/cmfserver-pvc.yaml
kubectl apply -f kubernetes/server/cmf-deployment.yaml
```

**UI:**

```bash
kubectl apply -f kubernetes/ui/ui-deployment.yaml
```

**Tensorboard:**

```bash
kubectl apply -f kubernetes/server/tensorboard.yaml
```

**Nginx:**

```bash
kubectl apply -f kubernetes/nginx/nginx-configmap.yaml
kubectl apply -f kubernetes/nginx/nginx-deployment.yaml
```

**Neo4j**

```bash
kubectl apply -f kubernetes/neo4j/neo4j-pv.yaml
kubectl apply -f kubernetes/neo4j/neo4j-pvc.yaml
kubectl apply -f kubernetes/neo4j/neo4j.yaml
```

---

## 9. Check Minikube status

Get cluster details, IP, and services.

```bash
minikube status
minikube ip
kubectl get svc nginx -o wide
minikube profile list
minikube service nginx –url
```

---

## 10. Do port forwarding

Forward Nginx service port to host and verify running process.

```bash
nohup kubectl port-forward --address 0.0.0.0 service/nginx 30080:80 > /tmp/port-forward.log 2>&1 &
sleep 2 && ps aux | grep "port-forward" | grep -v grep
```

## 11. Do port forwarding

Forward Neo4j service port to host and verify running process.

```bash
nohup kubectl port-forward --address 0.0.0.0 service/neo4j 7474:7474 > /tmp/port-forward.log 2>&1 &
sleep 2 && ps aux | grep "port-forward" | grep -v grep
```

```bash
nohup kubectl port-forward --address 0.0.0.0 service/neo4j 7687:7687 > /tmp/port-forward.log 2>&1 &
sleep 2 && ps aux | grep "port-forward" | grep -v grep
```


---

## 12. Access the application

Open the following URL in a browser:

```
http://x.x.x.x:30080
```

---

## 13. Initialize CMF locally

Copy example files and initialize CMF local setup.

```bash
cmf init local --path /home/username/local-storage --git-remote-url https://github.com/abc/hi --cmf-server-url http://x.x.x.x:30080
```

---

## 14. Run test script and push metadata

Execute test script and push CMF metadata.

```bash
sh test_script
cmf metadata push
```

---

## 15. Restart pods after image rebuild

Whenever a new image is built, restart the corresponding pod.

**Restart deployment:**

```bash
kubectl rollout restart deployment ui-deployment
```

**Watch rollout status:**

```bash
kubectl rollout status deployment ui-deployment
```

**Verify new pod is running:**

```bash
kubectl get pods -l app=ui
```


