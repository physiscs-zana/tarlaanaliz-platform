# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: CORS politikası; settings-driven allowlist.
"""CORS middleware setup with settings-driven policy."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.presentation.api.settings import settings


def add_cors_middleware(app: FastAPI) -> None:
    """Attach CORS middleware when enabled by settings."""
    if not settings.cors.enabled:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
        allow_credentials=settings.cors.allow_credentials,
        max_age=600,
    )
