# Microservices Platform on Kubernetes with Istio Service Mesh

## Overview

This project demonstrates a production-style microservices architecture deployed on Kubernetes. It includes multiple backend services, each with its own database, exposed through an ingress layer and integrated with an Istio service mesh for secure communication and observability.

The system is designed to reflect real-world distributed systems with proper separation of concerns, database isolation, and service-to-service communication patterns.

---

## Architecture

<img width="1209" height="537" alt="Screenshot 2026-04-04 at 12 04 27 PM" src="https://github.com/user-attachments/assets/d4a421f8-7864-457d-8b18-b4cef97b2264" />

Client → Ingress → Services → Pods → Databases

Request Flow:

Client (Browser / curl)  
→ NGINX Ingress (Layer 7 Routing)  
→ Kubernetes Services (ClusterIP)  
→ Pods (FastAPI Applications)  
→ PostgreSQL Databases (per service)

---

## Services

Auth Service  
- Handles authentication (login, register, JWT generation)  
- Database: auth_db  

User Service  
- Manages user profile data  
- Database: user_db  

Product Service  
- Manages product catalog  
- Database: product_db  

Order Service  
- Handles order creation and validation  
- Database: order_db  

Streamlit UI  
- Frontend interface for interacting with the system  

---

## Authentication Flow

1. User sends login request to Auth Service  
2. Auth Service validates credentials and generates a JWT token  
3. Token is returned to the client  
4. Client includes token in Authorization header  
5. Other services validate token using shared secret  

---

## Database Architecture

Each service owns its own PostgreSQL database. No service directly accesses another service’s database.

auth-service → auth-db  
user-service → user-db  
product-service → product-db  
order-service → order-db  

This ensures isolation, scalability, and fault tolerance.

---

## Ingress Routing

/login, /register → auth-service  
/users → user-service  
/products → product-service  
/orders → order-service  
/ → streamlit-ui  

---

## Kubernetes Components

<img width="1451" height="707" alt="Screenshot 2026-04-04 at 11 30 07 AM" src="https://github.com/user-attachments/assets/1baeb866-b36a-404d-98f6-ebf37bf51105" />

- Deployments for stateless services  
- StatefulSets for PostgreSQL databases  
- Services (ClusterIP) for internal communication  
- Persistent Volumes (PV)  
- Persistent Volume Claims (PVC)  
- Secrets for environment variables  
- Ingress for external routing  

---

## Istio Service Mesh

<img width="1451" height="707" alt="Screenshot 2026-04-04 at 11 25 20 AM" src="https://github.com/user-attachments/assets/9e0cd549-9801-40b8-af88-4abe54042a50" />

- Sidecar injection enabled for all services  
- Mutual TLS (mTLS) enforced  
- Traffic routing and observability through Istio  
- Kiali used for service graph visualization  
- Versioned traffic using labels (version: v1)  

---

## Key Issues Solved

Database Connection Issues  
- Fixed incorrect psycopg2 configuration (used dbname instead of database)

StatefulSet Persistence Behavior  
- Learned that environment variables do not reinitialize databases once volumes are created

Readiness and Liveness Probe Failures  
- Adjusted probe timing using initialDelaySeconds to allow database initialization

Data Inconsistency Across Services  
- Resolved ID mismatch by resetting sequences using:
  TRUNCATE TABLE <table> RESTART IDENTITY;

Istio Protocol Sniffing Issue  
- Fixed database communication by explicitly naming ports:
  name: tcp-postgresql

YAML Strict Decoding Errors  
- Removed invalid fields such as metadata.version

---

## Setup and Deployment

1. Create Kubernetes Cluster (Kind)

   kind create cluster --name microservices-cluster --config kind-config.yaml

2. Build Docker Images

   docker build -t auth-service:latest ./auth-service  
   docker build -t user-service:latest ./user-service  
   docker build -t product-service:latest ./product-service  
   docker build -t order-service:latest ./order-service  
   docker build -t streamlit-ui:latest ./ui  

3. Load Images into Kind

   kind load docker-image auth-service:latest --name microservices-cluster  
   kind load docker-image user-service:latest --name microservices-cluster  
   kind load docker-image product-service:latest --name microservices-cluster  
   kind load docker-image order-service:latest --name microservices-cluster  
   kind load docker-image streamlit-ui:latest --name microservices-cluster  

4. Deploy Kubernetes Resources

   kubectl apply -f k8s/postgres/  
   kubectl apply -f k8s/auth/  
   kubectl apply -f k8s/user/  
   kubectl apply -f k8s/product/  
   kubectl apply -f k8s/order/  
   kubectl apply -f k8s/ui/  
   kubectl apply -f k8s/ingress/  

5. Restart Deployments

   kubectl rollout restart deployment auth-service  
   kubectl rollout restart deployment user-service  
   kubectl rollout restart deployment product-service  
   kubectl rollout restart deployment order-service  
   kubectl rollout restart deployment streamlit-ui  

---

## Observability

Kiali Dashboard  
- Visualizes service-to-service communication  
- Shows traffic flow, versions, and mTLS status  

Istio Metrics  
- Provides insights into request latency, error rates, and traffic distribution  

---

## Key Learnings

- Importance of database-per-service architecture  
- Debugging distributed systems across multiple layers (app, network, infra)  
- Handling stateful workloads in Kubernetes  
- Understanding readiness and liveness probes  
- Working with Istio service mesh and mTLS  
- Identifying and fixing configuration and networking issues in real-world setups  

---

## Current Status

The system is fully functional with:

- All services running and communicating correctly  
- Independent databases per service  
- Secure communication via Istio mTLS  
- Observability through Kiali  
- Stable Kubernetes deployment  

---

## Future Improvements

- Event-driven architecture using Kafka or RabbitMQ  
- Observability stack using Prometheus and Grafana  
- CI/CD pipeline integration  
- Database migrations and schema versioning  
- Autoscaling using HPA  

---

## Conclusion

This project demonstrates a complete end-to-end microservices system built with Kubernetes and Istio. It reflects real-world challenges and solutions involved in deploying, debugging, and maintaining distributed systems at scale.
