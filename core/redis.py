import redis.asyncio as aioredis

from fastapi import HTTPException, status

from core.config import settings



# ------------------- Main redis client ------------------- #
# Creating Redis client
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)


# ------------- Rate Limiting Tool ------------ #
# Reusable class for rate limiting
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check_rate_limit(self, client_ip: int | str):

        # Creating a unique key for this specific user in Redis
        key = f"rate_limit:user:{client_ip}"

        # If the key doesn't exist yet, Redis automatically creates it at 1
        current_request = await redis_client.incr(key)

        if current_request == 1:
            # Uses the custom seconds we passed in
            await redis_client.expire(key, self.window_seconds)

        # If the counter goes past our limit (max_requests), block the request
        if current_request > self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many applications. Please wait a minute."
            )

rate_limiter = RateLimiter(max_requests=settings.RATE_LIMIT_PER_MINUTE, window_seconds=60)