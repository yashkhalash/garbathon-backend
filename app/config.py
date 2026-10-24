import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# Render deploy: append the Vercel domain via env so it never needs a code change.
_extra_origin = os.environ.get("FRONTEND_ORIGIN")
if _extra_origin:
    ALLOWED_ORIGINS.append(_extra_origin)
