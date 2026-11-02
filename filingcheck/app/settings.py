"""API settings, read from the environment."""

import logging
import os
import secrets
from collections.abc import Mapping

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# 70% of a 200,000-token daily limit over about 2,130 tokens a question; docs/decisions.md.
DEFAULT_DAILY_CAP = 65
PER_IP_PER_HOUR = 20
MAX_QUESTION_CHARS = 500
# Far above any valid request (a question is at most 500 characters); see limits.BodySizeLimit.
MAX_BODY_BYTES = 16 * 1024
DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)


class Settings(BaseModel):
    """Limits and origins for one running API."""

    daily_cap: int = Field(default=DEFAULT_DAILY_CAP, ge=0)  # model calls per UTC day
    per_ip_per_hour: int = Field(default=PER_IP_PER_HOUR, ge=1)
    cors_origins: list[str] = Field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))
    ip_hash_salt: str = Field(default_factory=lambda: secrets.token_hex(16))
    # Proxies in front of the app that append to X-Forwarded-For; 0 trusts no header.
    forwarded_hops: int = Field(default=0, ge=0)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        """FC_DAILY_CAP, FC_CORS_ORIGINS (comma-separated), FC_IP_HASH_SALT, FC_FORWARDED_HOPS."""
        env = os.environ if env is None else env
        values: dict[str, object] = {}
        if env.get("FC_DAILY_CAP"):
            values["daily_cap"] = int(env["FC_DAILY_CAP"])
        if env.get("FC_CORS_ORIGINS"):
            values["cors_origins"] = [
                o.strip() for o in env["FC_CORS_ORIGINS"].split(",") if o.strip()
            ]
        if env.get("FC_FORWARDED_HOPS"):
            values["forwarded_hops"] = int(env["FC_FORWARDED_HOPS"])
        if env.get("FC_IP_HASH_SALT"):
            values["ip_hash_salt"] = env["FC_IP_HASH_SALT"]
        else:
            log.warning(
                "FC_IP_HASH_SALT is not set; using a random salt, so the per-address count in "
                "the request log restarts with the process"
            )
        return cls.model_validate(values)
