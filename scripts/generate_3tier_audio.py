import os
import subprocess
from gtts import gTTS

os.makedirs("frontend/public/demo-calls", exist_ok=True)
os.makedirs("demo-audio", exist_ok=True)

tier_calls = {
    # 1. DEFINITE SPAM / HIGH-RISK SCAM (Critical Risk, >85 score)
    "tier1_definite_spam_digital_arrest": {
        "text": "નમસ્તે, હું મુંબઈ પોલીસ સાયબર સેલમાંથી બોલું છું. તમારા આધાર નંબર પર મોકલેલા પાર્સલમાં ડ્રગ્સ મળ્યા છે. તમે ડિજિટલ અરેસ્ટમાં છો, ફોન કાપશો નહીં. કેસ બંધ કરવા માટે અત્યારે જ ₹50,000 ટ્રાન્સફર કરો.",
        "lang": "gu",
        "label": "Definite Scam (પૂર્ણ છેતરપિંડી / Definite Spam)",
        "category": "DIGITAL_ARREST"
    },
    
    # 2. PARTIALLY SPAM / SUSPICIOUS TELEMARKETING OR UNSOLICITED CREDIT (Amber Risk, 30-60 score)
    # Unsolicited pre-approved personal loan agent pushing for immediate processing and asking for PAN & DOB details
    "tier2_partially_spam_loan_push": {
        "text": "Hello sir, good afternoon! I am calling from Bajaj Finance Quick Loan department. You have a pre-approved personal loan of five lakh rupees available right now with zero interest for the first month. This offer expires today at five PM. Please confirm your PAN card number and date of birth so I can process your application immediately.",
        "lang": "en",
        "label": "Partially Spam / Suspicious Push (શંકાસ્પદ / Partially Spam)",
        "category": "SOCIAL_ENGINEERING"
    },
    
    # 3. NO SPAM / GENUINE CONVERSATION (Safe, <15 score)
    # Legitimate food / parcel delivery partner with polite location inquiry
    "tier3_no_spam_swiggy_delivery": {
        "text": "Hi, this is the delivery partner from Swiggy. I am outside your building with your order. Which gate should I come to?",
        "lang": "en",
        "label": "No Spam / Genuine Call (સામાન્ય કોલ / No Spam)",
        "category": "BENIGN_OR_UNCLEAR"
    }
}

for name, item in tier_calls.items():
    mp3_path = f"/tmp/{name}.mp3"
    wav_public = f"frontend/public/demo-calls/{name}.wav"
    wav_demo = f"demo-audio/{name}.wav"

    print(f"Generating audio for {name} ({item['lang']})...")
    tts = gTTS(text=item["text"], lang=item["lang"], tld="co.in", slow=False)
    tts.save(mp3_path)

    # Convert to 16kHz Mono 16-bit PCM WAV (Standard for Gemini Speech and Web Audio)
    subprocess.run([
        "ffmpeg", "-y", "-i", mp3_path,
        "-ac", "1", "-ar", "16000",
        wav_public
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run(["cp", wav_public, wav_demo], check=True)
    print(f"Generated & saved: {wav_public}")

print("All 3-tier demo WAV files generated successfully!")
