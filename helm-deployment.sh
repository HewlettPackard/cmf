#!/bin/bash
set -e

NAMESPACE="cmf-deployment"
CHART_DIR="./cmf-deployment"

echo "Checking Kubernetes connection..."
kubectl cluster-info > /dev/null

echo "Creating namespace if not exists..."
kubectl get namespace $NAMESPACE >/dev/null 2>&1 || \
kubectl create namespace $NAMESPACE

echo "Installing Helm chart..."
helm upgrade --install $NAMESPACE $CHART_DIR \
  --namespace $NAMESPACE \
  -f $CHART_DIR/values.yaml

echo "Deployment status:"
kubectl get pods -n $NAMESPACE
kubectl get svc -n $NAMESPACE

echo "CMF deployed successfully."