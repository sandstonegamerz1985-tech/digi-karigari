"""Entry point of the backend. Run with:  uvicorn app.main:app --reload --port 8000"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (importing registers the tables)
from . import seed
from .config import settings
from .database import Base, engine
from .routers import (
    admin,
    ai,
    artisans,
    auth,
    disputes,
    messages,
    orders,
    planned,
    products,
    recommendations,
    reviews,
    search,
    trust_tiers,
)

# Make sure the upload folders exist before we serve them.
for _sub in ("products", "seed"):
    (settings.UPLOAD_DIR / _sub).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # creates tables if they do not exist yet
    logging.getLogger("uvicorn.error").info(
        "CORS allowed origins: %s | allowed origin pattern: %s | AI provider: %s",
        settings.CORS_ORIGINS,
        settings.CORS_ORIGIN_REGEX or "(none)",
        settings.AI_PROVIDER,
    )
    seed.ensure_seed_images()
    if settings.AUTO_SEED:
        seed.run()
    yield


app = FastAPI(title="Digi Karigari API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploaded product photos are served from /uploads/...
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

API_PREFIX = "/api"
ALL_ROUTERS = (
    auth.router,
    products.router,
    artisans.router,
    ai.router,
    orders.router,
    search.router,
    recommendations.router,
    messages.router,
    reviews.router,
    disputes.router,
    trust_tiers.router,
    admin.router,
    planned.router,
)

for r in ALL_ROUTERS:
    app.include_router(r, prefix=API_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    return {"app": "Digi Karigari API", "health": f"{API_PREFIX}/health", "docs": "/docs"}


@app.get(f"{API_PREFIX}/health", tags=["meta"])
def health():
    return {"status": "ok"}
