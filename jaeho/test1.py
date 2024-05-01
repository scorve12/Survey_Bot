import pandas as pd
from gtts import gTTS
import os

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

# CSV 파일 경로
file_path = 'CSV\대인관계 패턴의 자기이해 척도.csv'

# 사용자가 지정한 음성 파일을 저장할 경로
output_directory = 'CSV\대인관계음성'

# 함수 실행
read_csv_and_speak(file_path, output_directory)