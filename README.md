# AI Market Research Microservice

## Architecture Overview

### Core Components

1. **API Layer** (FastAPI)
   - Single `/research` endpoint for market analysis
   - Structured request/response with Pydantic validation
   - Graceful error handling with resilience patterns

2. **AI Agent System**
   - Tool-based agent architecture using LangChain
   - Extensible tool interface for market data retrieval
   - Structured output validation with retry logic

3. **Polyglot Persistence**
   - **PostgreSQL**: Transactional data (requests + final reports)
   - **MongoDB**: AI execution logs and debugging metadata
   - Resilient design: MongoDB failures don't block API responses

### Key Design Decisions

1. **Separation of Concerns**
   - `api/`: FastAPI routes and models
   - `agent/`: AI agent logic and tools
   - `db/`: Database clients and repositories
   - `core/`: Configuration and shared utilities

2. **Resilience Pattern**
   - MongoDB logging is non-blocking (fire-and-forget)
   - Failed logs are caught and logged but don't fail requests
   - PostgreSQL persistence is the source of truth

3. **Structured Output**
   - Pydantic models enforce schema validation
   - LLM responses use structured output (JSON mode)
   - Validation failures trigger retries with corrective prompts

4. **Tool System**
   - Abstract base class for extensibility
   - Mock implementations for demo purposes
   - Easy to swap with real API integrations

## Setup Instructions

Create a `.env` file in the project root by copying .env.example 

Running the Service:

```bash
docker-compose up --build

# The API will be available at:
# http://localhost:8000

```

Example Request

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"asset": "BTC"}'
```

Example Response:
```json
{
  "asset": "BTC",
  "risk_level": "High",
  "sentiment_score": 0.72,
  "tools_used": ["get_market_price", "get_internal_sentiment"]
}
```

## Design Question: Handling Long-Running Jobs

The synchronous design blocks API responses during:
- LLM API calls (can take 5-30 seconds)
- Multiple tool invocations
- Database writes

This creates poor user experience and limits throughput under high load.

### Proposed Asynchronous Architecture

Job Queue Pattern

**Components:**
- **Message Queue**: Redis or RabbitMQ for job distribution
- **Worker Pool**: Multiple worker processes for parallel execution
- **Job Status Store**: Redis for fast status lookups

**Flow:**
```
Client → POST /research → Job ID (202 Accepted)
                ↓
          Queue Job → Worker picks up
                ↓
          Process → Store results
                ↓
Client → GET /research/{job_id} → Result (200 OK)
```

**Benefits:**
- Immediate API response
- Horizontal scaling of workers
- Rate limiting and prioritization
- Retry and failure handling


Enhanced Architecture Components

**Worker Service:**
- Separate container(s) from API service
- Processes jobs from queue
- Scales independently based on queue depth
- Implements circuit breakers for external APIs

**Caching Layer:**
- Redis cache for recent results
- TTL-based invalidation (e.g., 5 minutes for market data)
- Reduces redundant LLM calls for same asset

**Rate Limiting:**
- Token bucket per client/API key
- Queue backpressure mechanisms
- Graceful degradation under load

