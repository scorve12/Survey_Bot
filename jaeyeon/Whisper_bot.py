import pygame
import glob
import time
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import whisper
import tempfile
import warnings
import os


# pygame 라이브러리 초기화
pygame.init()
pygame.mixer.init()

# 음성 파일이 저장된 폴더 경로와 패턴
audio_files_pattern = r'D:\Project\Survey_Bot\audio\*.mp3'

# glob을 사용하여 폴더 내의 모든 mp3 파일 목록을 가져옵니다.
audio_files = glob.glob(audio_files_pattern)

sample_rate = 44100  # 녹음 샘플링 비율
duration = 5  # 녹음할 시간(초)
respronse=[]

# 모든 음성 파일을 순차적으로 재생
for audio_file in audio_files[:3]:
    #print(f"Playing {audio_file}...")
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    # 재생이 완료될 때까지 대기
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    #print(f"Finished playing {audio_file}.")
    
    print("녹음을 시작합니다. 말씀해주세요...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2)
    sd.wait()  # 녹음이 끝날 때까지 대기
    print("녹음이 완료되었습니다.")

    # 임시 파일로 녹음된 오디오 저장
    temp_dir = tempfile.mkdtemp()
    audio_file = os.path.join(temp_dir, "recording.wav")
    write(audio_file, sample_rate, recording)  # 녹음된 오디오를 WAV 파일로 저장

    # Whisper 모델 로드 및 오디오 파일 변환
    model = whisper.load_model("medium")

    #cpu사용자경우 경고 메세지 삭제
    warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

    result = model.transcribe(audio_file, fp16=False)


    # 결과 출력 및 임시 파일 정리
    respronse.append(result["text"])
    print("인식된 텍스트:", result["text"])
    os.remove(audio_file)  # 임시 오디오 파일 삭제
    os.rmdir(temp_dir)  # 임시 디렉토리 삭제
    


# pygame 종료
pygame.quit()
