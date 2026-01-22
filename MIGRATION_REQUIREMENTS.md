# FTGO Monolith to Microservices Migration Requirements

## Overview

This document outlines the requirements for migrating the FTGO (Food To Go) application from its current modular monolith architecture to a fully distributed microservices architecture. The FTGO application is a food delivery platform that manages the complete order lifecycle, coordinating actions across consumers, restaurants, and couriers.

## Current State

The FTGO application is currently deployed as a single Spring Boot application (`ftgo-application`) that aggregates four main service modules:

**Order Service** (`ftgo-order-service`) orchestrates the order lifecycle and coordinates with other services. It currently makes direct method calls to `ConsumerService.validateOrderForConsumer()` and directly accesses `RestaurantRepository` and `CourierRepository` for data retrieval and courier assignment.

**Consumer Service** (`ftgo-consumer-service`) handles consumer validation and management. It validates orders by checking consumer existence and order total constraints.

**Restaurant Service** (`ftgo-restaurant-service`) manages restaurant profiles, menus, and menu items. The Order Service directly queries the `RestaurantRepository` to fetch restaurant and menu data during order creation.

**Courier Service** (`ftgo-courier-service`) manages courier availability and delivery scheduling. The Order Service directly accesses `CourierRepository.findAllAvailable()` to assign couriers to orders.

### Key Architectural Issues

The current architecture has several characteristics that need to be addressed during migration:

All services share a single MySQL database with direct repository access through the `ftgo-domain` module. This tight coupling means services cannot be deployed or scaled independently, and schema changes in one service can affect others.

The `OrderService.createOrder()` method is a single `@Transactional` operation that spans multiple service boundaries. It validates the consumer, fetches restaurant data, creates the order, and all within one database transaction. This pattern cannot work in a distributed environment where each service has its own database.

Direct method calls between services (e.g., `consumerService.validateOrderForConsumer()`) create compile-time dependencies that prevent independent deployment. Similarly, direct repository access (e.g., `restaurantRepository.findById()`, `courierRepository.findAllAvailable()`) bypasses service boundaries entirely.

The application does have some positive characteristics that will facilitate migration: service modules already have API-implementation separation (e.g., `ftgo-consumer-service-api`, `ftgo-restaurant-service-api`), Prometheus metrics and Spring Boot Actuator are already configured, and the codebase follows domain-driven design principles with clear aggregate boundaries.

## Migration Goal

Transform the FTGO monolith into a set of independently deployable microservices that communicate via well-defined APIs, each owning its own data, while maintaining the same business functionality and improving scalability, resilience, and team autonomy.

## Migration Phases

### Phase 1: Database Separation

The first phase focuses on extracting each service's data into its own database, breaking the shared database dependency.

**Objectives:**
- Create separate database schemas for Order, Consumer, Restaurant, and Courier services
- Migrate existing data to the appropriate service databases
- Update each service to connect only to its own database
- Remove cross-service repository dependencies from the `ftgo-domain` module

**Technical Approach:**
- Create four separate MySQL databases: `ftgo_orders`, `ftgo_consumers`, `ftgo_restaurants`, `ftgo_couriers`
- Move entity classes from `ftgo-domain` into their respective service modules
- Update JPA configurations to use service-specific datasources
- Implement data migration scripts using Flyway

**Key Entities by Service:**
- Order Service: `Order`, `OrderLineItem`, `OrderState`
- Consumer Service: `Consumer`
- Restaurant Service: `Restaurant`, `RestaurantMenu`, `MenuItem`
- Courier Service: `Courier`, `Plan`, `Action`

### Phase 2: API Communication

Replace direct method calls and repository access with REST API calls between services.

**Objectives:**
- Define REST API contracts for inter-service communication
- Implement API clients in each service that needs to call another service
- Replace direct `ConsumerService` method calls with Consumer Service API calls
- Replace direct `RestaurantRepository` access with Restaurant Service API calls
- Replace direct `CourierRepository` access with Courier Service API calls

**Technical Approach:**
- Leverage existing API modules (`ftgo-consumer-service-api`, `ftgo-restaurant-service-api`, `ftgo-courier-service-api`) to define DTOs and contracts
- Implement REST controllers in each service exposing the required endpoints
- Create Feign clients or RestTemplate-based clients for inter-service communication
- Add circuit breakers (Resilience4j) for fault tolerance

**API Endpoints Required:**
- Consumer Service: `POST /consumers/{id}/validate` - Validate consumer for order
- Restaurant Service: `GET /restaurants/{id}` - Get restaurant with menu
- Courier Service: `GET /couriers/available` - Get available couriers, `POST /couriers/{id}/actions` - Assign delivery actions

### Phase 3: Distributed Transactions (Saga Pattern)

Implement the Saga pattern to handle distributed transactions that span multiple services.

**Objectives:**
- Replace the single `@Transactional` operation in `OrderService.createOrder()` with a saga
- Define compensating transactions for rollback scenarios
- Implement saga orchestration for the order creation process

**Technical Approach:**
- Implement a choreography-based or orchestration-based saga for order creation
- The Create Order Saga will include these steps:
  1. Create Order in PENDING state
  2. Validate Consumer (call Consumer Service)
  3. Validate Restaurant and get menu items (call Restaurant Service)
  4. Approve Order (update Order state to APPROVED)
  5. Schedule Delivery (call Courier Service to assign courier)
- Define compensating transactions:
  - If consumer validation fails: Reject Order
  - If restaurant validation fails: Reject Order
  - If courier assignment fails: Reject Order

**Saga Implementation Options:**
- Use an event-driven approach with Kafka for choreography
- Use a saga orchestrator service for orchestration (recommended for complex workflows)
- Consider using frameworks like Eventuate Tram Sagas

### Phase 4: Independent Deployments

Extract each service as a standalone Spring Boot application that can be deployed independently.

**Objectives:**
- Create separate Spring Boot applications for each service
- Configure independent build and deployment pipelines
- Containerize each service with its own Dockerfile
- Set up Kubernetes deployments for each service

**Technical Approach:**
- Create new main application classes for each service (replacing the aggregated `FtgoApplicationMain`)
- Configure separate `application.properties` for each service with its own database connection
- Create individual Dockerfiles for each service
- Define Kubernetes Deployment, Service, and ConfigMap resources for each service
- Implement health checks and readiness probes

**Service Ports (suggested):**
- Order Service: 8081
- Consumer Service: 8082
- Restaurant Service: 8083
- Courier Service: 8084

### Phase 5: Service Discovery and API Gateway

Implement service discovery and an API gateway for dynamic service location and unified entry point.

**Objectives:**
- Deploy a service registry for dynamic service discovery
- Implement an API gateway for routing, load balancing, and cross-cutting concerns
- Configure services to register with the service registry
- Set up load balancing between service instances

**Technical Approach:**
- Deploy Netflix Eureka or HashiCorp Consul as the service registry
- Implement Spring Cloud Gateway or Kong as the API gateway
- Configure each service with Spring Cloud Netflix Eureka Client
- Define routing rules in the API gateway for each service
- Implement rate limiting and authentication at the gateway level

**Gateway Routes:**
- `/api/orders/**` → Order Service
- `/api/consumers/**` → Consumer Service
- `/api/restaurants/**` → Restaurant Service
- `/api/couriers/**` → Courier Service

### Phase 6: Observability

Implement comprehensive observability for monitoring, tracing, and debugging the distributed system.

**Objectives:**
- Implement distributed tracing across all services
- Set up centralized logging
- Extend existing Prometheus metrics for microservices monitoring
- Optionally configure a service mesh for advanced traffic management

**Technical Approach:**
- Deploy Zipkin or Jaeger for distributed tracing
- Configure Spring Cloud Sleuth for automatic trace propagation
- Deploy the ELK stack (Elasticsearch, Logstash, Kibana) for centralized logging
- Configure structured JSON logging in each service
- Extend Prometheus metrics with service-specific custom metrics
- Create Grafana dashboards for monitoring
- Optionally deploy Istio service mesh for traffic management, mTLS, and advanced observability

**Observability Components:**
- Distributed Tracing: Zipkin/Jaeger with Spring Cloud Sleuth
- Centralized Logging: ELK Stack (Elasticsearch, Logstash, Kibana)
- Metrics: Prometheus + Grafana (building on existing Actuator endpoints)
- Service Mesh (optional): Istio for traffic management and security

## Technical Requirements

### Technology Stack

The migration will leverage the following technologies:

**Core Framework:** Spring Boot 2.x (existing), with potential upgrade path to Spring Boot 3.x

**Inter-Service Communication:** REST APIs with Spring Web, Feign Clients for declarative HTTP clients

**Distributed Transactions:** Saga pattern implementation using Eventuate Tram or custom orchestration

**Service Discovery:** Netflix Eureka or HashiCorp Consul

**API Gateway:** Spring Cloud Gateway or Kong

**Resilience:** Resilience4j for circuit breakers, retries, and rate limiting

**Messaging:** Apache Kafka (already configured via Eventuate Local)

**Database:** MySQL (separate instance per service)

**Containerization:** Docker with multi-stage builds

**Orchestration:** Kubernetes (existing deployment manifests in `deployment/kubernetes/`)

**Observability:** Prometheus (existing), Zipkin (existing configuration), ELK Stack, Grafana

### Non-Functional Requirements

**Performance:** Service-to-service latency should not exceed 100ms for synchronous calls. The system should handle at least 1000 orders per minute.

**Availability:** Each service should maintain 99.9% availability. The system should gracefully degrade when individual services are unavailable.

**Scalability:** Each service should be independently scalable based on its specific load characteristics.

**Security:** All inter-service communication should be encrypted (TLS). API gateway should handle authentication and authorization.

**Data Consistency:** Eventual consistency is acceptable for cross-service data. Saga pattern ensures business transaction consistency.

## Success Criteria

The migration will be considered successful when the following criteria are met:

**Phase 1 Complete:** Each service has its own database with no cross-service repository dependencies. Data integrity is maintained after migration.

**Phase 2 Complete:** All inter-service communication uses REST APIs. No direct method calls or repository access across service boundaries. Circuit breakers prevent cascade failures.

**Phase 3 Complete:** Order creation works correctly using the Saga pattern. Compensating transactions successfully roll back failed operations. System handles partial failures gracefully.

**Phase 4 Complete:** Each service can be deployed independently without affecting other services. Services can be scaled independently based on load.

**Phase 5 Complete:** Services discover each other dynamically through the service registry. API gateway successfully routes all external requests. Load balancing distributes traffic across service instances.

**Phase 6 Complete:** Distributed traces are visible across all service calls. Logs are aggregated and searchable in a central location. Dashboards provide real-time visibility into system health.

**Overall Success:** All existing end-to-end tests pass against the microservices architecture. System performance meets or exceeds the monolith baseline. Development teams can deploy services independently without coordination.

## Risks and Mitigations

**Data Migration Risk:** Moving data to separate databases could cause data loss or inconsistency. Mitigation: Implement comprehensive data validation scripts and run migration in stages with rollback capability.

**Distributed Transaction Complexity:** Saga pattern adds complexity compared to simple database transactions. Mitigation: Start with well-documented saga implementations and comprehensive testing of failure scenarios.

**Increased Latency:** Network calls between services add latency compared to in-process calls. Mitigation: Implement caching strategies, optimize API payloads, and use asynchronous communication where appropriate.

**Operational Complexity:** Managing multiple services is more complex than a single monolith. Mitigation: Invest in observability tooling and automation from the start.

**Team Learning Curve:** Teams need to learn new patterns and technologies. Mitigation: Provide training and start with less critical services to build experience.

## Timeline Estimate

Phase 1 (Database Separation): 4-6 weeks
Phase 2 (API Communication): 3-4 weeks
Phase 3 (Distributed Transactions): 4-6 weeks
Phase 4 (Independent Deployments): 2-3 weeks
Phase 5 (Service Discovery & Gateway): 2-3 weeks
Phase 6 (Observability): 2-3 weeks

Total estimated duration: 17-25 weeks

Note: Phases can overlap where dependencies allow. The timeline assumes a dedicated team and may vary based on team size and experience.
