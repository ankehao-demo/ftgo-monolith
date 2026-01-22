# FTGO Migration User Stories

This document contains user stories with acceptance criteria for each major phase of the FTGO monolith to microservices migration.

## Story 1: Database Separation

**As a** system architect,
**I want** each service to have its own database
**So that** services are independently deployable and can evolve their schemas without affecting other services.

### Description

The current FTGO application uses a single shared MySQL database (`ftgo`) where all services access tables directly through the `ftgo-domain` module. This creates tight coupling between services and prevents independent deployment. This story covers extracting each service's data into its own dedicated database.

### Acceptance Criteria

**AC 1.1: Separate Database Schemas**
- Order Service has its own database (`ftgo_orders`) containing the `orders` and `order_line_items` tables
- Consumer Service has its own database (`ftgo_consumers`) containing the `consumers` table
- Restaurant Service has its own database (`ftgo_restaurants`) containing the `restaurants` and `restaurant_menu_items` tables
- Courier Service has its own database (`ftgo_couriers`) containing the `courier` and `courier_actions` tables

**AC 1.2: No Cross-Service Repository Dependencies**
- The `ftgo-domain` module no longer contains shared repository interfaces
- `OrderRepository` is moved to `ftgo-order-service` and only accesses the Order database
- `ConsumerRepository` is moved to `ftgo-consumer-service` and only accesses the Consumer database
- `RestaurantRepository` is moved to `ftgo-restaurant-service` and only accesses the Restaurant database
- `CourierRepository` is moved to `ftgo-courier-service` and only accesses the Courier database

**AC 1.3: Service Database Isolation**
- Each service's datasource configuration points only to its own database
- No service can directly query another service's database tables
- Foreign key constraints between services are removed (referential integrity is handled at the application level)

**AC 1.4: Data Migration**
- Existing data is migrated to the appropriate service databases without data loss
- Data integrity is verified after migration through automated validation scripts
- Flyway migrations are created for each service's database schema

### Technical Notes

The `Order` entity currently has a `consumerId` field that references the Consumer table and a `restaurantId` that references the Restaurant table. After database separation, these will remain as foreign key values but without database-level foreign key constraints. The Order Service will validate these references through API calls to the respective services.

---

## Story 2: API Communication

**As a** developer,
**I want** services to communicate via REST APIs
**So that** they are loosely coupled and can be deployed, scaled, and updated independently.

### Description

The current implementation has the Order Service making direct method calls to `ConsumerService.validateOrderForConsumer()` and directly accessing `RestaurantRepository` and `CourierRepository`. This story covers replacing these direct dependencies with REST API calls using the existing API modules.

### Acceptance Criteria

**AC 2.1: Consumer Service API Integration**
- Order Service calls Consumer Service via REST API instead of direct method invocation
- Consumer Service exposes a `POST /consumers/{consumerId}/validate` endpoint that accepts order total and returns validation result
- Order Service uses a Feign client or RestTemplate to call the Consumer Service API
- The API contract is defined in `ftgo-consumer-service-api` module

**AC 2.2: Restaurant Service API Integration**
- Order Service calls Restaurant Service via REST API instead of direct repository access
- Restaurant Service exposes a `GET /restaurants/{restaurantId}` endpoint that returns restaurant details including menu items
- Order Service uses a Feign client or RestTemplate to call the Restaurant Service API
- The API contract is defined in `ftgo-restaurant-service-api` module

**AC 2.3: Courier Service API Integration**
- Order Service calls Courier Service via REST API instead of direct repository access
- Courier Service exposes a `GET /couriers/available` endpoint that returns available couriers
- Courier Service exposes a `POST /couriers/{courierId}/actions` endpoint to assign pickup and dropoff actions
- Order Service uses a Feign client or RestTemplate to call the Courier Service API
- The API contract is defined in `ftgo-courier-service-api` module

**AC 2.4: Fault Tolerance**
- Circuit breakers (Resilience4j) are implemented for all inter-service API calls
- Appropriate timeouts are configured for API calls (default: 5 seconds)
- Fallback responses are defined for when downstream services are unavailable
- Retry logic is implemented with exponential backoff for transient failures

**AC 2.5: API Contract Compliance**
- All inter-service communication uses DTOs defined in the respective `-api` modules
- No service implementation classes are exposed across service boundaries
- API versioning strategy is defined (e.g., URL path versioning: `/api/v1/...`)

### Technical Notes

The existing API modules (`ftgo-consumer-service-api`, `ftgo-restaurant-service-api`, `ftgo-courier-service-api`) already define request/response DTOs. These should be leveraged for the REST API contracts. The Order Service will need to add dependencies on these API modules and implement HTTP clients.

---

## Story 3: Distributed Transactions (Saga Pattern)

**As a** system architect,
**I want** to implement the Saga pattern for distributed transactions
**So that** multi-service operations can be coordinated reliably with proper rollback handling.

### Description

The current `OrderService.createOrder()` method is a single `@Transactional` operation that validates the consumer, fetches restaurant data, creates the order, and would eventually assign a courier. In a microservices architecture with separate databases, this single transaction cannot span multiple services. This story implements the Saga pattern to coordinate the order creation process across services.

### Acceptance Criteria

**AC 3.1: Create Order Saga Definition**
- The order creation process is implemented as a saga with the following steps:
  1. Create Order in PENDING state (Order Service)
  2. Validate Consumer (Consumer Service)
  3. Validate Restaurant and retrieve menu items (Restaurant Service)
  4. Approve Order and update state to APPROVED (Order Service)
  5. Schedule Delivery and assign courier (Courier Service)
  6. Confirm Order completion (Order Service)

**AC 3.2: Compensating Transactions**
- If consumer validation fails: Order is rejected and marked as REJECTED with reason "Consumer validation failed"
- If restaurant validation fails: Order is rejected and marked as REJECTED with reason "Restaurant not found or invalid menu items"
- If courier assignment fails: Order is rejected and marked as REJECTED with reason "No couriers available"
- Each compensating transaction properly cleans up any state created in previous steps

**AC 3.3: Saga Orchestration**
- A saga orchestrator component coordinates the saga execution
- The orchestrator tracks saga state and handles step transitions
- Saga state is persisted to enable recovery from failures
- The orchestrator handles both successful completion and rollback scenarios

**AC 3.4: Replace @Transactional Operation**
- The single `@Transactional` annotation on `OrderService.createOrder()` is removed
- Each saga step has its own local transaction within its respective service
- The saga ensures eventual consistency across all services
- The `createOrder()` method returns immediately with the order in PENDING state

**AC 3.5: Idempotency**
- Each saga step is idempotent to handle retries safely
- Duplicate saga step executions do not create duplicate data
- Saga step identifiers are used to track and deduplicate operations

### Technical Notes

Consider using Eventuate Tram Sagas framework which is already partially configured in the codebase (Eventuate Local). Alternatively, implement a custom orchestration-based saga using Kafka for event communication. The saga should be designed to handle network partitions and service failures gracefully.

---

## Story 4: Independent Deployments

**As a** DevOps engineer,
**I want** each service to be independently deployable
**So that** we can scale, update, and maintain services separately without affecting the entire system.

### Description

Currently, all services are aggregated into a single Spring Boot application (`FtgoApplicationMain`) that imports all service configurations. This story extracts each service into its own standalone Spring Boot application with independent deployment artifacts.

### Acceptance Criteria

**AC 4.1: Separate Spring Boot Applications**
- Order Service has its own `OrderServiceApplication` main class with `@SpringBootApplication`
- Consumer Service has its own `ConsumerServiceApplication` main class with `@SpringBootApplication`
- Restaurant Service has its own `RestaurantServiceApplication` main class with `@SpringBootApplication`
- Courier Service has its own `CourierServiceApplication` main class with `@SpringBootApplication`
- The aggregated `FtgoApplicationMain` is deprecated or removed

**AC 4.2: Independent Configuration**
- Each service has its own `application.properties` or `application.yml` file
- Database connection strings point to service-specific databases
- Server ports are configured independently (Order: 8081, Consumer: 8082, Restaurant: 8083, Courier: 8084)
- Each service has its own logging configuration

**AC 4.3: Separate Database Connections**
- Each service's datasource is configured to connect only to its own database
- Connection pool settings are tuned per service based on expected load
- Database credentials are externalized using environment variables or secrets management

**AC 4.4: Containerization**
- Each service has its own Dockerfile
- Docker images are built independently for each service
- Images follow naming convention: `ftgo-{service-name}:version`
- Multi-stage builds are used to minimize image size

**AC 4.5: Kubernetes Deployments**
- Each service has its own Kubernetes Deployment manifest
- Each service has its own Kubernetes Service manifest for internal communication
- ConfigMaps are created for service-specific configuration
- Secrets are used for sensitive configuration (database passwords, API keys)
- Health checks (liveness and readiness probes) are configured for each service

**AC 4.6: Independent Scaling**
- Each service can be scaled independently using `kubectl scale` or HPA
- Resource requests and limits are defined per service based on profiling
- Services do not share pods or containers

### Technical Notes

The existing `deployment/kubernetes/` directory contains Kubernetes manifests that should be updated or replaced. Each service should be deployable to Kubernetes without requiring other services to be deployed simultaneously (though they may need to be running for full functionality).

---

## Story 5: Service Discovery and API Gateway

**As a** system architect,
**I want** service discovery and an API gateway
**So that** services can find each other dynamically and external clients have a unified entry point.

### Description

In a microservices architecture, services need to discover each other dynamically as instances scale up and down. An API gateway provides a single entry point for external clients, handling routing, load balancing, and cross-cutting concerns like authentication.

### Acceptance Criteria

**AC 5.1: Service Registry Implementation**
- A service registry is deployed (Netflix Eureka or HashiCorp Consul)
- The registry is highly available with multiple instances
- The registry UI is accessible for monitoring registered services
- Health check intervals are configured appropriately (default: 30 seconds)

**AC 5.2: Service Registration**
- Order Service registers itself with the service registry on startup
- Consumer Service registers itself with the service registry on startup
- Restaurant Service registers itself with the service registry on startup
- Courier Service registers itself with the service registry on startup
- Services deregister gracefully on shutdown
- Service metadata (version, environment) is included in registration

**AC 5.3: Service Discovery**
- Services discover other services through the registry instead of hardcoded URLs
- Client-side load balancing is implemented using Spring Cloud LoadBalancer
- Service discovery is integrated with Feign clients for automatic resolution
- Fallback to cached service locations is available if registry is temporarily unavailable

**AC 5.4: API Gateway Deployment**
- Spring Cloud Gateway or Kong is deployed as the API gateway
- The gateway is the single entry point for all external API requests
- The gateway is deployed with multiple replicas for high availability

**AC 5.5: Gateway Routing**
- Routes are configured for each service:
  - `/api/orders/**` routes to Order Service
  - `/api/consumers/**` routes to Consumer Service
  - `/api/restaurants/**` routes to Restaurant Service
  - `/api/couriers/**` routes to Courier Service
- Path rewriting is configured as needed
- Route predicates handle versioned APIs (e.g., `/api/v1/orders/**`)

**AC 5.6: Load Balancing**
- The gateway load balances requests across service instances
- Load balancing algorithm is configurable (round-robin by default)
- Unhealthy instances are automatically removed from the load balancer pool
- Sticky sessions can be enabled for stateful operations if needed

**AC 5.7: Cross-Cutting Concerns**
- Rate limiting is configured at the gateway level
- Request/response logging is enabled for debugging
- CORS is configured for browser-based clients
- Request timeout policies are defined

### Technical Notes

If using Eureka, deploy it as a StatefulSet in Kubernetes for stable network identities. The API gateway should be exposed via a Kubernetes Ingress or LoadBalancer service. Consider using Spring Cloud Gateway for consistency with the Spring ecosystem.

---

## Story 6: Observability

**As an** operations engineer,
**I want** comprehensive observability
**So that** I can monitor, troubleshoot, and understand the behavior of the distributed system.

### Description

A microservices architecture introduces complexity in understanding system behavior. This story implements distributed tracing, centralized logging, and enhanced metrics to provide visibility into the system. The existing Prometheus metrics and Actuator endpoints serve as a foundation.

### Acceptance Criteria

**AC 6.1: Distributed Tracing Implementation**
- Zipkin or Jaeger is deployed for distributed trace collection and visualization
- Spring Cloud Sleuth is configured in all services for automatic trace propagation
- Trace IDs are propagated across all inter-service HTTP calls
- Trace IDs are included in log messages for correlation
- The tracing UI is accessible for viewing traces and analyzing latency

**AC 6.2: Trace Sampling and Retention**
- Sampling rate is configurable (default: 10% for production, 100% for development)
- Traces are retained for at least 7 days
- High-latency and error traces are always sampled (adaptive sampling)

**AC 6.3: Centralized Logging**
- ELK Stack (Elasticsearch, Logstash, Kibana) is deployed for log aggregation
- All services send logs to the centralized logging system
- Logs are structured in JSON format for easy parsing
- Log levels are configurable per service without redeployment

**AC 6.4: Log Correlation**
- Trace IDs and span IDs are included in all log entries
- Request IDs are propagated and logged for end-to-end request tracking
- Logs can be filtered by trace ID in Kibana to see all logs for a single request

**AC 6.5: Prometheus Metrics Extension**
- Existing Prometheus metrics from Actuator are preserved
- Custom business metrics are added:
  - `orders_created_total` - Counter for orders created
  - `orders_by_state` - Gauge for orders in each state
  - `order_processing_duration_seconds` - Histogram for order processing time
  - `service_call_duration_seconds` - Histogram for inter-service call latency
- Metrics are labeled with service name, version, and environment

**AC 6.6: Grafana Dashboards**
- Grafana is deployed and connected to Prometheus
- A system overview dashboard shows health of all services
- Per-service dashboards show detailed metrics
- Alert rules are configured for critical metrics (error rate, latency, availability)

**AC 6.7: Service Mesh (Optional)**
- Istio service mesh is optionally deployed for advanced traffic management
- mTLS is enabled for secure inter-service communication
- Traffic policies (retries, timeouts, circuit breakers) are configured in Istio
- Istio telemetry integrates with existing observability stack

**AC 6.8: Health Endpoints**
- All services expose `/actuator/health` endpoint with detailed health information
- Health checks include database connectivity, downstream service availability
- Kubernetes probes use health endpoints for liveness and readiness checks
- Health status is aggregated in monitoring dashboards

### Technical Notes

The existing `application.properties` already has some Zipkin configuration. Extend this to ensure all services participate in distributed tracing. For the ELK stack, consider using Filebeat as a lightweight log shipper. Istio deployment is optional and should be evaluated based on operational complexity tolerance.

---

## Definition of Done

For each story to be considered complete:

1. All acceptance criteria are met and verified
2. Code changes are reviewed and merged
3. Unit tests cover new functionality with at least 80% coverage
4. Integration tests verify inter-service communication
5. Documentation is updated (README, API docs, architecture diagrams)
6. Deployment manifests are updated and tested
7. Monitoring and alerting are configured for new components
8. Performance testing confirms no regression from baseline
9. Security review is completed for any new endpoints or data flows
10. Runbook is updated with operational procedures

## Story Dependencies

The stories should be implemented in the following order due to dependencies:

1. **Story 1: Database Separation** - Foundation for all other stories
2. **Story 2: API Communication** - Requires database separation to be meaningful
3. **Story 3: Distributed Transactions** - Requires API communication to be in place
4. **Story 4: Independent Deployments** - Can start in parallel with Story 3
5. **Story 5: Service Discovery & API Gateway** - Requires independent deployments
6. **Story 6: Observability** - Can be implemented incrementally throughout all phases

Note: Some aspects of Story 6 (basic logging and metrics) should be implemented early to aid in debugging during the migration process.
