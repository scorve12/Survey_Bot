import os
import pandas as pd
from openai import OpenAI

# 환경 변수에서 API 키 불러오기
#TODO: key 수정 요청
client = OpenAI.api_key = (os.getenv("OPENAI_API_KEY"))

# 음성 파일 경로와 파일 이름 설정
audio_file_base_path = "tts_audio"

# 설문 데이터프레임 로드 (예시: CSV 파일로부터)
survey = pd.read_csv(r".\CSV\대인관계 패턴의 자기이해 척도.csv", index_col=False)

# 음성 파일 생성
for idx, q in enumerate(survey['질문'].to_list()):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            input=q,
            voice="alloy",
            response_format="mp3",
            speed=1.1,
        )
        # 각 음성 파일을 별도의 파일로 저장
        audio_file_path = f"{audio_file_base_path}_{idx}.mp3"
        with open(audio_file_path, "wb") as f:
            f.write(response.content)
        print(f"Saved audio file for question {idx} at {audio_file_path}")
    except Exception as e:
        print(f"Failed to create speech for question {idx}: {e}")
