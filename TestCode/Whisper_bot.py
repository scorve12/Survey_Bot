import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import whisper
import tempfile
import os

# 녹음 설정
sample_rate = 44100  # 녹음 샘플링 비율
duration = 5  # 녹음할 시간(초)

print("녹음을 시작합니다. 말씀해주세요...")
recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2)
sd.wait()  # 녹음이 끝날 때까지 대기
print("녹음이 완료되었습니다.")

# 임시 파일로 녹음된 오디오 저장
temp_dir = tempfile.mkdtemp()
audio_file = os.path.join(temp_dir, "recording.wav")
write(audio_file, sample_rate, recording)  # 녹음된 오디오를 WAV 파일로 저장

# Whisper 모델 로드 및 오디오 파일 변환
model = whisper.load_model("base")
result = model.transcribe(audio_file)

# 결과 출력 및 임시 파일 정리
print("인식된 텍스트:", result["text"])
os.remove(audio_file)  # 임시 오디오 파일 삭제
os.rmdir(temp_dir)  # 임시 디렉토리 삭제
