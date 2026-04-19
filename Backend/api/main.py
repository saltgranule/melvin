from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
import os
import sys

# Ensure Backend/python is in path for core imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))

from core.database import get_session, SessionLocal, init_db
from core.models import GuildConfig, DashboardLog
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# load env from the same directory as main.py
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

app = FastAPI()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "123456789")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "your_secret")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/callback")
SESSION_SECRET = os.getenv("SESSION_SECRET", "super-secret-key")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

DISCORD_API_ENDPOINT = "https://discord.com/api/v10"

frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Frontend"))

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

@app.on_event("startup")
async def startup_event():
    init_db()

# ── static assets (css, js, public) ──
app.mount("/css", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_path, "js")), name="js")
app.mount("/public", StaticFiles(directory=os.path.join(frontend_path, "public")), name="public")

# ── page routes ──
@app.get("/")
async def index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/login")
async def login_redirect():
    return RedirectResponse("/auth/discord", status_code=302)

@app.get("/auth/discord")
async def auth_discord():
    auth_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    )
    return RedirectResponse(auth_url, status_code=302)

@app.get("/callback")
async def callback(request: Request, code: str):
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = await client.post(f"{DISCORD_API_ENDPOINT}/oauth2/token", data=data, headers=headers)

        if response.status_code != 200:
            print(f"token exchange failed: {response.status_code} {response.text}")
            return RedirectResponse("/?error=auth_failed", status_code=302)

        token_data = response.json()
        access_token = token_data.get("access_token")

        # fetch user info only — guilds fetched on demand to avoid cookie overflow
        user_response = await client.get(
            f"{DISCORD_API_ENDPOINT}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if user_response.status_code != 200:
            print(f"user fetch failed: {user_response.status_code} {user_response.text}")
            return RedirectResponse("/?error=auth_failed", status_code=302)

        user_data = user_response.json()

        # store only small data in session cookie
        request.session["user"] = {
            "id": user_data.get("id"),
            "username": user_data.get("username"),
            "global_name": user_data.get("global_name"),
            "avatar": user_data.get("avatar"),
        }
        request.session["access_token"] = access_token

        return RedirectResponse("/servers", status_code=302)

@app.get("/servers")
async def servers_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/auth/discord", status_code=302)
    return FileResponse(os.path.join(frontend_path, "servers.html"))

@app.get("/api/me")
async def get_me(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")
    return {"user": user}

@app.get("/api/guilds")
async def get_guilds(request: Request):
    user = request.session.get("user")
    access_token = request.session.get("access_token")
    if not user or not access_token:
        raise HTTPException(status_code=401, detail="not authenticated")

    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="bot token not configured")

    async with httpx.AsyncClient() as client:
        # fetch user's guilds and bot's guilds in parallel
        user_guilds_resp, bot_guilds_resp = await asyncio.gather(
            client.get(
                f"{DISCORD_API_ENDPOINT}/users/@me/guilds",
                headers={"Authorization": f"Bearer {access_token}"},
            ),
            client.get(
                f"{DISCORD_API_ENDPOINT}/users/@me/guilds",
                headers={"Authorization": f"Bot {BOT_TOKEN}"},
            ),
        )

    if user_guilds_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="failed to fetch user guilds")
    if bot_guilds_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="failed to fetch bot guilds")

    user_guilds = user_guilds_resp.json()
    bot_guild_ids = {g["id"] for g in bot_guilds_resp.json()}

    MANAGE_GUILD = 0x20

    # return only guilds where: user has manage_guild AND bot is present
    mutual_guilds = [
        g for g in user_guilds
        if (int(g["permissions"]) & MANAGE_GUILD) == MANAGE_GUILD
        and g["id"] in bot_guild_ids
    ]

    return {"guilds": mutual_guilds}

@app.get("/manage/{guild_id}")
async def management_page(request: Request, guild_id: str):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/auth/discord", status_code=302)
    
    # Check if user has permission for this guild (security)
    # Actually, for now we serve the page and the JS will check if valid
    return FileResponse(os.path.join(frontend_path, "management.html"))

@app.get("/api/guild/{guild_id}")
async def get_guild_details(request: Request, guild_id: str):
    user = request.session.get("user")
    access_token = request.session.get("access_token")
    if not user or not access_token:
        raise HTTPException(status_code=401, detail="not authenticated")

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        resp = await client.get(f"{DISCORD_API_ENDPOINT}/guilds/{guild_id}?with_counts=true", headers=headers)
        
        if resp.status_code != 200:
            return JSONResponse({"error": "could not fetch guild from discord"}, status_code=404)
            
        guild_data = resp.json()

        # Merge with database config
        db = SessionLocal()
        try:
            config = db.query(GuildConfig).filter(GuildConfig.guild_id == int(guild_id)).first()
            if not config:
                # Create default config if missing
                config = GuildConfig(guild_id=int(guild_id))
                db.add(config)
                db.commit()
                db.refresh(config)
            
            # Calculate module stats
            enabled_count = 0
            disabled_count = 0
            
            module_flags = [
                ("base", bool(config.base_enabled)),
                ("moderation", bool(config.moderation_enabled)),
                ("logging", bool(config.logging_enabled)),
                ("tickets", bool(config.tickets_enabled)),
                ("frogboard", bool(config.frogboard_enabled)),
                ("levels", bool(config.levels_enabled)),
                ("economy", bool(config.economy_enabled)),
                ("counting", bool(config.counting_enabled)),
            ]

            for _name, is_enabled in module_flags:
                if is_enabled:
                    enabled_count += 1
                else:
                    disabled_count += 1
            
            guild_data["config"] = {
                "base_enabled": config.base_enabled,
                "moderation_enabled": config.moderation_enabled,
                "logging_enabled": config.logging_enabled,
                "tickets_enabled": config.tickets_enabled,
                "frogboard_enabled": config.frogboard_enabled,
                "levels_enabled": config.levels_enabled,
                "economy_enabled": config.economy_enabled,
                "counting_enabled": config.counting_enabled,
                "mod_log_channel_id": config.mod_log_channel_id
            }

            guild_data["metrics"] = {
                "enabled_modules": enabled_count,
                "disabled_modules": disabled_count,
                "commands_ran": config.commands_ran or 0,
                "message_count": config.message_count or 0,
                "joined_at": config.joined_at.isoformat() if config.joined_at else None,
                "member_count": guild_data.get("approximate_member_count", 0),
                "peak_online": config.peak_online or 0
            }
        finally:
            db.close()
            
        return guild_data

@app.get("/api/guild/{guild_id}/logs")
async def get_guild_logs(request: Request, guild_id: str):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")

    db = SessionLocal()
    try:
        logs = db.query(DashboardLog).filter(DashboardLog.guild_id == int(guild_id)).order_by(DashboardLog.timestamp.desc()).limit(5).all()
        return [
            {
                "user_id": str(log.user_id),
                "user_name": log.user_name,
                "user_avatar": log.user_avatar,
                "action": log.action,
                "timestamp": log.timestamp.isoformat()
            } for log in logs
        ]
    finally:
        db.close()

@app.patch("/api/guild/{guild_id}/config")
async def update_guild_config(request: Request, guild_id: str, data: dict):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")

    db = SessionLocal()
    try:
        config = db.query(GuildConfig).filter(GuildConfig.guild_id == int(guild_id)).first()
        if not config:
            raise HTTPException(status_code=404, detail="config not found")

        # module toggles
        module_fields = [
            "base_enabled",
            "moderation_enabled",
            "logging_enabled",
            "tickets_enabled",
            "frogboard_enabled",
            "levels_enabled",
            "economy_enabled",
            "counting_enabled",
        ]

        for field in module_fields:
            if field in data:
                old_val = bool(getattr(config, field))
                new_val = bool(data[field])
                if old_val != new_val:
                    setattr(config, field, new_val)
                    module_name = field.replace("_enabled", "")
                    log = DashboardLog(
                        guild_id=int(guild_id),
                        user_id=int(user["id"]),
                        user_name=user.get("global_name") or user.get("username"),
                        user_avatar=user.get("avatar"),
                        action=f"{'enabled' if new_val else 'disabled'} {module_name} module"
                    )
                    db.add(log)
        
        if "mod_log_channel_id" in data:
            config.mod_log_channel_id = data["mod_log_channel_id"]
            # Log action
            log = DashboardLog(
                guild_id=int(guild_id),
                user_id=int(user["id"]),
                user_name=user.get("global_name") or user.get("username"),
                user_avatar=user.get("avatar"),
                action=f"updated mod log channel to {data['mod_log_channel_id']}"
            )
            db.add(log)

        db.commit()
        return {"status": "success"}
    finally:
        db.close()

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
