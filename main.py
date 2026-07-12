import base64
from fastapi import FastAPI, Request
from pydantic import BaseModel
from google import genai
from google.genai import types
import os

app = FastAPI()

# Initialize the Gemini Client
# Ensure GEMINI_API_KEY is set in Render Environment variables
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class ImageQARequest(BaseModel):
    image_base64: str
    question: str

@app.post("/answer-image")
async def answer_image(request: ImageQARequest):
    try:
        # Decode base64 to bytes
        image_bytes = base64.b64decode(request.image_base64)
        
        # Use the modern Gemini client to generate content
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=[
                request.question,
                types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            ]
        )
        
        return {"answer": response.text.strip()}
    except Exception as e:
        # Returning the error helps debug in Render logs
        return {"error": str(e)}
