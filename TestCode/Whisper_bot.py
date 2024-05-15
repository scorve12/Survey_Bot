import pygame
import glob
import time
import sounddevice as sd

import pandas as pd
from scipy.io.wavfile import write
import whisper
import tempfile
import warnings
import os
from transformers import pipeline

classifier = pipeline("text-classification", model="matthewburke/korean_sentiment")

# pygame 라이브러리 초기화
pygame.init()
pygame.mixer.init()

# 음성 파일이 저장된 폴더 경로와 패턴
audio_files_pattern = r'audio\*.mp3'

# glob을 사용하여 폴더 내의 모든 mp3 파일 목록을 가져옵니다.
audio_files = glob.glob(audio_files_pattern)

sample_rate = 44100  # 녹음 샘플링 비율
duration = 5  # 녹음할 시간(초)
response_text=[]

# 모든 음성 파일을 순차적으로 재생
for audio_file in audio_files[:1]:
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    # 재생이 완료될 때까지 대기
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
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
    response_text.append(result["text"])
    print("인식된 텍스트:", result["text"])
    os.remove(audio_file)  # 임시 오디오 파일 삭제
    os.rmdir(temp_dir)  # 임시 디렉토리 삭제

pred_respronse=[]
for r in response_text:
    print(r)
    preds =classifier(r, return_all_scores=True) # top_k=None
    print(preds)
    #is_positive = preds[0][1]['score'] > 0.5
    #TODO top
    #is_positive = next((item for item in preds[0] if item['label'] == 'LABEL_1'), None)['score'] > 0.5
    
    pred_respronse.append(is_positive)
    
response=[1 if x else 0 for x in pred_respronse]

print(response)
print(pred_respronse)

data=pd.read_csv('CSV/sample_survey_answer.csv')
data['답변']=response

data.to_csv('User_result/sample_test.csv', index=False)

pygame.quit()
