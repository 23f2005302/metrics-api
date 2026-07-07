from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid

# 1. Initialize the FastAPI application
app = FastAPI()

# 2. Configure the CORS Policy
# This ensures ONLY the specific website provided by your assignment can access your API.
# It automatically handles the "Preflight OPTIONS" checks the grader is looking for.
origins = [
    "https://dash-qju8pt.example.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"], 
    allow_headers=["*"],
)

# 3. Custom Middleware for Required Headers
# Middleware is a function that runs before and after every single request.
@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    # Start a timer
    start_time = time.time()
    
    # Generate a unique identifier for the request
    request_id = str(uuid.uuid4())

    # Pass the request down the line to be processed
    response = await call_next(request)

    # Stop the timer and calculate how long it took (in seconds)
    process_time = time.time() - start_time
    
    # Attach the required custom headers to the response
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    return response

# 4. The Stats Endpoint
@app.get("/stats")
def get_stats(values: str):
    # The 'values' parameter comes in as a string like "1,2,3"
    # We split it by the comma and convert each piece into an integer
    try:
        int_values = [int(v) for v in values.split(",")]
    except ValueError:
        return {"error": "Invalid input. Please provide comma-separated integers."}

    # Perform the required mathematical calculations
    count = len(int_values)
    total_sum = sum(int_values)
    minimum = min(int_values)
    maximum = max(int_values)
    mean = total_sum / count

    # Return the exact JSON structure requested by the grader
    return {
        "email": "23f2005302@ds.study.iitm.ac.in", # REPLACE THIS WITH YOUR LOGGED-IN EMAIL
        "count": count,
        "sum": total_sum,
        "min": minimum,
        "max": maximum,
        "mean": mean
    }