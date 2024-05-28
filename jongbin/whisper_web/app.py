from flask import Flask, jsonify, render_template, request
import glob
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import tempfile
import warnings
import os
from transformers import pipeline
from configparser import ConfigParser
import logging
import pandas as pd
import pygame

app = Flask(__name__)

# 설정 파일 로드
config = ConfigParser()
config.read('config.ini', encoding='utf-8')

# pygame 라이브러리 초기화
pygame.init()
pygame.mixer.init()

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 설정 변수
#CSV_FILE = config.get('paths', 'csv_file')
OUTPUT_DIR = config.get('paths', 'output_dir')
RESULT_FILE = config.get('paths', 'result_file')
TEXTS_FILE = config.get('paths', 'texts_file')
DURATION = config.getint('audio', 'duration')
SAMPLE_RATE = config.getint('audio', 'sample_rate')
WHISPER_MODEL = config.get('models', 'whisper_model')
SENTIMENT_MODEL = config.get('models', 'sentiment_model')

# 감정 분석 모델 초기화
classifier = pipeline("text-classification", model=SENTIMENT_MODEL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['GET'])
def process_files():
    # 음성 파일이 저장된 폴더 경로와 패턴
    audio_files_pattern = os.path.join(OUTPUT_DIR, '*.mp3')

    # glob을 사용하여 폴더 내의 모든 mp3 파일 목록을 가져옵니다.
    audio_files = glob.glob(audio_files_pattern)
    
    # CSV 파일에서 텍스트를 읽어옵니다.
    texts_df = pd.read_csv(TEXTS_FILE)
    texts = texts_df['text'].tolist()
    
    if len(audio_files) != len(texts):
        return jsonify({'error': '음성 파일의 수와 텍스트의 수가 일치하지 않습니다.'}), 400
    
    response_texts = []
    all_results = []

    # 모든 음성 파일을 순차적으로 재생
    for i, audio_file in enumerate(audio_files):
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()

        # 재생이 완료될 때까지 대기
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # 현재 텍스트를 프론트엔드에 보내기
        current_text = texts[i]

        print("녹음을 시작합니다. 말씀해주세요...")
        recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=2)
        sd.wait()  # 녹음이 끝날 때까지 대기
        print("녹음이 완료되었습니다.")

        # 임시 파일로 녹음된 오디오 저장
        temp_dir = tempfile.mkdtemp()
        temp_audio_file = os.path.join(temp_dir, "recording.wav")
        write(temp_audio_file, SAMPLE_RATE, recording)  # 녹음된 오디오를 WAV 파일로 저장

        # Whisper 모델 로드 및 오디오 파일 변환
        model = whisper.load_model(WHISPER_MODEL)
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
        result = model.transcribe(temp_audio_file, fp16=False)

        # 결과 출력 및 임시 파일 정리
        response_text = result["text"]
        response_texts.append(response_text)
        os.remove(temp_audio_file)  # 임시 오디오 파일 삭제
        os.rmdir(temp_dir)  # 임시 디렉토리 삭제

        # 감정 분석
        preds = classifier(response_text, top_k=None)
        is_positive = preds[0]['score'] > 0.5
        sentiment = 'positive' if is_positive else 'negative'

        all_results.append({
            'audio_file': audio_file,
            'display_text': current_text,
            'response_text': response_text,
            'sentiment': sentiment
        })

    # Save responses to CSV
    response_df = pd.DataFrame(all_results)
    response_df.to_csv(RESULT_FILE, index=False)
    
    logger.info(f"결과가 {RESULT_FILE}에 저장되었습니다.")
    
    return jsonify(all_results)

if __name__ == '__main__':
    app.run(debug=True)
