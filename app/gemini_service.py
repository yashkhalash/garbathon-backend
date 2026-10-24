import json
import time

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.schemas import AnalyzeResponse, RedFlagItem

_client: genai.Client | None = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

SYSTEM_PROMPT = """You are Suraksha AI — an expert real-time scam call detection and voice safety assistant designed to protect citizens (especially senior citizens in India) from fraudulent phone calls.

Analyze the provided audio chunk in the context of the call so far.
Evaluate combinations of red flags, threats, coercion, isolation, and urgency.
CRITICAL: Do NOT classify every caller mentioning police, a bank, or a courier as a scammer. Analyze context:
- Genuine calls (e.g. routine courier updates or general bank notices that DO NOT ask for OTP, passwords, or immediate coerced transfers) are BENIGN_OR_UNCLEAR with low risk.
- High risk requires evidence of coercion, threats of arrest (digital arrest), OTP/password demands, fake KYC deadlines, or coercive payment transfers.

Output MUST conform strictly to the JSON schema.
Warning text must be clear, calm, and written in the requested user language (Gujarati 'gu', Hindi 'hi', or English 'en').
"""

RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    required=[
        "language",
        "risk_level",
        "risk_score",
        "summary",
        "red_flags",
        "warning_text",
        "recommended_actions",
        "should_warn",
        "context_summary",
        "scam_type",
    ],
    properties={
        "language": types.Schema(type=types.Type.STRING),
        "risk_level": types.Schema(
            type=types.Type.STRING,
            enum=["safe", "low", "suspicious", "high", "critical"],
        ),
        "risk_score": types.Schema(type=types.Type.INTEGER),
        "summary": types.Schema(type=types.Type.STRING),
        "red_flags": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                required=["category", "evidence", "timestamp_seconds", "severity", "reason", "recommended_action"],
                properties={
                    "category": types.Schema(
                        type=types.Type.STRING,
                        enum=[
                            "DIGITAL_ARREST",
                            "OTP_FRAUD",
                            "BANK_KYC_FRAUD",
                            "COURIER_FRAUD",
                            "PAYMENT_FRAUD",
                            "AUTHORITY_IMPERSONATION",
                            "SOCIAL_ENGINEERING",
                            "BENIGN_OR_UNCLEAR",
                        ],
                    ),
                    "evidence": types.Schema(type=types.Type.STRING),
                    "timestamp_seconds": types.Schema(type=types.Type.NUMBER),
                    "severity": types.Schema(
                        type=types.Type.STRING,
                        enum=["low", "medium", "high", "critical"],
                    ),
                    "reason": types.Schema(type=types.Type.STRING),
                    "recommended_action": types.Schema(type=types.Type.STRING),
                },
            ),
        ),
        "warning_text": types.Schema(type=types.Type.STRING),
        "recommended_actions": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
        ),
        "should_warn": types.Schema(type=types.Type.BOOLEAN),
        "context_summary": types.Schema(type=types.Type.STRING),
        "scam_type": types.Schema(type=types.Type.STRING),
    },
)

FALLBACK_WARNINGS = {
    "gu": "સાવધાન! આ કોલમાં છેતરપિંડીનાં સંકેતો છે. તમારો OTP કે પૈસા શેર કરશો નહીં.",
    "hi": "सावधान! इस कॉल में धोखाधड़ी के संकेत हैं। अपना OTP या पैसा साझा न करें।",
    "en": "Warning: This call contains suspicious indicators. Do not share OTP or transfer money.",
}

def degraded_response(context_summary: str, lang: str = "gu") -> AnalyzeResponse:
    """Safe fallback if Gemini credentials or quota are missing, or network fails."""
    warning = FALLBACK_WARNINGS.get(lang, FALLBACK_WARNINGS["gu"])
    return AnalyzeResponse(
        language=lang,
        risk_level="safe",
        risk_score=0,
        summary="Analysis paused or offline. Verifying caller credentials independently is always advised.",
        red_flags=[],
        warning_text=warning,
        recommended_actions=[
            "Do not share OTP or sensitive passwords.",
            "Verify the caller through official toll-free numbers."
        ],
        should_warn=False,
        context_summary=context_summary,
        scam_type="none",
        degraded=True,
    )

def analyze_chunk(
    audio_bytes: bytes,
    mime_type: str,
    context_summary: str,
    elapsed_sec: float,
    lang: str = "gu",
) -> AnalyzeResponse:
    if not GEMINI_API_KEY:
        return degraded_response(context_summary, lang)

    prompt_text = (
        f"Audio chunk timestamp offset: {elapsed_sec:.1f}s\n"
        f"Preferred warning language: {lang}\n"
        f"Running conversation context so far: {context_summary or '(Call start)'}\n"
        "Listen to the speech in this audio chunk. Extract spoken evidence, determine fraud risk, "
        "and return the structured JSON assessment with warning_text in the requested language."
    )

    try:
        client = _get_client()
        result = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                        types.Part.from_text(text=prompt_text),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                temperature=0.1,
            ),
        )
        data = json.loads(result.text)
    except Exception as e:
        print(f"Gemini API analysis failed: {e}")
        return degraded_response(context_summary, lang)

    try:
        red_flags = [
            RedFlagItem(
                category=f["category"],
                evidence=f["evidence"],
                timestamp_seconds=float(f.get("timestamp_seconds", elapsed_sec)),
                severity=f.get("severity", "high"),
                reason=f.get("reason", "Suspicious scam behavior detected."),
                recommended_action=f.get("recommended_action", "Hang up and do not share sensitive information."),
            )
            for f in data.get("red_flags", [])
        ]

        return AnalyzeResponse(
            language=data.get("language", lang),
            risk_level=data.get("risk_level", "safe"),
            risk_score=int(data.get("risk_score", 0)),
            summary=data.get("summary", ""),
            red_flags=red_flags,
            warning_text=data.get("warning_text", FALLBACK_WARNINGS.get(lang, "")),
            recommended_actions=data.get("recommended_actions", []),
            should_warn=bool(data.get("should_warn", False)),
            context_summary=data.get("context_summary", context_summary),
            scam_type=data.get("scam_type", "none"),
            degraded=False,
        )
    except Exception as e:
        print(f"Error parsing Gemini response JSON: {e}")
        return degraded_response(context_summary, lang)

def now_ts() -> float:
    return time.time()
