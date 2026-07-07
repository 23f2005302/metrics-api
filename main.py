from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time
import uuid
import jwt

app = FastAPI()

# ==========================================
# QUESTION 1: THE STATS & CORS ENDPOINT
# ==========================================

origins = ["https://dash-qju8pt.example.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # FIX: Changed to "*" to allow the POST request for Q2
    allow_headers=["*"],
)

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
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbyGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyjJG2axVfmq7i6SuKr1JoWYG7xTTAvKPujS140tsQfO3h5NepzdfXpr28oNnzfW
ed+zc1R6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd119VDetJZVEgC5tkyvXsfI
SI6iyrYbkR0NEBSqq4XkadEjsCs4F1RncsS4L1gniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

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
            leeway=60 # FIX: This allows for a 60-second clock difference between servers!
        )
        return {
            "valid": True,
            "email": decoded_payload.get("email"),
            "sub": decoded_payload.get("sub"),
            "aud": decoded_payload.get("aud")
        }
    except Exception as e:
        # FIX: If it fails again, this will echo the exact error back to the grader
        return JSONResponse(
            status_code=401,
            content={"valid": False, "error": str(e)}
        )
