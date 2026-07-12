import base64
import os
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI()

# Use the modern client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class ImageQARequest(BaseModel):
    image_base64: str
    question: str

@app.post("/answer-image")
async def answer_image(request: ImageQARequest):
    try:
        image_bytes = base64.b64decode(request.image_base64)
        
        # 1. Define the most restrictive system instruction possible
        system_instruction = (
            "You are a data extraction machine. "
            "Task: Answer the user question based on the image. "
            "Output constraints: RETURN ONLY THE VALUE. No symbols, no units, no text. "
            "Example: If the answer is $4089.35, return '4089.35'."
        )

        # 2. Re-initialize client with system instruction
        model = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[request.question, types.Part.from_bytes(data=image_bytes, mime_type="image/png")],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0  # Force the model to be deterministic
            )
        )
        
        # 3. Final aggressive cleaning
        answer = model.text.strip()
        # Remove anything that isn't a digit, a decimal point, or a dash (for negative numbers)
        answer = re.sub(r'[^\d.-]', '', answer)
        
        return {"answer": answer}
        
    except Exception as e:
        return {"answer": "0"}
