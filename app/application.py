
import os
import httpx
import feedparser

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.db import create_db_and_tables
from app.users import (
    auth_backend,
    fastapi_users,
    current_active_user,
)
from app.schemas import UserRead, UserCreate, UserUpdate

# =========================
# LOAD ENV
# =========================

load_dotenv()

# =========================
# APP LIFESPAN
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    await create_db_and_tables()
    yield
    print("Application shutdown...")


app = FastAPI(
    title="Cricketapp prototype",
    version="1.0.0",
    lifespan=lifespan,
)

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# CONSTANTS
# =========================

CRICAPI_BASE = "https://api.cricapi.com/v1"
NEWS_RSS_URL = "https://feeds.bbci.co.uk/sport/cricket/rss.xml"

# =========================
# AUTH ROUTES
# =========================

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
# =========================
# API KEY
# =========================

def get_api_key() -> str:
    key = os.getenv("CRICAPI_KEY")

    if not key:
        raise HTTPException(
            status_code=500,
            detail="CRICAPI_KEY is not configured",
        )

    return key


# =========================
# HEALTH CHECK
# =========================

@app.get("/api/healthz")
def health_check():
    return {"status": "ok"}


# =========================
# CURRENT USER TEST
# =========================

@app.get("/api/me")
async def get_me(user=Depends(current_active_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
    }


# =========================
# CRICKET NEWS
# =========================

@app.get("/api/cricket/news")
async def get_cricket_news():
    try:
        feed = feedparser.parse(NEWS_RSS_URL)

        articles = []

        for entry in feed.entries:
            articles.append({
                "id": entry.get("id") or entry.get("link"),
                "title": entry.get("title"),
                "summary": entry.get("summary"),
                "link": entry.get("link"),
                "published": entry.get("published"),
                "source": "BBC Sport Cricket",
                "imageUrl": (
                    entry.get("media_thumbnail", [{}])[0].get("url")
                    if entry.get("media_thumbnail")
                    else None
                ),
            })

        return {
            "data": articles,
            "total": len(articles),
        }

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch cricket news: {str(e)}",
        )


# =========================
# LIVE SCORES
# =========================

@app.get("/api/cricket/live-scores")
async def get_live_scores(
    user=Depends(current_active_user),
):
    api_key = get_api_key()

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{CRICAPI_BASE}/currentMatches",
            params={
                "apikey": api_key,
                "offset": 0,
            },
        )

    data = response.json()

    if data.get("status") != "success":
        raise HTTPException(
            status_code=502,
            detail={
                "error": "CricAPI error",
                "reason": data.get("reason"),
            },
        )

    items = data.get("data", [])

    live_matches = [
        {
            "id": m.get("id"),
            "name": m.get("name"),
            "matchType": m.get("matchType"),
            "status": m.get("status"),
            "venue": m.get("venue"),
            "date": m.get("date"),
            "dateTimeGMT": m.get("dateTimeGMT"),
            "teams": m.get("teams", []),
            "teamInfo": m.get("teamInfo", []),
            "score": m.get("score", []),
            "tossWinner": m.get("tossWinner"),
            "tossChoice": m.get("tossChoice"),
            "matchWinner": m.get("matchWinner"),
            "matchStarted": m.get("matchStarted", False),
            "matchEnded": m.get("matchEnded", False),
        }
        for m in items
        if m.get("matchStarted") and not m.get("matchEnded")
    ]

    return {
        "data": live_matches,
        "total": len(live_matches),
    }


# =========================
# FIXTURES
# =========================

@app.get("/api/cricket/fixtures")
async def get_fixtures(
    user=Depends(current_active_user),
):
    api_key = get_api_key()

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{CRICAPI_BASE}/matches",
            params={
                "apikey": api_key,
                "offset": 0,
            },
        )

    data = response.json()

    if data.get("status") != "success":
        raise HTTPException(
            status_code=502,
            detail={
                "error": "CricAPI error",
                "reason": data.get("reason"),
            },
        )

    items = data.get("data", [])

    def map_match(m):
        return {
            "id": m.get("id"),
            "name": m.get("name"),
            "matchType": m.get("matchType"),
            "status": m.get("status"),
            "venue": m.get("venue"),
            "date": m.get("date"),
            "dateTimeGMT": m.get("dateTimeGMT"),
            "teams": m.get("teams", []),
            "teamInfo": m.get("teamInfo", []),
            "score": m.get("score", []),
            "matchStarted": m.get("matchStarted", False),
            "matchEnded": m.get("matchEnded", False),
        }

    return {
        "data": {
            "live": [
                map_match(m)
                for m in items
                if m.get("matchStarted") and not m.get("matchEnded")
            ],

            "upcoming": [
                map_match(m)
                for m in items
                if not m.get("matchStarted")
            ],

            "completed": [
                map_match(m)
                for m in items
                if m.get("matchEnded")
            ],
        },

        "total": len(items),
    }