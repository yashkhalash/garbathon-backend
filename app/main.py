import asyncio
import base64
import io
import tempfile
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

from app.config import ALLOWED_ORIGINS
from app.gemini_service import (
    analyze_chunk,
    analyze_text_call,
    degraded_response,
    get_effective_api_key,
    get_effective_model,
    get_gemini_settings_status,
    now_ts,
    set_runtime_gemini_key,
    set_runtime_gemini_model,
    test_gemini_connection,
)
from app.schemas import (
    AlertRequest, AlertResponse,
    AnalyzeRequest, AnalyzeResponse, AnalyzeTextRequest,
    GeminiSettingsResponse, TestGeminiKeyRequest, TestGeminiKeyResponse,
    TTSRequest, TTSResponse, UpdateGeminiSettingsRequest,
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
        "model": get_effective_model(),
        "has_gemini_key": bool(get_effective_api_key()),
        "natural_voice_engine": "edge-tts-neural" if edge_tts is not None else "gtts-neural",
    }

@app.get("/api/settings/gemini", response_model=GeminiSettingsResponse)
def get_gemini_settings():
    """Returns current active model, key status, and supported models."""
    return get_gemini_settings_status()

@app.post("/api/settings/gemini", response_model=GeminiSettingsResponse)
def update_gemini_settings(req: UpdateGeminiSettingsRequest):
    """
    Updates Gemini model and/or custom API key.
    Tests the key and saves it if valid or updates model selection.
    """
    if req.model:
        set_runtime_gemini_model(req.model)

    if req.api_key is not None:
        clean_key = req.api_key.strip()
        if clean_key:
            # Test key before setting
            is_active, status, msg, latency = test_gemini_connection(
                api_key=clean_key,
                model=req.model or get_effective_model(),
            )
            # Persist key in runtime
            set_runtime_gemini_key(clean_key)
            resp = get_gemini_settings_status()
            resp["status"] = status
            resp["status_message"] = msg
            resp["latency_ms"] = latency
            return resp
        else:
            set_runtime_gemini_key(None)

    return get_gemini_settings_status()

@app.delete("/api/settings/gemini", response_model=GeminiSettingsResponse)
def delete_gemini_key():
    """
    Deletes custom Gemini API key and reverts to server environment or demo mode.
    """
    set_runtime_gemini_key(None)
    status_info = get_gemini_settings_status()
    status_info["status_message"] = "Custom API Key removed. Reset to system default or demo benchmark mode."
    return status_info

@app.post("/api/settings/gemini/test", response_model=TestGeminiKeyResponse)
def test_gemini_key_endpoint(req: TestGeminiKeyRequest):
    """
    Actively tests an API key against Google Gemini API,
    measuring latency and verifying if quota limits have been reached.
    """
    target_model = req.model or get_effective_model()
    is_active, status, msg, latency = test_gemini_connection(
        api_key=req.api_key,
        model=target_model,
    )
    return TestGeminiKeyResponse(
        is_active=is_active,
        status=status,
        status_message=msg,
        latency_ms=latency,
        model=target_model,
    )

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

    if edge_tts is not None:
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

    if gTTS is not None:
        try:
            tts = gTTS(text=req.text, lang=lang_code, tld=req.tld, slow=False)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_b64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
            return TTSResponse(audio_b64=audio_b64, mime_type="audio/mp3")
        except Exception as e2:
            print(f"Fallback gTTS error: {e2}")

    return TTSResponse(audio_b64="", mime_type="audio/mp3")
