from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
import jwt

app = FastAPI()

# ==========================================
# 🚨 THE FINAL CORS FIX 🚨
# We now allow the Q1 mock grader AND your actual browser URL!
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dash-qju8pt.example.com",
        "https://exam.sanand.workers.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# QUESTION 1: THE STATS & HEADERS ENDPOINT
# ==========================================
@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    return response

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
