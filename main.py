import base64
import os
import json
import asyncio
import re
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError

app = FastAPI()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class AudioRequest(BaseModel):
    audio_id: str
    audio_base64: str

@app.post("/analyze-audio")
async def analyze_audio(request: AudioRequest):
    expected_structure = {
        "rows": 0, "columns": [], "mean": {}, "std": {}, "variance": {}, 
        "min": {}, "max": {}, "median": {}, "mode": {}, "range": {}, 
        "allowed_values": {}, "value_range": {}, "correlation": []
    }

    # List of models to try in case of 429 errors
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]
    
    audio_bytes = base64.b64decode(request.audio_base64)
    
    system_instruction = (
        "You are an expert data analyst and multi-lingual audio transcription tool. "
        "Listen carefully to the provided audio, which describes statistical data. "
        "The audio may be spoken in Korean, Japanese, English, or other languages. "
        "CRITICAL RULES: "
        "1. Accurately identify the column names in the EXACT language spoken (e.g., if Korean is spoken, output ['키', '몸무게']). DO NOT TRANSLATE the column names. "
        "2. You MUST output your response strictly as a JSON object matching this schema: "
        '{"rows": int, "columns": [str], "mean": {}, "std": {}, "variance": {}, "min": {}, '
        '"max": {}, "median": {}, "mode": {}, "range": {}, "allowed_values": {}, '
        '"value_range": {}, "correlation": []}. '
        "Do not include any conversational text."
    )

    # We will try up to 3 times total across models with a short delay if rate limited
    for attempt in range(3):
        # Alternate models on retries to bypass specific model quotas
        model_name = models_to_try[attempt % len(models_to_try)]
        
        try:
            print(f"Attempt {attempt + 1}: Using model {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    "Listen to this audio and extract the statistical metadata into the required JSON format.",
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3") 
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,
                    response_mime_type="application/json",
                )
            )
            
            raw_text = response.text.strip()
            result_json = json.loads(raw_text)
            
            # Ensure the response has all the required keys
            for key in expected_structure.keys():
                if key not in result_json:
                    result_json[key] = expected_structure[key]

            return result_json

        except APIError as e:
            if e.code == 429:
                print(f"Rate limit hit on {model_name}. Waiting 4 seconds before trying alternative...")
                await asyncio.sleep(4)  # Give the API a brief moment to breathe
                continue
            else:
                print(f"API Error occurred: {e}")
                break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    # Ultimate fallback if everything gets completely choked out by quota limits
    return expected_structure
