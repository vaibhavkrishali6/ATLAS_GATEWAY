from dataclasses import dataclass
from time import time

import redis


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: int


class TokenBucketLimiter:
    def __init__(
            self,
            redis_client: redis.Redis,
            capacity: int = 100,
            refill_rate: float = 100 / 30,) -> None:
        
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate

    def allow(self, user_id: str) -> RateLimitResult:
        key = f"atlas:rate_limit:token_bucket:{user_id}"

        now = time()

        result = self.redis.eval(
            """
            local key = KEYS[1]

            local now = tonumber(ARGV[1])
            local capacity = tonumber(ARGV[2])
            local refill_rate = tonumber(ARGV[3])

            local bucket = redis.call("HMGET", key, "tokens", "timestamp")

            local tokens = tonumber(bucket[1])
            local timestamp = tonumber(bucket[2])

            if tokens == nil then
                tokens = capacity
            end

            if timestamp == nil then
                timestamp = now
            end

            local elapsed = math.max(0, now - timestamp)

            tokens = math.min(
                capacity,
                tokens + (elapsed * refill_rate)
            )

            local allowed = 0
            local retry_after = 0

            if tokens >= 1 then
                tokens = tokens - 1
                allowed = 1
            else
                retry_after = math.ceil((1 - tokens) / refill_rate)
            end

            redis.call(
                "HSET",
                key,
                "tokens",
                tokens,
                "timestamp",
                now
            )

            redis.call(
                "EXPIRE",
                key,
                120
            )

            return {
                allowed,
                math.floor(tokens),
                retry_after
            }
            """,
            1,
            key,
            now,
            self.capacity,
            self.refill_rate,
        )

        return RateLimitResult(
            allowed=bool(result[0]),
            remaining=int(result[1]),
            retry_after=int(result[2]),
        )