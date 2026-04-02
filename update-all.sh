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

echo "🗄️ Applying DATABASE layer (PV → PVC → Service → StatefulSet)..."

# AUTH DB
kubectl apply -f k8s/postgres/auth_db/pv.yaml
kubectl apply -f k8s/postgres/auth_db/pvc.yaml
kubectl apply -f k8s/postgres/auth_db/service.yaml
kubectl apply -f k8s/postgres/auth_db/statefulset.yaml

# USER DB
kubectl apply -f k8s/postgres/user_db/pv.yaml
kubectl apply -f k8s/postgres/user_db/pvc.yaml
kubectl apply -f k8s/postgres/user_db/service.yaml
kubectl apply -f k8s/postgres/user_db/statefulset.yaml

# PRODUCT DB
kubectl apply -f k8s/postgres/product_db/pv.yaml
kubectl apply -f k8s/postgres/product_db/pvc.yaml
kubectl apply -f k8s/postgres/product_db/service.yaml
kubectl apply -f k8s/postgres/product_db/statefulset.yaml

# ORDER DB
kubectl apply -f k8s/postgres/order_db/pv.yaml
kubectl apply -f k8s/postgres/order_db/pvc.yaml
kubectl apply -f k8s/postgres/order_db/service.yaml
kubectl apply -f k8s/postgres/order_db/statefulset.yaml

echo "⏳ Waiting for DBs to be ready..."
sleep 10

echo "🔐 Applying SECRETS..."

kubectl apply -f k8s/auth/secret.yaml
kubectl apply -f k8s/user/secret.yaml
kubectl apply -f k8s/product/secret.yaml
kubectl apply -f k8s/order/secret.yaml

echo "⚙️ Applying SERVICES + DEPLOYMENTS..."

kubectl apply -f k8s/auth/
kubectl apply -f k8s/user/
kubectl apply -f k8s/product/
kubectl apply -f k8s/order/
kubectl apply -f k8s/ui/

echo "🌐 Applying INGRESS..."

kubectl apply -f k8s/ingress/

echo "🔄 Restarting deployments..."

kubectl rollout restart deployment auth-service
kubectl rollout restart deployment user-service
kubectl rollout restart deployment product-service
kubectl rollout restart deployment order-service
kubectl rollout restart deployment streamlit-ui

echo "📊 Current pods:"
kubectl get pods

echo "🌍 Access your app at: http://localhost:8085"
echo "✅ Deployment complete!"