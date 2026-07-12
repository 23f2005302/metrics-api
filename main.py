import base64
import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI()

# Initialize the modern Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ----------------------------------------------------
# 1. Define the incoming request model
# ----------------------------------------------------
class AudioRequest(BaseModel):
    audio_id: str
    audio_base64: str

# ----------------------------------------------------
# 2. Define the Audio Processing Endpoint
# ----------------------------------------------------
@app.post("/analyze-audio")
async def analyze_audio(request: AudioRequest):
    expected_structure = {
        "rows": 0, "columns": [], "mean": {}, "std": {}, "variance": {}, 
        "min": {}, "max": {}, "median": {}, "mode": {}, "range": {}, 
        "allowed_values": {}, "value_range": {}, "correlation": []
    }

    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        
        # 1. Multi-lingual System Instruction
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

        # 2. Changed mime_type to audio/mp3 which is standard for web graders
        response = client.models.generate_content(
            model="gemini-2.0-flash",
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
        
    except Exception as e:
        print(f"ERROR processing audio: {e}")
        return expected_structure
