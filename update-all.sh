#!/bin/bash

set -e

CLUSTER_NAME="microservices-cluster"

echo "🚀 Building Docker images..."

docker build -t auth-service:latest ./auth-service
docker build -t user-service:latest ./user-service
docker build -t product-service:latest ./product-service
docker build -t order-service:latest ./order-service
docker build -t streamlit-ui:latest ./ui

echo "📦 Loading images into KIND..."

kind load docker-image auth-service:latest --name $CLUSTER_NAME
kind load docker-image user-service:latest --name $CLUSTER_NAME
kind load docker-image product-service:latest --name $CLUSTER_NAME
kind load docker-image order-service:latest --name $CLUSTER_NAME
kind load docker-image streamlit-ui:latest --name $CLUSTER_NAME

echo "🗄️ Applying Postgres (ConfigMap + StatefulSet + Service)..."

# FIXED PATH ✅
kubectl apply -f k8s/postgres/

echo "⏳ Waiting for Postgres to be ready..."

# BETTER THAN SLEEP ✅
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s

echo "🚀 Deploying Microservices using Helm..."

helm upgrade --install microservices ./microservices-chart

echo "⏳ Waiting for microservices to be ready..."

kubectl wait --for=condition=available deployment/auth-service --timeout=120s || true
kubectl wait --for=condition=available deployment/user-service --timeout=120s || true
kubectl wait --for=condition=available deployment/product-service --timeout=120s || true
kubectl wait --for=condition=available deployment/order-service --timeout=120s || true
kubectl wait --for=condition=available deployment/streamlit-ui --timeout=120s || true

echo "🔄 Restarting deployments (optional)..."

kubectl rollout restart deployment auth-service || true
kubectl rollout restart deployment user-service || true
kubectl rollout restart deployment product-service || true
kubectl rollout restart deployment order-service || true
kubectl rollout restart deployment streamlit-ui || true

echo "📊 Current Pods:"
kubectl get pods -o wide

echo "📡 Services:"
kubectl get svc

echo "🌐 Ingress:"
kubectl get ingress

echo "✅ Deployment complete!"