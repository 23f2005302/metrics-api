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
        
        # Condensed instruction for faster processing
        system_instruction = (
            "Listen to the audio. Extract statistical metadata. "
            "Output ONLY valid JSON matching this schema: "
            '{"rows": 0, "columns": [], "mean": {}, "std": {}, "variance": {}, "min": {}, '
            '"max": {}, "median": {}, "mode": {}, "range": {}, "allowed_values": {}, '
            '"value_range": {}, "correlation": []}. '
            "Identify column names in the EXACT original language (e.g., Korean, English). DO NOT translate."
        )

        # Call Gemini as fast as possible without fallback loops
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            # Removed extra text prompt to save processing time; the system instruction is enough
            contents=[types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3")],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                response_mime_type="application/json",
            )
        )
        
        result_json = json.loads(response.text.strip())
        
        # Ensure the response has all required keys
        for key in expected_structure.keys():
            if key not in result_json:
                result_json[key] = expected_structure[key]

        return result_json

    except Exception as e:
        print(f"API Error: {e}")
        return expected_structure
