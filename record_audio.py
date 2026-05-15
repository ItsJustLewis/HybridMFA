import serial
import wave
import time
import struct

COM_PORT = "COM5"
BAUD_RATE = 921600
SAMPLE_RATE = 8000
RECORD_SECONDS = 3
OUTPUT_FILE = "recording.wav"

TOTAL_SAMPLES = SAMPLE_RATE * RECORD_SECONDS
TOTAL_BYTES = TOTAL_SAMPLES * 4  # 32-bit audio from ESP32

ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=5)
time.sleep(2)

print("Connected to ESP32.")
print("Starting recording...")

ser.write(b"start\n")

while True:
    line = ser.readline()
    if b"START_AUDIO" in line:
        print("Audio started.")
        break

raw_data = ser.read(TOTAL_BYTES)

samples_16bit = bytearray()

for i in range(0, len(raw_data), 4):
    if i + 4 <= len(raw_data):
        sample32 = struct.unpack("<i", raw_data[i:i+4])[0]

        # INMP441 is usually 24-bit audio inside a 32-bit value
        sample16 = sample32 >> 16

        # Clamp to 16-bit range
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
