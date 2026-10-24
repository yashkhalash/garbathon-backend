from typing import Literal
from pydantic import BaseModel, Field

ScamCategory = Literal[
    "DIGITAL_ARREST",
    "OTP_FRAUD",
    "BANK_KYC_FRAUD",
    "COURIER_FRAUD",
    "PAYMENT_FRAUD",
    "AUTHORITY_IMPERSONATION",
    "SOCIAL_ENGINEERING",
    "BENIGN_OR_UNCLEAR",
]

SeverityLevel = Literal["low", "medium", "high", "critical"]
RiskLevel = Literal["safe", "low", "suspicious", "high", "critical"]

class RedFlagItem(BaseModel):
    category: ScamCategory
    evidence: str
    timestamp_seconds: float = 0.0
    severity: SeverityLevel = "high"
    reason: str
    recommended_action: str

class AnalyzeRequest(BaseModel):
    audio_b64: str
    mime_type: str = "audio/wav"
    context_summary: str = ""
    elapsed_sec: float = 0.0
    language: str = "gu"

class AnalyzeTextRequest(BaseModel):
    text: str
    language: str = "gu"

class AnalyzeResponse(BaseModel):
    language: str
    risk_level: RiskLevel
    risk_score: int = Field(ge=0, le=100)
    summary: str
    red_flags: list[RedFlagItem] = []
    warning_text: str
    recommended_actions: list[str] = []
    should_warn: bool
    context_summary: str = ""
    scam_type: str = "none"
    degraded: bool = False

class AlertRequest(BaseModel):
    call_id: str
    risk: int
    scam_type: str
    contact_name: str = "family"

class AlertResponse(BaseModel):
    message: str
    logged_at: float

class TTSRequest(BaseModel):
    text: str
    language: str = "gu" # gu, hi, en
    tld: str = "co.in"

class TTSResponse(BaseModel):
    audio_b64: str
    mime_type: str = "audio/mp3"

class GeminiModelInfo(BaseModel):
    id: str
    name: str
    description: str
    is_recommended: bool = False

class GeminiSettingsResponse(BaseModel):
    model: str
    has_active_key: bool
    has_custom_key: bool
    masked_key: str
    status: Literal["active", "invalid", "rate_limited", "not_configured"]
    status_message: str
    latency_ms: float | None = None
    supported_models: list[GeminiModelInfo]

class UpdateGeminiSettingsRequest(BaseModel):
    api_key: str | None = None
    model: str | None = None

class TestGeminiKeyRequest(BaseModel):
    api_key: str | None = None
    model: str | None = None

class TestGeminiKeyResponse(BaseModel):
    is_active: bool
    status: Literal["active", "invalid", "rate_limited", "not_configured", "error"]
    status_message: str
    latency_ms: float | None = None
    model: str
