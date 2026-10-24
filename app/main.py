import asyncio
import base64
import io
import tempfile
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
from gtts import gTTS

from app.config import ALLOWED_ORIGINS, GEMINI_API_KEY, GEMINI_MODEL
from app.gemini_service import analyze_chunk, analyze_text_call, degraded_response, now_ts
from app.schemas import (
    AlertRequest, AlertResponse,
    AnalyzeRequest, AnalyzeResponse, AnalyzeTextRequest,
    TTSRequest, TTSResponse,
)

app = FastAPI(title="Suraksha AI — Real-Time Scam Protection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

_alert_log: list[dict] = []

FEMALE_NEURAL_VOICES = {
    "gu": "gu-IN-DhwaniNeural",            # Natural Gujarati Female voice
    "hi": "hi-IN-SwaraNeural",             # Natural Hindi Female voice
    "en": "en-IN-NeerjaExpressiveNeural",  # Natural Indian English Female voice
}

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Suraksha AI",
        "model": GEMINI_MODEL,
        "has_gemini_key": bool(GEMINI_API_KEY),
        "natural_voice_engine": "edge-tts-neural",
    }

@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        audio_bytes = base64.b64decode(req.audio_b64, validate=True)
    except ValueError:
        return degraded_response(req.context_summary, req.language)

    return analyze_chunk(
        audio_bytes=audio_bytes,
        mime_type=req.mime_type,
        context_summary=req.context_summary,
        elapsed_sec=req.elapsed_sec,
        lang=req.language,
    )

@app.post("/api/analyze-text", response_model=AnalyzeResponse)
def analyze_text(req: AnalyzeTextRequest):
    return analyze_text_call(
        transcript=req.text,
        lang=req.language,
    )

@app.post("/api/alert", response_model=AlertResponse)
def alert(req: AlertRequest):
    message = (
        f"SURAKSHA AI SAFETY ALERT for {req.contact_name}: "
        f"Call flagged as potential {req.scam_type.replace('_', ' ').upper()} "
        f"(Risk Level {req.risk}/100). Please call immediately to ensure safety."
    )
    logged_at = now_ts()
    _alert_log.append(
        {
            "call_id": req.call_id,
            "risk": req.risk,
            "scam_type": req.scam_type,
            "contact_name": req.contact_name,
            "message": message,
            "logged_at": logged_at,
        }
    )
    return AlertResponse(message=message, logged_at=logged_at)

@app.post("/api/tts", response_model=TTSResponse)
async def text_to_speech(req: TTSRequest):
    """
    Generates natural human female neural voice in Gujarati (gu-IN-DhwaniNeural),
    Hindi (hi-IN-SwaraNeural), or Indian English (en-IN-NeerjaExpressiveNeural).
    Eliminates robotic artifacts, delivering calm and reassuring human vocal cadences.
    """
    lang_code = req.language if req.language in FEMALE_NEURAL_VOICES else "gu"
    voice = FEMALE_NEURAL_VOICES.get(lang_code, "gu-IN-DhwaniNeural")

    try:
        # Edge TTS High-Fidelity Female Neural Audio
        communicate = edge_tts.Communicate(text=req.text, voice=voice)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
            temp_path = tf.name

        await communicate.save(temp_path)

        with open(temp_path, "rb") as f:
            audio_bytes = f.read()

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return TTSResponse(audio_b64=audio_b64, mime_type="audio/mp3")
    except Exception as e:
        print(f"Edge TTS error, trying fallback: {e}")
        try:
            tts = gTTS(text=req.text, lang=lang_code, tld=req.tld, slow=False)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_b64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
            return TTSResponse(audio_b64=audio_b64, mime_type="audio/mp3")
        except Exception as e2:
            print(f"Fallback TTS error: {e2}")
            return TTSResponse(audio_b64="", mime_type="audio/mp3")
