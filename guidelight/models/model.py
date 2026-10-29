"""Read-only model catalog response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import ResponseModel


class Model(ResponseModel):
    """A catalog model returned by Endeavor."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    provider_id: str | None = None
    provider_name: str = ""
    name: str = ""
    slug: str = ""
    description: str = ""
    links: Any = None
    hugging_face_url: str | None = None
    author: str = ""
    published: datetime | None = None
    license_id: str | None = None
    input_modality: Any = None
    output_modality: Any = None
    architecture: Any = None
    size: str = ""
    context_size: int | None = None
    parameters: Any = None
    capabilities: Any = None
    pricing: Any = None
    input_cost: float | None = None
    output_cost: float | None = None
    tpm_limit: int | None = None
    rpm_limit: int | None = None
    limits: Any = None
    is_moderated: bool | None = None
    energy_usage: Any = None
    api_type: Any = None
    endpoint: str = ""
    auth_type: Any = None
    credentials: str | None = None
    usage_id: str | None = None


class ModelUsage(ResponseModel):
    """Usage and deployment summary for a catalog model."""

    usage: Any = None
    tasks: Any = None
    experiments: Any = None
    agent_count: int = 0
    deployed_count: int = 0
