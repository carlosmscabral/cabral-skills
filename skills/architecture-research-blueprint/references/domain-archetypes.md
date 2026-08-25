# Architectural Domain Decomposition Archetypes

When executing **Phase 1 (Parallel Specialist Research)** of the `architecture-research-blueprint` workflow, decompose the problem space into **4 to 6 orthogonal, mutually exclusive macro-domains**.

Select or adapt one of the canonical archetypes below, or synthesize a custom decomposition tailored to the project's primary architectural drivers.

---

## Archetype 1: Cloud-Native Microservices & Event-Driven Platforms

Best suited for distributed service meshes, decoupled asynchronous workflows, and high-throughput transactional backends.

- **Domain 1: Edge Ingress, API Gateway & Traffic Routing**
  - Global Anycast Load Balancing (Cloud Load Balancing, Envoy Gateway).
  - API Gateway management (Apigee, Kong), rate limiting, SSL termination, and WAF security (Cloud Armor).
- **Domain 2: Compute Orchestration & Service Mesh**
  - Workload scheduling (GKE Autopilot / Cloud Run / Kubernetes).
  - Inter-service communication, mTLS service mesh (Istio / Cloud Service Mesh), and auto-scaling heuristics (HPA, KEDA).
- **Domain 3: Asynchronous Event Mesh & Stream Processing**
  - Event brokers (Pub/Sub, Apache Kafka, Eventarc), dead-letter queuing, and stream processing engines (Dataflow / Apache Flink).
  - Event schemas, schema registries (Avro, Protobuf), and idempotency guarantees (at-least-once vs exactly-once).
- **Domain 4: Stateful Persistence, Polyglot Data & Caching**
  - Relational OLTP (Cloud SQL, AlloyDB, Spanner), document/NoSQL (Firestore, MongoDB), and in-memory caches (Memorystore Redis / Valkey).
  - Connection pooling (PgBouncer), database replication, and read/write splitting.
- **Domain 5: Observability, Distributed Tracing & Resilience**
  - OpenTelemetry instrumentation, distributed tracing (Cloud Trace), structured logging (Cloud Logging), and Prometheus/Grafana metrics.
  - Circuit breakers, retry budgets, rate limiters, and chaos testing strategies.

---

## Archetype 2: Generative AI & Autonomous Agent Platforms

Best suited for multi-agent systems, LLM orchestration, Retrieval-Augmented Generation (RAG), and agentic workflows.

- **Domain 1: Model Gateway, Routing & Inferencing Infrastructure**
  - Model multiplexing (Vertex AI Model Garden, Gemini APIs, self-hosted vLLM/Ollama on GKE GPUs).
  - Dynamic fallback routing, prompt caching, token rate limiting, and inference latency optimization.
- **Domain 2: Agent Orchestration & Execution Runtime**
  - Multi-agent orchestration frameworks (Google Agent Development Kit / ADK, LangGraph, CrewAI).
  - Execution sandbox environments, tool calling safety, dynamic session management, and state machine persistence.
- **Domain 3: Knowledge Retrieval, Vector Stores & Hybrid Search**
  - Vector databases (Vertex AI Vector Search, AlloyDB Omni / pgvector, Pinecone).
  - Document chunking pipelines, embedding generation, reranking models, and hybrid keyword/semantic search.
- **Domain 4: Identity, Delegated Auth & Tool Access Control**
  - 3-legged OAuth (3LO), Agent Identity Auth Manager, Workload Identity Federation.
  - Granular tool-level IAM permissions, privilege escalation prevention, and audit logging for agent actions.
- **Domain 5: AI FinOps, Guardrails & Quality Evaluation**
  - Token consumption tracking, cost attribution per user/organization, model evaluation (LLM-as-a-judge, Vertex AI Gen AI Evaluation).
  - Safety guardrails (Llama Guard, Cloud DLP, prompt injection defense, hallucination detection).

---

## Archetype 3: Enterprise Data Mesh & Real-Time Analytics

Best suited for analytical platforms, data warehousing, business intelligence, and lakehouse architectures.

- **Domain 1: Ingestion & Stream Ingestion Pipelines**
  - Batch ingestion (Storage Transfer Service, Datastream CDC) and real-time streaming (Pub/Sub, Kafka).
  - Data ingestion validation, schema evolution handling, and rate decoupling.
- **Domain 2: Storage Lakehouse & Warehouse Layer**
  - Columnar storage, open table formats (Apache Iceberg, Delta Lake on Cloud Storage).
  - Scalable data warehouse compute (BigQuery editions, slot reservations, BI Engine acceleration).
- **Domain 3: Transformation, Modeling & Orchestration**
  - ETL/ELT pipelines (dbt, Dataform, Cloud Composer / Apache Airflow).
  - Incremental data modeling, medallion architecture (Bronze $\to$ Silver $\to$ Gold), and partition/clustering optimization.
- **Domain 4: Data Governance, Cataloging & Quality**
  - Data cataloging (Dataplex), metadata discovery, data lineage tracking, and automated data quality assertions.
  - Column-level and row-level access control, data masking, and compliance classification.
- **Domain 5: Analytics Serving & API Exposure**
  - Low-latency analytical APIs, semantic layers (Looker / Cube.js), caching layers, and reverse ETL syncs.

---

## Archetype 4: Multi-Tenant SaaS Applications

Best suited for B2B software architectures serving multiple distinct organizations/customers with strict isolation requirements.

- **Domain 1: Tenant Identity, Hierarchy & Governance**
  - Tenant organization models, identity provisioning (Cloud Identity, Firebase Auth, Okta), and role-based access control (RBAC).
  - Tamper-proof tenant context propagation (JWT claims) across all ingress points.
- **Domain 2: Edge Routing & Tenant Ingress**
  - Custom domain management, SSL certificate provisioning, path-based vs subdomain tenant routing.
  - Per-tenant rate limiting and DDoS insulation at the edge (Cloud Armor / Apigee).
- **Domain 3: Workload Isolation & Compute Strategy**
  - Compute partitioning models: Silo (dedicated clusters/namespaces) vs Pooled (shared compute with sandboxing).
  - Kernel isolation (gVisor / GKE Sandbox), Kubernetes `ResourceQuotas`, and PriorityClasses.
- **Domain 4: Multi-Tenant Data Persistence**
  - Database partitioning: Silo (dedicated databases/instances), Bridge (shared database with dedicated schemas), or Pooled (shared schema with Row-Level Security / RLS).
  - Schema migration scaling ($O(N)$ vs $O(1)$) and automated cross-tenant data leak prevention.
- **Domain 5: Tenant FinOps & Metering**
  - Per-tenant resource consumption attribution (GKE Cost Allocation to BigQuery), tier-based billing, and idle capacity overhead ("Silo tax") optimization.

---

## Archetype 5: Hybrid-Cloud & Zero-Trust Enterprise Networks

Best suited for enterprise infrastructure spanning on-premises data centers and multi-cloud environments.

- **Domain 1: Interconnect, Transit VPCs & Hybrid Connectivity**
  - Dedicated Interconnect, Cloud VPN, Cloud Router BGP routing, and Hub-and-Spoke Network Topology.
  - Redundancy topologies (99.99% SLA dual-region active-active interconnects).
- **Domain 2: Zero-Trust Perimeter Security & Micro-segmentation**
  - VPC Service Controls (VPC-SC) perimeters, Private Service Connect (PSC), and firewall policies (hierarchical and tag-based).
  - Identity-Aware Proxy (IAP) and BeyondCorp Enterprise zero-trust application access.
- **Domain 3: Unified Identity & Credential Federation**
  - Workload Identity Federation (AWS, Azure, OIDC to GCP), Keyless CI/CD authentication, and Active Directory federation.
- **Domain 4: Shared Services & Governance**
  - Enterprise landing zones, resource hierarchy (Organizations $\to$ Folders $\to$ Projects), Organization Policies, and KMS / CMEK key management hierarchies.
- **Domain 5: Compliance, Forensics & Audit Logging**
  - Centralized log sink aggregation (Cloud Logging export to BigQuery/SIEM), VPC Flow Logs analysis, and immutable audit trails (Bucket Lock WORM).
