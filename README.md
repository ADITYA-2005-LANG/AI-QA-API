# AI Q&A API

A production-oriented AI Question-Answering API built with **FastAPI, Google Gemini, PostgreSQL, Redis, JWT authentication, and Docker**.

The project demonstrates LLM integration, authentication, RBAC, caching, distributed rate limiting, monitoring, retries, error handling, containerization, and a scalable production architecture.

## 1. Features

- FastAPI REST API
- Google Gemini LLM integration
- JWT-based authentication
- Role-Based Access Control (RBAC)
- PostgreSQL for persistent user data
- Redis for:
  - Response caching
  - Distributed rate limiting
  - Metrics storage
- LLM timeout and retry handling
- Request latency tracking
- LLM token usage tracking
- Docker and Docker Compose
- Automated tests with Pytest

## 2. Current Architecture

```text
                    Client
                      |
                      v
                +-----------+
                |  FastAPI  |
                +-----+-----+
                      |
             +--------+--------+
             |                 |
             v                 v
         PostgreSQL          Redis
         User data       Cache / Rate Limit
             |                 |
             |                 v
             |             Gemini API
             |
             +----------------------+
```

The current implementation runs FastAPI, PostgreSQL, and Redis using Docker Compose.

## 3. Proposed Production Architecture

```text
Users
  |
  v
Load Balancer
  |
  +-------------------+-------------------+
  |                   |                   |
  v                   v                   v
FastAPI-1          FastAPI-2          FastAPI-N
  |                   |                   |
  +-------------------+-------------------+
                      |
              +-------+-------+
              |               |
              v               v
            Redis        PostgreSQL
       Cache / Rate       Persistent
          Limit             Data
              |
              v
        LLM Gateway
              |
              v
          LLM APIs
```

The load balancer, multiple FastAPI instances, LLM gateway, and background queue represent the proposed production scaling architecture.

## 4. Technology Stack

| Component | Technology |
|---|---|
| API | Python + FastAPI |
| LLM | Google Gemini |
| Authentication | JWT |
| Database | PostgreSQL |
| Cache | Redis |
| Rate Limiting | Redis |
| Containerization | Docker |
| Local Orchestration | Docker Compose |
| Testing | Pytest |

## 5. API Endpoints

### POST /auth/login

Authenticates a user and returns a JWT.

Example:

```json
{
  "username": "user",
  "password": "user123"
}
```

### POST /chat

Requires a valid JWT.

Example:

```json
{
  "question": "What is Docker?"
}
```

Example response:

```json
{
  "question": "What is Docker?",
  "answer": "Docker is a platform for developing..."
}
```

### GET /health

Returns the API health status.

```json
{
  "status": "healthy"
}
```

### GET /metrics

Returns application metrics stored in Redis.

Example:

```json
{
  "total_requests": 1,
  "total_tokens": 677,
  "average_latency_seconds": 3.529
}
```

### GET /admin

Administrative endpoint protected by the `Admin` role.

## 6. Authentication and RBAC

The application uses JWT authentication.

Supported roles:

### Admin

- Administrative access
- Intended for user/configuration management
- Access to administrative metrics

### User

- Access to the chat API

### Read-only

- Intended for permitted reports/data access

JWT tokens contain the username, role, and expiration time.

### Production SSO/OIDC Architecture

The local JWT login can be extended to a production SSO architecture:

```text
Application
     |
     v
SSO / OAuth2 / OIDC
     |
     v
Identity Provider
     |
     v
JWT
     |
     v
API Gateway
     |
     v
AI Service
```

## 7. Redis Caching

Responses are cached using Redis.

The cache key is generated from the normalized question:

```text
chat:<question>
```

Cached responses expire after **5 minutes**.

Repeated questions can therefore be served from Redis without making another LLM request, reducing latency and LLM usage.

## 8. Redis Rate Limiting

The `/chat` endpoint implements per-user distributed rate limiting.

Current limit:

```text
10 requests per authenticated user per 60 seconds
```

The Redis key is:

```text
rate_limit:<username>
```

When the limit is exceeded, the API returns:

```http
429 Too Many Requests
```

Example:

```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

Because the counter is stored in Redis, the limit can be shared across multiple FastAPI instances.

## 9. LLM Integration and Error Handling

The application uses Google Gemini to generate answers.

LLM requests include:

- Request timeout
- Up to 3 attempts
- Exponential backoff

The retry delays are:

```text
Attempt 1 -> immediate
Attempt 2 -> 2 seconds
Attempt 3 -> 4 seconds
```

If all attempts fail, the API returns:

```http
503 Service Unavailable
```

This provides basic recovery from temporary LLM failures.

## 10. Monitoring and Metrics

The application records:

- Total requests
- Total LLM token usage
- Total LLM latency
- Average latency

Metrics are stored in Redis.

A production deployment could extend this with Prometheus and Grafana:

```text
FastAPI
   |
   v
Prometheus
   |
   v
Grafana
```

Additional production metrics could include:

- Request rate
- HTTP error rate
- P50/P95/P99 latency
- Cache hit rate
- LLM failure rate
- LLM token usage
- Rate-limit violations
- Active requests

## 11. Docker Setup

The application uses Docker Compose with:

```text
api
db
redis
```

Build and start:

```bash
docker-compose up -d --build
```

Check services:

```bash
docker-compose ps
```

Stop services:

```bash
docker-compose down
```

The API is available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

## 12. Environment Configuration

Configuration is provided through environment variables.

Example:

```env
GEMINI_API_KEY=<your-api-key>
DATABASE_URL=<database-url>
JWT_SECRET_KEY=<your-secret>
REDIS_URL=redis://redis:6379
```

Secrets should not be committed to Git.

For production, secrets should be stored using a cloud secret manager or Kubernetes Secrets.

## 13. Testing

The project contains tests for:

- Health endpoint
- Successful login
- Invalid login
- JWT validation
- RBAC
- Chat authentication
- Chat functionality

Run tests inside the API container:

```bash
docker exec -it ai-qa-api pytest
```

The current test suite contains 9 tests.

## 14. Scaling to 100–500 RPS

The assessment scenario assumes 100 requests/second with occasional spikes to 500 requests/second.

### Horizontal Scaling

Run multiple FastAPI instances behind a load balancer.

```text
Load Balancer
      |
  +---+---+---+
  |   |   |   |
 API API API API
```

### Load Balancing

The load balancer distributes traffic and performs health checks.

### Kubernetes HPA

In Kubernetes, Horizontal Pod Autoscaler can increase or decrease FastAPI replicas based on resource or custom metrics.

### Redis

Redis can provide:

- Shared response caching
- Distributed rate limiting
- Short-lived shared state

### Background Queues

Long-running or asynchronous workloads can be moved to a queue:

```text
FastAPI -> Queue -> Worker -> LLM
```

This prevents API workers from being tied up by long-running work.

### LLM Limits

LLM providers may impose:

- RPM — Requests Per Minute
- TPM — Tokens Per Minute
- Concurrency limits

An LLM gateway can centrally enforce these limits.

### Concurrent Requests

The application can scale FastAPI horizontally, while an LLM gateway or worker layer controls the number of simultaneous LLM calls.

### Failure Recovery

Production recovery can include:

- Timeouts
- Exponential-backoff retries
- Circuit breakers
- LLM provider fallback
- Graceful degradation
- Queue-based processing for asynchronous workloads

The assessment does not require implementing a complete 500-RPS environment.

## 15. Migration from Single EC2 to 10,000 Users

The initial application can run on a single EC2 server. For approximately 10,000 users, the proposed architecture is:

```text
Users
  |
  v
Load Balancer
  |
  v
Kubernetes / ECS
  |
  v
Multiple FastAPI Instances
  |
  +--------+---------+
  |                  |
  v                  v
Redis / Queue     PostgreSQL
  |
  v
LLM Gateway
  |
  v
LLM APIs
```

### Scaling

- Deploy multiple FastAPI replicas.
- Use a load balancer for traffic distribution.
- Use Kubernetes HPA or equivalent autoscaling.
- Move PostgreSQL to a managed/high-availability deployment when required.

### LLM API Limits

Use a centralized LLM gateway to control:

- RPM
- TPM
- Concurrent requests
- Retry policies
- Provider selection

This prevents independently scaled API instances from overwhelming the LLM provider.

### Slow or Failing LLM Requests

Use:

```text
Timeout
   |
   v
Retry with Backoff
   |
   v
Circuit Breaker
   |
   +----> Fallback Provider
   |
   +----> Graceful Error
```

### Redis and Queues

Redis can handle:

- Response caching
- Distributed rate limiting
- Short-lived state

A queue can handle long-running asynchronous workloads.

### Monitoring

Monitor:

- API latency
- HTTP error rate
- LLM latency
- LLM failures
- Token usage
- Cache hit rate
- Rate-limit violations
- CPU and memory
- Queue depth

### Minimal-Downtime Migration

A gradual migration can be performed:

```text
Existing EC2
     |
     v
Containerize application
     |
     v
Deploy new environment
     |
     v
Run health checks
     |
     v
Send a small percentage of traffic
     |
     v
Verify metrics
     |
     v
Gradually shift traffic
     |
     v
Retire old EC2
```

This allows the existing system to remain available while the new deployment is validated.

### Secrets and Configuration

Use environment-based configuration during development.

For production, use:

- Kubernetes Secrets
- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Another managed secret-management solution

Secrets must not be hard-coded into application source code.

## 16. Project Structure

```text
ai-qa-api/
├── app/
│   ├── api/
│   │   └── auth.py
│   ├── schemas/
│   │   ├── auth.py
│   │   └── chat.py
│   ├── services/
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── llm.py
│   │   └── redis.py
│   └── main.py
│
├── tests/
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_rbac.py
│   └── test_chat.py
│
├── create_user.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── .gitignore
```

## 17. Future Production Improvements

The assessment implementation can be extended with:

- Kubernetes deployment
- API Gateway
- Managed PostgreSQL
- Redis Cluster
- Prometheus and Grafana
- Centralized logging
- OpenTelemetry tracing
- Database connection pooling
- Alembic migrations
- LLM gateway
- Circuit breaker
- Multiple LLM provider fallback
- Kubernetes/cloud secrets
- TLS termination
- CI/CD

## 18. Assessment Coverage

| Requirement | Status |
|---|---|
| FastAPI application | Implemented |
| JWT authentication | Implemented |
| `/chat` + LLM | Implemented |
| Redis integration | Implemented |
| PostgreSQL integration | Implemented |
| Docker | Implemented |
| Error handling and retries | Implemented |
| Latency/token metrics | Implemented |
| Redis caching | Implemented |
| Distributed rate limiting | Implemented |
| RBAC | Implemented |
| Basic tests | Implemented |
| README | Implemented |
| Architecture/scaling design | Documented |
| Migration strategy | Documented |
| Architecture diagram | To add as a separate diagram/image |

## 19. Local Verification

Health:

```bash
curl http://localhost:8000/health
```

Login:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"user123"}'
```

Metrics:

```bash
curl http://localhost:8000/metrics
```

Run tests:

```bash
docker exec -it ai-qa-api pytest
```

Rate-limit verification:

```text
Requests 1–10 -> 200
Request 11    -> 429
```
