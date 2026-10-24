import base64
import io
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS

from app.config import ALLOWED_ORIGINS, GEMINI_API_KEY, GEMINI_MODEL
from app.gemini_service import analyze_chunk, degraded_response, now_ts
from app.schemas import (
    AlertRequest, AlertResponse,
    AnalyzeRequest, AnalyzeResponse,
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

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Suraksha AI",
        "model": GEMINI_MODEL,
        "has_gemini_key": bool(GEMINI_API_KEY),
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
def text_to_speech(req: TTSRequest):
    """
    Generates natural, human-sounding speech in Gujarati (gu-IN), Hindi (hi-IN), or Indian English.
    Replaces mechanical robotic browser voices with calm, human inflection.
    """
    lang_code = req.language
    if lang_code not in ["gu", "hi", "en"]:
        lang_code = "gu"

    try:
        tts = gTTS(text=req.text, lang=lang_code, tld=req.tld, slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_b64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
        return TTSResponse(audio_b64=audio_b64, mime_type="audio/mp3")
    except Exception as e:
        print(f"Human voice TTS error: {e}")
        return TTSResponse(audio_b64="", mime_type="audio/mp3")
