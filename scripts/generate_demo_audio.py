import os
import subprocess
from gtts import gTTS

os.makedirs("frontend/public/demo-calls", exist_ok=True)
os.makedirs("demo-audio", exist_ok=True)

scripts = {
    "recording_a_digital_arrest": {
        "text": "This is Inspector Vijay Kumar calling from Delhi Police Cyber Crime Branch. Your Aadhaar number and phone number are directly linked to a high level money laundering and narcotics criminal case. Non-bailable arrest warrant has been issued against you. Do not disconnect this call. You are under immediate digital arrest. Do not tell your family or contact anyone. Transfer fifty thousand rupees verification security deposit immediately to clear your name or our team will reach your residence in twenty minutes.",
        "lang": "en",
        "tld": "co.in"
    },
    "recording_b_fake_kyc": {
        "text": "Hello, I am calling from State Bank Customer Support Verification Desk. As per new RBI guidelines, your bank account and debit card will be permanently blocked today within one hour. To prevent immediate account suspension, you have received a six-digit verification OTP on your mobile. Read out that OTP to me right now so I can update your KYC immediately.",
        "lang": "en",
        "tld": "co.in"
    },
    "recording_c_fake_courier": {
        "text": "Urgent alert from Customs Narcotics Division and International Courier Hub. Your parcel from Mumbai to Taiwan has been seized at airport customs. Inside the parcel we found five expired passports, sixteen credit cards, and two hundred grams of illegal narcotics. A criminal FIR has been registered. You must pay twenty-five thousand rupees customs clearance penalty now, or local police will arrest you within two hours.",
        "lang": "en",
        "tld": "co.in"
    },
    "recording_d_genuine_call": {
        "text": "Hello sir, good afternoon. I am calling from BlueDart Express delivery services regarding your parcel booked yesterday. Your package is scheduled for delivery tomorrow between ten AM and two PM. You do not need to pay anything, and never share any confidential OTP or PIN with any delivery executive. You can track your shipment status on our official website anytime. Thank you and have a nice day.",
        "lang": "en",
        "tld": "co.in"
    }
}

for name, item in scripts.items():
    mp3_path = f"/tmp/{name}.mp3"
    wav_public = f"frontend/public/demo-calls/{name}.wav"
    wav_demo = f"demo-audio/{name}.wav"
    
    print(f"Generating TTS for {name}...")
    tts = gTTS(text=item["text"], lang=item["lang"], tld=item["tld"], slow=False)
    tts.save(mp3_path)
    
    # Convert to 16kHz Mono 16-bit PCM WAV (Standard for Gemini Speech and Web Audio)
    subprocess.run([
        "ffmpeg", "-y", "-i", mp3_path,
        "-ac", "1", "-ar", "16000",
        wav_public
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Also copy to demo-audio
    subprocess.run(["cp", wav_public, wav_demo], check=True)
    print(f"Saved: {wav_public}")

print("All 4 demo WAV files successfully generated!")
