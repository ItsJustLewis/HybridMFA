import serial
import wave
import time
import struct
import whisper
import firebase_admin
from firebase_admin import credentials, db

# ---------- ESP32 / Serial Settings ----------
COM_PORT = "COM5"
BAUD_RATE = 921600

# ---------- Audio Settings ----------
SAMPLE_RATE = 8000
RECORD_SECONDS = 3
OUTPUT_FILE = "recording.wav"

TOTAL_SAMPLES = SAMPLE_RATE * RECORD_SECONDS
TOTAL_BYTES = TOTAL_SAMPLES * 4

# ---------- Firebase Settings ----------
SERVICE_ACCOUNT_FILE = "hybridmfa-firebase-adminsdk-fbsvc-c4bad1c186.json"
DATABASE_URL = "https://hybridmfa-default-rtdb.europe-west1.firebasedatabase.app/"

# ---------- Whisper Settings ----------
WHISPER_MODEL = "base"


def connect_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred, {
            "databaseURL": DATABASE_URL
        })


def record_audio():
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=5)
    time.sleep(2)

    print("Connected to ESP32.")
    print("Starting voice recording...")

    ser.write(b"start\n")

    while True:
        line = ser.readline()
        if b"START_AUDIO" in line:
            print("Audio started. Say your name...")
            break

    raw_data = ser.read(TOTAL_BYTES)

    samples_16bit = bytearray()

    for i in range(0, len(raw_data), 4):
        if i + 4 <= len(raw_data):
            sample32 = struct.unpack("<i", raw_data[i:i + 4])[0]

            sample16 = sample32 >> 16

            if sample16 > 32767:
                sample16 = 32767
            elif sample16 < -32768:
                sample16 = -32768

            samples_16bit += struct.pack("<h", sample16)

    with wave.open(OUTPUT_FILE, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(samples_16bit)

    print(f"Saved audio as {OUTPUT_FILE}")
    print(f"Bytes received: {len(raw_data)}")
    print(f"Expected bytes: {TOTAL_BYTES}")

    ser.close()


def transcribe_audio():
    print("Loading Whisper model...")
    model = whisper.load_model(WHISPER_MODEL)

    print("Transcribing name...")
    result = model.transcribe(OUTPUT_FILE, language="English")

    transcription = result["text"].strip().lower()
    transcription = transcription.replace(".", "").replace(",", "")

    print(f"Recognised speech: {transcription}")

    return transcription


def find_user_from_transcription(transcription):
    users_ref = db.reference("/users")
    users = users_ref.get()

    if not users:
        print("No users found in Firebase.")
        return None, None

    for username, user_data in users.items():
        if username.lower() in transcription:
            return username, user_data

    return None, None


def check_pin(user_data):
    entered_pin = input("Enter PIN: ")

    stored_pin = str(user_data.get("pin"))

    if entered_pin == stored_pin:
        return True

    return False


def main():
    connect_firebase()

    record_audio()

    transcription = transcribe_audio()

    username, user_data = find_user_from_transcription(transcription)

    if username is None:
        print("UNKNOWN USER")
        print("ACCESS DENIED")
        return

    print(f"User identified: {username}")

    if not user_data.get("enabled", False):
        print("User account disabled.")
        print("ACCESS DENIED")
        return

    pin_correct = check_pin(user_data)

    if pin_correct:
        print("PIN correct.")
        print("ACCESS GRANTED")
    else:
        print("PIN incorrect.")
        print("ACCESS DENIED")


if __name__ == "__main__":
    main()
