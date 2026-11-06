from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A production-oriented starter API for ingesting insurance-policy "
        "content and answering grounded questions with citations."
    ),
)

app.include_router(router)
