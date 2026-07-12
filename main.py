import base64
import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types

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

    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        
        system_instruction = (
            "You are a strict data extraction tool. Listen to the audio and extract the described dataset statistics.\n"
            "CRITICAL RULES:\n"
            "1. Identify the column/variable names in the EXACT language spoken (e.g., Korean keywords like '키', '몸무게'). Do not translate them to English.\n"
            "2. Output ONLY a valid JSON object matching the requested schema. No markdown, no markdown code blocks, no conversational filler."
        )

        # Force JSON output structure matching the requirements
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                "Analyze this audio file and extract the data into the requested JSON schema. Ensure column names match the exact spoken language.",
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3")
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "rows": {"type": "INTEGER"},
                        "columns": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "mean": {"type": "OBJECT"},
                        "std": {"type": "OBJECT"},
                        "variance": {"type": "OBJECT"},
                        "min": {"type": "OBJECT"},
                        "max": {"type": "OBJECT"},
                        "median": {"type": "OBJECT"},
                        "mode": {"type": "OBJECT"},
                        "range": {"type": "OBJECT"},
                        "allowed_values": {"type": "OBJECT"},
                        "value_range": {"type": "OBJECT"},
                        "correlation": {"type": "ARRAY", "items": {"type": "STRING"}}
                    },
                    "required": ["rows", "columns"]
                }
            )
        )
        
        result_json = json.loads(response.text.strip())
        
        # Fill in any missing structural keys automatically
        for key in expected_structure.keys():
            if key not in result_json:
                result_json[key] = expected_structure[key]

        return result_json

    except Exception as e:
        print(f"API Error: {e}")
        return expected_structure
