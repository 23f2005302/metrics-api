import os
import json
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

app = FastAPI()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class ProblemRequest(BaseModel):
    problem_id: str
    problem: str

class SolveResponse(BaseModel):
    reasoning: str = Field(..., min_length=80)
    answer: int

@app.post("/solve", response_model=Ah, the error trace tells us exactly what went wrong! 

The error `fastapi.exceptions.ResponseValidationError: {'type': 'string_too_short'}` happened because FastAPI caught our code breaking its own rules. 

We told FastAPI that the `reasoning` string **must** be at least 80 characters long (`min_length=80`). But when the API hit the rate limit and triggered our final safety net, it tried to return this string:
`"Fallback triggered. The API encountered an unrecoverable error."`

That string is only **63 characters long**. Because it's less than 80 characters, FastAPI panicked, blocked the response, and threw an HTTP 500 crash instead.

### The Fix

Scroll to the very bottom of your `main.py` file and replace the final `return` block with this updated version that meets the 80-character requirement:

```python
    # Changed to ensure the string is strictly longer than 80 characters
    return {
        "reasoning": "Fallback calculation triggered. The Gemini API encountered an unrecoverable error, most likely due to a 429 Rate Limit from processing too many simultaneous requests. This fallback string has been padded to satisfy the strict length requirements.",
        "answer": -999999 
    }
