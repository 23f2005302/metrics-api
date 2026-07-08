from fastapi import FastAPI, Request, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List
from collections import defaultdict
import time
import uuid
import jwt

app = FastAPI()

# ==========================================
# GLOBAL TRACKING (For Q6 & Q10)
# ==========================================
APP_START_TIME = time.time()
REQUEST_COUNT = 0
LOGS = []

# Rate limiter bucket for Q10
RATE_LIMIT_DATA = defaultdict(list)
RATE_LIMIT = 15
RATE_WINDOW = 10

# ==========================================
# 🚨 THE CORS FIX 🚨
# Browsers block expose_headers=["*"] if credentials are True.
# We must explicitly list the custom headers the grader needs to read!
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dash-qju8pt.example.com",     # Q1 Grader
        "https://exam.sanand.workers.dev",     # Your Browser (Q3, Q10)
        "https://app-lkptr8.example.com"       # Q10 Assigned Origin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time", "Retry-After"] 
)

# ==========================================
# GLOBAL MIDDLEWARE (Q1, Q6, & Q10)
# ==========================================
@app.middleware("http")
async def global_middleware(request: Request, call_next):
    global REQUEST_COUNT, LOGS, RATE_LIMIT_DATA
    
    # --- Q10: PER-CLIENT RATE LIMITING ---
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        # Clean up timestamps older than 10 seconds
        RATE_LIMIT_DATA[client_id] = [ts for ts in RATE_LIMIT_DATA[client_id] if now - ts < RATE_WINDOW]
        
        # Check if they exceeded the assigned 15 requests
        if len(RATE_LIMIT_DATA[client_id]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429, 
                content={"error": "Too Many Requests"}, 
                headers={
                    "Retry-After": str(RATE_WINDOW),
                    "X-Request-ID": request.headers.get("X-Request-ID", str(uuid.uuid4()))
                }
            )
        RATE_LIMIT_DATA[client_id].append(now)

    # --- Q6: PROMETHEUS COUNTER ---
    REQUEST_COUNT += 1
    
    start_time = time.time()
    
    # --- Q10 & Q1: REQUEST CONTEXT ID ---
    # If the user sends an ID, reuse it. Otherwise, make a new one.
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
        
    # Save the ID so endpoints (like /ping) can read it
    request.state.req_id = request_id
    
    # --- Q6: STRUCTURED LOGS ---
    LOGS.append({
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    })
    if len(LOGS) > 100:
        LOGS.pop(0)

    # PROCESS THE ACTUAL REQUEST
    response = await call_next(request)
    
    # --- Q10 & Q1: RESPONSE HEADERS ---
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# ==========================================
# QUESTION 10: PING ENDPOINT
# ==========================================
@app.get("/ping")
def ping_endpoint(request: Request):
    return {
        "email": "23f2005302@ds.study.iitm.ac.in",
        "request_id": request.state.req_id
    }

# ==========================================
# QUESTION 1: THE STATS ENDPOINT
# ==========================================
@app.get("/stats")
def get_stats(values: str):
    try:
        int_values = [int(v) for v in values.split(",")]
    except ValueError:
        return {"error": "Invalid input."}

    count = len(int_values)
    return {
        "email": "23f2005302@ds.study.iitm.ac.in",
        "count": count,
        "sum": sum(int_values),
        "min": min(int_values),
        "max": max(int_values),
        "mean": sum(int_values) / count
    }

# ==========================================
# QUESTION 2: THE JWT VERIFY ENDPOINT
# ==========================================
PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\n"
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY\n"
    "cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID\n"
    "EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc\n"
    "WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW\n"
    "ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI\n"
    "SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX\n"
    "dQIDAQAB\n"
    "-----END PUBLIC KEY-----"
)

@app.post("/verify")
async def verify_token(request: Request):
    try:
        body = await request.json()
        decoded = jwt.decode(
            body.get("token"),
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer="https://idp.exam.local",
            audience="tds-0vwph3az.apps.exam.local",
            leeway=60 
        )
        return {
            "valid": True,
            "email": decoded.get("email"),
            "sub": decoded.get("sub"),
            "aud": decoded.get("aud")
        }
    except Exception:
        return JSONResponse(status_code=401, content={"valid": False})

# ==========================================
# QUESTION 3: THE EFFECTIVE CONFIG ENDPOINT
# ==========================================
@app.get("/effective-config")
def get_effective_config(request: Request):
    try:
        set_params = request.query_params.getlist("set")
        
        config = {
            "port": 8893,
            "workers": 12,
            "debug": True,
            "log_level": "error",
            "api_key": "key-20gz5h8ynp"
        }
        
        for override in set_params:
            if "=" in override:
                key, value = override.split("=", 1)
                config[key] = value
                
        config["port"] = int(config["port"])
        config["workers"] = int(config["workers"])
        
        val = config["debug"]
        if isinstance(val, bool):
            config["debug"] = val
        else:
            config["debug"] = str(val).lower() in ("true", "1", "yes", "on")
            
        for k in list(config.keys()):
            if k not in ["port", "workers", "debug"]:
                config[k] = str(config[k])
                
        config["api_key"] = "****"
        
        return config
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ==========================================
# QUESTION 5: POST ANALYTICS ENDPOINT
# ==========================================
class Event(BaseModel):
    user: str
    amount: float
    ts: int

class AnalyticsPayload(BaseModel):
    events: List[Event]

@app.post("/analytics")
def analyze_events(
    payload: AnalyticsPayload, 
    x_api_key: str = Header(None) 
):
    if x_api_key != "ak_h5y8gsndyxzwpx4r2h2t6bma":
        return JSONResponse(status_code=401, content={"error": "Invalid API Key"})

    events = payload.events
    total_events = len(events)
    unique_users = set()
    user_revenue = {}
    total_revenue = 0.0
    
    for event in events:
        unique_users.add(event.user)
        if event.amount > 0:
            total_revenue += event.amount
            user_revenue[event.user] = user_revenue.get(event.user, 0.0) + event.amount

    top_user = ""
    if user_revenue:
        top_user = max(user_revenue, key=user_revenue.get)

    return {
        "email": "23f2005302@ds.study.iitm.ac.in",
        "total_events": total_events,
        "unique_users": len(unique_users),
        "revenue": total_revenue,
        "top_user": top_user
    }

# ==========================================
# QUESTION 6: OBSERVABILITY ENDPOINTS
# ==========================================
@app.get("/work")
def do_work(n: int = Query(default=1)):
    return {"email": "23f2005302@ds.study.iitm.ac.in", "done": n}

@app.get("/metrics", response_class=PlainTextResponse)
def get_metrics():
    return f"http_requests_total {REQUEST_COUNT}\n"

@app.get("/healthz")
def get_health():
    uptime = time.time() - APP_START_TIME
    return {"status": "ok", "uptime_s": uptime}

@app.get("/logs/tail")
def get_logs(limit: int = Query(default=10)):
    return LOGS[-limit:]
