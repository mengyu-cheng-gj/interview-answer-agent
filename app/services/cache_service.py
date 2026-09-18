import hashlib
import json
import logging

import redis.asyncio as redis
from pydantic import ValidationError
from redis.exceptions import RedisError

from app.config import settings
from app.models.candidate import Candidate, TargetJob
from app.models.highlight import HighlightResult

logger = logging.getLogger("interview_agent")


class CacheService:
    def __init__(self):
        self.client = None
        self.ttl = settings.CACHE_TTL_SECONDS
        if settings.CACHE_ENABLED:
            self.client = redis.from_url(
                settings.REDIS_URL, decode_responses=True,
                socket_connect_timeout=2, socket_timeout=2,
            )

    @staticmethod
    def _highlight_key(candidate: Candidate, target_job: TargetJob) -> str:
        payload = {
            "version": settings.HIGHLIGHT_CACHE_VERSION,
            "model": settings.LLM_MODEL,
            "base_url": settings.LLM_BASE_URL,
            "candidate": candidate.model_dump(mode="json"),
            "target_job": target_job.model_dump(mode="json"),
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        return "interview:highlights:" + hashlib.sha256(encoded).hexdigest()

    async def get_highlights(self, candidate: Candidate,
                             target_job: TargetJob) -> HighlightResult | None:
        if self.client is None:
            return None
        try:
            raw = await self.client.get(self._highlight_key(candidate, target_job))
            if raw is None:
                return None
            result = HighlightResult.model_validate_json(raw)
            if result.candidate_id != candidate.candidate_id or len(result.highlights) > 5:
                return None
            valid_ids = {p.project_id for p in candidate.projects}
            if any(not set(h.source_project_ids) <= valid_ids for h in result.highlights):
                return None
            return result
        except (RedisError, ValidationError):
            logger.warning("亮点缓存读取失败，将重新生成。")
            return None

    async def set_highlights(self, candidate: Candidate, target_job: TargetJob,
                             result: HighlightResult) -> None:
        if self.client is None:
            return
        try:
            await self.client.set(self._highlight_key(candidate, target_job),
                                  result.model_dump_json(), ex=self.ttl)
        except RedisError:
            logger.warning("缓存写入失败，仍返回本次生成结果。")

    async def close(self) -> None:
        if self.client is not None:
            await self.client.aclose()
