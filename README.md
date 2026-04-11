# Production-Grade Microservices Platform with Kubernetes, Istio, Argo CD & Observability

---

## Overview

This project is an advanced upgrade of a microservices-based eCommerce system, evolved into a production-grade cloud-native platform that closely mimics real-world distributed systems.

It demonstrates not just deployment, but **end-to-end platform engineering**, including:

- Kubernetes-based microservices architecture with proper service isolation  
- Istio service mesh for secure, observable service-to-service communication  
- GitOps workflow using Argo CD for declarative and automated deployments  
- Helm-based templating for scalable and reusable infrastructure  
- CI/CD pipeline using Jenkins for automated build and delivery  
- Full observability stack with Prometheus, Grafana, and Kiali  
- Real-time alerting using Alertmanager integrated with Slack  
- Developer productivity improvements using K9s for live debugging  

The project focuses heavily on **real debugging scenarios**, such as service mesh issues, database connectivity failures, GitOps conflicts, and stateful workload behavior.

---

## Architecture

<img width="1354" height="513" alt="Screenshot 2026-04-11 at 2 52 12 PM" src="https://github.com/user-attachments/assets/89b01518-eefc-434b-9f63-5be265327b86" />

Client → Ingress → Service Mesh (Istio) → Microservices → Databases  

Request Flow:

Client → NGINX Ingress → Istio Ingress Gateway → Kubernetes Services → Pods (FastAPI + Envoy Sidecars) → PostgreSQL  

- Ingress handles external routing  
- Istio manages internal traffic, security, and observability  
- Services abstract pod networking  
- Each microservice communicates over the mesh with telemetry enabled  

---

## Microservices

Auth Service  
- Handles authentication and JWT generation  
- Acts as the entry point for identity  
- DB: auth_db  

User Service  
- Manages user data and syncs with Auth Service  
- Demonstrates inter-service communication  
- DB: user_db  

Product Service  
- Maintains product catalog  
- DB: product_db  

Order Service  
- Handles order creation  
- Communicates with User and Product services  
- DB: order_db  

Streamlit UI  
- Lightweight frontend for interacting with APIs  
- Helps validate end-to-end flow  

Each service is independently deployable and follows **database-per-service architecture**.

---

## Authentication Flow

1. Client sends login request to Auth Service  
2. Auth Service validates credentials and generates JWT  
3. Token is returned to client  
4. Client includes token in Authorization header  
5. Other services validate token using shared secret  

This ensures **stateless authentication across distributed services**.

---

## Database Architecture

auth-service → auth_db  
user-service → user_db  
product-service → product_db  
order-service → order_db  

- Each service owns its schema and data  
- No cross-database access allowed  
- Improves fault isolation and scalability  
- Helps simulate real microservice boundaries  

---

## Kubernetes Components

- Deployments for stateless services with replica scaling  
- StatefulSets for PostgreSQL with persistent storage  
- Services (ClusterIP) for internal DNS-based communication  
- Ingress for external traffic routing  
- Secrets for environment variables and credentials  
- Persistent Volumes and PVCs for durable storage  

Special focus was given to understanding **StatefulSet lifecycle and persistence behavior**.

---

## Helm

- All services are deployed using Helm charts  
- Centralized values.yaml for configuration  
- Enables easy upgrades, rollbacks, and environment changes  
- Reduces duplication across service manifests  

---

## Argo CD (GitOps)

<img width="1454" height="739" alt="Screenshot 2026-04-11 at 12 59 15 PM copy" src="https://github.com/user-attachments/assets/7458cf1e-8ef9-4ded-a3ec-3f99e44847f9" />

- Entire system managed declaratively via Git  
- Argo CD continuously syncs cluster state with repository  
- Eliminates configuration drift  
- Handles automated deployments and rollbacks  

A key learning was resolving **Helm vs Argo CD conflicts**, enforcing Git as the single source of truth.

---

## CI/CD Pipeline (Jenkins)

<img width="1454" height="739" alt="Screenshot 2026-04-11 at 12 58 03 PM" src="https://github.com/user-attachments/assets/f403f4b2-29aa-4896-ae6e-26ddc1d3876a" />

- Jenkins is used as the Continuous Integration layer for the platform  
- Pipeline is triggered manually (or via SCM trigger) by the developer  
- Automates build, versioning, and GitOps trigger flow  

Pipeline Flow:

1. Checkout latest code from GitHub  
2. Build Docker images for all services  
3. Push images to Docker Hub  
4. Update Helm values.yaml with new image tags (BUILD_NUMBER)  
5. Commit and push updated values.yaml back to GitHub  
6. Argo CD detects changes and automatically syncs deployment  

Key Highlights:

- Fully automated image lifecycle  
- Tight integration with GitOps workflow  
- No direct kubectl/helm deploy from CI (clean separation of concerns)  
- Enables reproducible and versioned deployments  

---

## Istio Service Mesh

<img width="1456" height="739" alt="Screenshot 2026-04-11 at 1 40 02 PM" src="https://github.com/user-attachments/assets/39fe3d5d-059c-4664-9fbd-811df8963e5a" />

- Automatic sidecar injection using Envoy proxies  
- Mutual TLS (mTLS) for secure communication  
- Traffic interception and routing at L7  
- Deep observability with metrics and traces  

Special handling for PostgreSQL:

- Database traffic excluded from sidecar interception  
- Avoids TCP connection failures caused by Envoy  
- Demonstrates real-world service mesh edge cases  

---

## Observability

<img width="1454" height="739" alt="Screenshot 2026-04-11 at 12 59 33 PM" src="https://github.com/user-attachments/assets/3252e6fa-cffc-4979-bae8-f6bcc0152405" />

Prometheus  
- Collects metrics from services and nodes  
- Used for alerting and monitoring  

<img width="1454" height="739" alt="Screenshot 2026-04-11 at 12 59 26 PM" src="https://github.com/user-attachments/assets/43823203-8fd2-4226-a44d-3bf7ed90cece" />

Grafana  
- Visual dashboards for system health  
- Tracks CPU, memory, request rates, and errors  

Kiali  
- Visualizes service mesh topology  
- Shows request flow, traffic distribution, and mTLS status  
- Useful for debugging service-to-service communication  

---

## Alerting

<img width="1454" height="739" alt="Screenshot 2026-04-11 at 1 00 10 PM" src="https://github.com/user-attachments/assets/abd062cd-755a-495f-8433-33cb211a2f8d" />
<img width="1454" height="739" alt="Screenshot 2026-04-11 at 1 00 17 PM" src="https://github.com/user-attachments/assets/aa1bbc8b-9959-4939-bfcc-473140701365" />

- Alertmanager configured with Slack integration  
- Sends real-time alerts to a Slack channel  

Monitored conditions include:
- High CPU usage  
- Memory spikes  
- Pod restarts  
- Service failures  

Also involved handling **secret management and preventing webhook leaks**.

---

## Tooling

<img width="1456" height="606" alt="Screenshot 2026-04-11 at 1 28 02 PM" src="https://github.com/user-attachments/assets/f030555d-d6b1-4e8d-942b-8bd0946427f6" />

K9s  
- Terminal-based Kubernetes UI  
- Real-time visibility into pods, logs, and resources  
- Speeds up debugging significantly  

---

## Routing

/login → auth-service  
/users → user-service  
/products → product-service  
/orders → order-service  
/ → streamlit-ui  

Routing is handled via ingress and service abstraction.

---

## Issues Solved

- Istio breaking PostgreSQL connections → fixed via port exclusion and TCP handling  
- Argo CD overriding Helm changes → enforced GitOps workflow  
- Secret leak (Slack webhook) → removed from Git history and moved to Kubernetes Secrets  
- CrashLoopBackOff due to DB misconfig → fixed environment variables and retry logic  
- StatefulSet confusion → understood persistent volumes and init behavior  
- CI/CD drift issues → fixed by enforcing Jenkins → Git → Argo CD flow  

These reflect **real production debugging scenarios**.

---

## Setup

Create cluster:
kind create cluster --name microservices-cluster --config kind-config.yaml

Install Istio:
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled

Install ArgoCD:
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

Port-forward dashboards:
kubectl port-forward svc/kiali -n istio-system 20001:20001
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
kubectl port-forward svc/argocd-server -n argocd 8080:443

---

## Status

- All microservices running and stable  
- PostgreSQL databases connected correctly  
- Istio mesh fully operational  
- Argo CD managing deployments  
- Jenkins CI/CD pipeline integrated and working  
- Monitoring dashboards active  
- Slack alerting functional  

---

## Future

- Event-driven architecture (Kafka / RabbitMQ)  
- Horizontal Pod Autoscaling (HPA)  
- Canary deployments using Istio  
- Distributed tracing with Jaeger  

---

## Conclusion

This project represents a **complete, production-style microservices platform**, combining:

Kubernetes + Istio + Helm + Argo CD + Jenkins + Prometheus + Grafana + Kiali + Slack Alerts  

It highlights real-world challenges in building distributed systems and demonstrates how to **design, deploy, debug, and operate them effectively at scale**.
