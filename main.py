from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time
import uuid
import jwt

app = FastAPI()

# Enable Global CORS for all grader questions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
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
    total_sum = sum(int_values)
    minimum = min(int_values)
    maximum = max(int_values)
    mean = total_sum / count

    return {
        "email": "23f2005302@ds.study.iitm.ac.in",
        "count": count,
        "sum": total_sum,
        "min": minimum,
        "max": maximum,
        "mean": mean
    }

# ==========================================
# QUESTION 2: THE JWT VERIFY ENDPOINT
# ==========================================
ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-0vwph3az.apps.exam.local"

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

class TokenRequest(BaseModel):
    token: str

@app.post("/verify")
def verify_token(request: TokenRequest):
    try:
        decoded_payload = jwt.decode(
            request.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            leeway=60 
        )
        return {
            "valid": True,
            "email": decoded_payload.get("email"),
            "sub": decoded_payload.get("sub"),
            "aud": decoded_payload.get("aud")
        }
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"valid": False, "error": str(e)}
        )

# ==========================================
# QUESTION 3: THE EFFECTIVE CONFIG ENDPOINT
# ==========================================
def parse_boolean(val):
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("true", "1", "yes", "on")

@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])):
    # Layer 1
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }
    
    # Layer 2
    config["log_level"] = "error"
    
    # Layer 3
    env_layer = {
        "APP_PORT": "8838",
        "NUM_WORKERS": "12",
        "APP_DEBUG": "true"
    }
    if "APP_PORT" in env_layer: config["port"] = env_layer["APP_PORT"]
    if "NUM_WORKERS" in env_layer: config["workers"] = env_layer["NUM_WORKERS"]
    if "APP_DEBUG" in env_layer: config["debug"] = env_layer["APP_DEBUG"]
    
    # Layer 4
    os_layer = {
        "APP_PORT": "8893",
        "APP_API_KEY": "key-20gz5h8ynp"
    }
    if "APP_PORT" in os_layer: config["port"] = os_layer["APP_PORT"]
    if "APP_API_KEY" in os_layer: config["api_key"] = os_layer["APP_API_KEY"]
    
    # Layer 5 (Overrides)
    for override in set:
        if "=" in override:
            key, value = override.split("=", 1)
            config[key] = value
            
    # Coercion & Masking
    config["port"] = int(config["port"])
    config["workers"] = int(config["workers"])
    config["debug"] = parse_boolean(config["debug"])
    
    for k in config.keys():
        if k not in ["port", "workers", "debug"]:
            config[k] = str(config[k])
            
    config["api_key"] = "****"
    
    return config
