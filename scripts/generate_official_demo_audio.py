import os
import subprocess
from gtts import gTTS

os.makedirs("frontend/public/demo-calls", exist_ok=True)
os.makedirs("demo-audio", exist_ok=True)

# Exact scripts specified in the official Garbathon prompt:
# 1. Gujarati scam: નમસ્તે, હું મુંબઈ પોલીસ સાયબર સેલમાંથી બોલું છું. તમારા આધાર નંબર પર મોકલેલા પાર્સલમાં ડ્રગ્સ મળ્યા છે. તમે ડિજિટલ અરેસ્ટમાં છો, ફોન કાપશો નહીં. કેસ બંધ કરવા માટે અત્યારે જ ₹50,000 ટ્રાન્સફર કરો.
# 2. Hindi scam: नमस्ते, मैं मुंबई पुलिस साइबर सेल से बोल रहा हूँ। आपके आधार नंबर से भेजे गए पार्सल में ड्रग्स मिले हैं। आप डिजिटल अरेस्ट में हैं, कॉल मत काटिए। केस बंद करने के लिए अभी ₹50,000 ट्रांसफर कीजिए।
# 3. English scam: Hello, this is your bank's KYC team. Your account will be blocked today because your KYC has expired. To keep it active, please share the OTP we just sent to your phone.
# 4. English genuine: Hi, this is the delivery partner from Swiggy. I'm outside your building with your order. Which gate should I come to?

official_calls = {
    "recording_gujarati_scam": {
        "text": "નમસ્તે, હું મુંબઈ પોલીસ સાયબર સેલમાંથી બોલું છું. તમારા આધાર નંબર પર મોકલેલા પાર્સલમાં ડ્રગ્સ મળ્યા છે. તમે ડિજિટલ અરેસ્ટમાં છો, ફોન કાપશો નહીં. કેસ બંધ કરવા માટે અત્યારે જ પચાસ હજાર રૂપિયા ટ્રાન્સફર કરો.",
        "lang": "gu",
        "tld": "co.in"
    },
    "recording_hindi_scam": {
        "text": "नमस्ते, मैं मुंबई पुलिस साइबर सेल से बोल रहा हूँ। आपके आधार नंबर से भेजे गए पार्सल में ड्रग्स मिले हैं। आप डिजिटल अरेस्ट में हैं, कॉल मत काटिए। केस बंद करने के लिए अभी पचास हजार रुपये ट्रांसफर कीजिए।",
        "lang": "hi",
        "tld": "co.in"
    },
    "recording_english_scam": {
        "text": "Hello, this is your bank's KYC team. Your account will be blocked today because your KYC has expired. To keep it active, please share the OTP we just sent to your phone.",
        "lang": "en",
        "tld": "co.in"
    },
    "recording_english_genuine": {
        "text": "Hi, this is the delivery partner from Swiggy. I am outside your building with your order. Which gate should I come to?",
        "lang": "en",
        "tld": "co.in"
    }
}

for name, item in official_calls.items():
    mp3_path = f"/tmp/{name}.mp3"
    wav_public = f"frontend/public/demo-calls/{name}.wav"
    wav_demo = f"demo-audio/{name}.wav"

    print(f"Generating TTS for {name} ({item['lang']})...")
    tts = gTTS(text=item["text"], lang=item["lang"], tld=item.get("tld", "com"), slow=False)
    tts.save(mp3_path)

    # Standard 16kHz Mono 16-bit PCM WAV for Gemini
    subprocess.run([
        "ffmpeg", "-y", "-i", mp3_path,
        "-ac", "1", "-ar", "16000",
        wav_public
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run(["cp", wav_public, wav_demo], check=True)
    print(f"Generated & saved: {wav_public}")

print("All official hackathon demo WAV files successfully generated!")
