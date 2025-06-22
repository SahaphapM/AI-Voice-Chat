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
import requests
import tempfile
from faster_whisper import WhisperModel


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
            {"role": "system", "content": "Your name is Brian, You are an English speaking coach."},
            {"role": "user", "content": message}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    reply = response.json()["choices"][0]["message"]["content"]
    return JSONResponse({"reply": reply})


# โหลดโมเดล Whisper
model = WhisperModel("tiny", device="cpu")  # หรือเลือกขนาดอื่น ตามต้องการ เช่น "base", "small", "medium", "large"
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    
    audio_bytes = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    segments, _ = model.transcribe(tmp_path)
    text = " ".join(seg.text for seg in segments)
    return {"transcript": text.strip()}

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