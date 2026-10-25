"""Entry point of the backend. Run with:  uvicorn app.main:app --reload --port 8000"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (importing registers the tables)
from . import seed
from .config import settings
from .database import Base, engine
from .routers import admin, ai, artisans, auth, orders, planned, products

# Make sure the upload folders exist before we serve them.
for _sub in ("products", "seed"):
    (settings.UPLOAD_DIR / _sub).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # creates tables if they do not exist yet
    # On hosts with a temporary disk (like Render's free plan) the sample pictures vanish on every
    # restart, so we quietly re-create any that are missing.
    seed.ensure_seed_images()
    if settings.AUTO_SEED:
        seed.run()  # does nothing if the database already has data
    yield


app = FastAPI(title="Digi Karigari API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=False,  # we use an Authorization header, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploaded product photos are served from /uploads/...
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

API_PREFIX = "/api"
for r in (auth.router, products.router, artisans.router, ai.router, orders.router, admin.router, planned.router):
    app.include_router(r, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/health", tags=["meta"])
def health():
    return {"status": "ok"}
