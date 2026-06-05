import wave
import struct
import math
import os

def generate_alarm(path: str, frequency: int = 880, duration: float = 1.0, sample_rate: int = 44100):
    n_samples = int(sample_rate * duration)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for i in range(n_samples):
            v = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            f.writeframes(struct.pack("<h", v))

if __name__ == "__main__":
    generate_alarm("assets/alarm.wav")
    print("Generated assets/alarm.wav")
