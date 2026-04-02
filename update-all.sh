#!/bin/bash

set -e

CLUSTER_NAME="microservices-cluster"

echo "Building Docker images..."

docker build -t auth-service:latest ./auth-service
docker build -t user-service:latest ./user-service
docker build -t product-service:latest ./product-service
docker build -t order-service:latest ./order-service
docker build -t streamlit-ui:latest ./ui

echo "Loading images into KIND..."

kind load docker-image auth-service:latest --name $CLUSTER_NAME
kind load docker-image user-service:latest --name $CLUSTER_NAME
kind load docker-image product-service:latest --name $CLUSTER_NAME
kind load docker-image order-service:latest --name $CLUSTER_NAME
kind load docker-image streamlit-ui:latest --name $CLUSTER_NAME

echo "Applying Kubernetes manifests..."

kubectl apply -f k8s/postgres/
kubectl apply -f k8s/auth/
kubectl apply -f k8s/user/
kubectl apply -f k8s/product/
kubectl apply -f k8s/order/
kubectl apply -f k8s/ui/
kubectl apply -f k8s/ingress/

echo "Restarting deployments..."

kubectl rollout restart deployment auth-service
kubectl rollout restart deployment user-service
kubectl rollout restart deployment product-service
kubectl rollout restart deployment order-service
kubectl rollout restart deployment streamlit-ui


echo "Access your app at: http://localhost:8085"
echo "Deployment complete!"