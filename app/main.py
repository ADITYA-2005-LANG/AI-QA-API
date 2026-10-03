
from fastapi import FastAPI, Depends, HTTPException, status
import time

from app.services.llm import ask_llm
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.auth import router as auth_router
from app.services.database import create_users_table
from app.services.redis import redis_client
from app.services.auth import get_current_user, require_role


app = FastAPI(title="AI Q&A API")

create_users_table()

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "AI Q&A API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):
    username = current_user["username"]

    # -------------------------
    # Rate limiting
    # -------------------------
    rate_limit_key = f"rate_limit:{username}"

    request_count = redis_client.incr(rate_limit_key)

    if request_count == 1:
        redis_client.expire(rate_limit_key, 60)

    if request_count > 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )

    # -------------------------
    # Redis cache
    # -------------------------
    cache_key = f"chat:{request.question.strip().lower()}"

    cached_answer = redis_client.get(cache_key)

    if cached_answer:
        redis_client.incr("metrics:total_requests")
        redis_client.incr("metrics:cache_hits")

        return {
            "question": request.question,
            "answer": cached_answer
        }

    # -------------------------
    # LLM request
    # -------------------------
    start_time = time.perf_counter()

    result = ask_llm(request.question)

    # Cache the answer for 5 minutes
    redis_client.setex(
        cache_key,
        300,
        result["answer"]
    )

    latency = time.perf_counter() - start_time

    # -------------------------
    # Metrics
    # -------------------------
    redis_client.incr("metrics:total_requests")
    redis_client.incr("metrics:llm_requests")

    redis_client.incrby(
        "metrics:total_tokens",
        result["total_tokens"]
    )

    redis_client.incrbyfloat(
        "metrics:total_latency",
        latency
    )

    print(f"LLM latency: {latency:.3f} seconds")
    print(f"Token usage: {result['total_tokens']}")

    return {
        "question": request.question,
        "answer": result["answer"]
    }


@app.get("/metrics")
def metrics():
    total_requests = int(
        redis_client.get("metrics:total_requests") or 0
    )

    cache_hits = int(
        redis_client.get("metrics:cache_hits") or 0
    )

    llm_requests = int(
        redis_client.get("metrics:llm_requests") or 0
    )

    total_tokens = int(
        redis_client.get("metrics:total_tokens") or 0
    )

    total_latency = float(
        redis_client.get("metrics:total_latency") or 0
    )

    average_llm_latency = (
        total_latency / llm_requests
        if llm_requests > 0
        else 0
    )

    return {
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "llm_requests": llm_requests,
        "total_tokens": total_tokens,
        "average_llm_latency_seconds": round(
            average_llm_latency,
            3
        )
    }


@app.get("/admin")
def admin_only(
    current_user=Depends(require_role("Admin"))
):
    return {
        "message": "Welcome Admin",
        "user": current_user["username"],
        "role": current_user["role"]
    }

