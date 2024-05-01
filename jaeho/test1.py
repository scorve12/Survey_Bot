import pandas as pd
from gtts import gTTS
import os
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import whisper
import tempfile


def read_csv_and_speak(file_path, output_dir):
    # CSV 파일을 읽어옵니다.
    df = pd.read_csv(file_path)
    
    # 출력 디렉토리가 존재하지 않으면 생성합니다.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # '질문' 열의 각 항목에 대해 TTS를 사용하여 읽어줍니다.
    for index, row in df.iterrows():
        text = str(row['질문'])
        tts = gTTS(text=text, lang='ko')
        filename = f"question_{index+1}.mp3"
        filepath = os.path.join(output_dir, filename)  # 파일 경로
        tts.save(filepath)  # 음성 파일 저장
        print(f"Saved: {filepath}")
        
def record_csv_and_speak():
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

# CSV 파일 경로
file_path = 'CSV\대인관계 패턴의 자기이해 척도.csv'

# 사용자가 지정한 음성 파일을 저장할 경로
output_directory = 'CSV\대인관계음성'

# 함수 실행
read_csv_and_speak(file_path, output_directory)