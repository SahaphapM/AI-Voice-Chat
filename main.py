import io
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
import os
import httpx
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

    # รายการโมเดลสำรอง (เรียงลำดับตามความต้องการ)
    free_models = [
        # "openchat/openchat-7b",           # โมเดลเร็วพิเศษสำหรับแชท พัง
        "mistralai/mistral-7b-instruct",  # โมเดลหลัก
        "gryphe/mythomax-l2-13b", # (ขนาด 2B ที่เล็กกว่าและเร็วขึ้น)
        "google/gemma-3n-e4b-it" ,  
        "google/gemma-7b-it",             # สำรองที่ 1
        "huggingfaceh4/zephyr-7b-beta",   # สำรองที่ 2
        "anthropic/claude-3-haiku" ,       # สำรองที่ 3
        "meta-llama/llama-3-8b-instruct"  # สำรอง 4 - โมเดลใหม่จาก Meta
    ]

    # ข้อมูลพื้นฐานสำหรับทุกโมเดล
    base_body = {
        "max_tokens": 250,  # ลดความยาวคำตอบลงเล็กน้อย
        "temperature": 0.5,  # ลดการสุ่มให้ตอบตรงประเด็นมากขึ้น
        "top_k": 30,         # เพิ่มความเร็วการประมวลผล
        "messages": [
           {
                "role": "system",
                "content": (
                    "You are Brian, an English speaking coach. Your responses MUST:\n"
                    "1. Be in English ONLY\n"
                    "2. Correct user's grammar mistakes concisely\n"
                    "3. Give 1 short practice tip\n"
                    "4. Keep responses to 1-2 sentences MAX\n"
                )
            },
            {"role": "user", "content": message}
        ]
    }

    # ลองส่งคำขอด้วยโมเดลต่างๆ ตามลำดับ
    async with httpx.AsyncClient() as client:
        for model_name in free_models:
            try:
                body = {**base_body, "model": model_name}
                
               # ใช้ asynchronous request
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=5  # timeout สั้นลง
                )
                response.raise_for_status()
                
                reply = response.json()["choices"][0]["message"]["content"]
                return JSONResponse({"reply": reply, "model_used": model_name})
            
            except Exception as e:
                print(f"Error with model {model_name}: {str(e)}")
                continue  # ลองโมเดลถัดไป

    # หากทุกโมเดลล้มเหลว
    return JSONResponse(
        {"error": "All models failed to respond. Please try again later."},
        status_code=500
    )
# โหลดโมเดล Whisper
# โหลดโมเดล Whisper สำหรับภาษาอังกฤษเฉพาะ
model = WhisperModel(
    "tiny.en",  # แนะนำให้ใช้ base.en สำหรับสมดุลความเร็วและความแม่นยำ
    device="cpu",
    compute_type="int8",
    # cpu_threads=4  # ใช้ CPU threads ให้เต็มที่ (ปรับตามเครื่อง)
    # download_root="./whisper_models"  # ระบุโฟลเดอร์เก็บโมเดล
)

# ในส่วน transcribe
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    try:
        # ใช้ BytesIO เพื่อหลีกเลี่ยงการเขียนไฟล์ชั่วคราว
        audio_buffer = io.BytesIO(audio_bytes)
        
        # ตั้งค่าพารามิเตอร์เพื่อเพิ่มความเร็วและความแม่นยำ
        segments, info = model.transcribe(
            audio_buffer,
            language="en",          # ระบุภาษาเป็นภาษาอังกฤษ
            task="transcribe",      # งานถอดความ
            vad_filter=True,        # กรองเสียงเงียบ
            beam_size=5,            # เพิ่มความแม่นยำ (ค่าเริ่มต้น=5)
            without_timestamps=True # ไม่ต้องคืนค่า timestamp แต่ละส่วน (เร็วขึ้น)
        )
        
        # รวมข้อความ
        text = " ".join(segment.text for segment in segments)
        return {"transcript": text.strip()}
    
    except Exception as e:
        return JSONResponse(
            {"error": f"Transcription failed: {str(e)}"},
            status_code=500
        )

