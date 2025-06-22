import io
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from google.cloud import speech_v1p1beta1 as speech
import os
import numpy as np
import requests
import librosa
import whisper


load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
REFERER = os.getenv("OPENROUTER_REFERER")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(message: str = Form(...)):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": REFERER,
        "Content-Type": "application/json"
    }

    body = {
        "model": "openai/gpt-3.5-turbo",  # หรือทดลองโมเดลฟรี เช่น "mistral-7b-instruct"
        "messages": [
            {"role": "system", "content": "You are an English speaking coach."},
            {"role": "user", "content": message}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    reply = response.json()["choices"][0]["message"]["content"]
    return JSONResponse({"reply": reply})


# โหลดโมเดล Whisper
model = whisper.load_model("small")  # หรือใช้ "small", "medium",  " 

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    data, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)  # Resampling ไปที่ 16 kHz

    # Whisper รับ float32 values อยู่ในช่วง [-1, +1]
    audio_float = data.astype(np.float32)

    result = model.transcribe(audio_float, language="en")
    return {"transcript": result["text"]}

# @app.post("/transcribe")
# async def transcribe(file: UploadFile = File(...)):
#     content = await file.read()
#     client = speech.SpeechClient()

#     audio = speech.RecognitionAudio(content=content)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
#         sample_rate_hertz=48000,
#         language_code="en-US"
#     )

#     response = client.recognize(config=config, audio=audio)

#     transcript = ""
#     for result in response.results:
#         transcript += result.alternatives[0].transcript + " "

#     return {"transcript": transcript.strip()}