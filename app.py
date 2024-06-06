from flask import Flask, jsonify, render_template, request, redirect, url_for
import glob
import os
import pandas as pd
import logging
from configparser import ConfigParser
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import tempfile
import warnings
from transformers import pipeline
import re

app = Flask(__name__)

# 설정 파일 로드
config = ConfigParser()
config.read('config.ini', encoding='utf-8')

# BASE_DIR 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 로그 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 설정 변수
OUTPUT_DIR = os.path.join(BASE_DIR, config.get('paths', 'output_dir').replace('/', os.sep))
RESULT_FILE = os.path.join(BASE_DIR, config.get('paths', 'result_file').replace('/', os.sep))
TEXTS_FILE = os.path.join(BASE_DIR, config.get('paths', 'texts_file').replace('/', os.sep))
DURATION = config.getint('audio', 'duration')
SAMPLE_RATE = config.getint('audio', 'sample_rate')
WHISPER_MODEL = config.get('models', 'whisper_model')
SENTIMENT_MODEL = config.get('models', 'sentiment_model')

# 감정 분석 모델 초기화
classifier = pipeline("text-classification", model=SENTIMENT_MODEL)

def transcribe_with_progress(model, audio_path):
    import time

    start_time = time.time()
    result = model.transcribe(audio_path, fp16=False)
    end_time = time.time()

    response_text = result["text"]
    elapsed_time = end_time - start_time

    logger.debug(f'Transcription completed in {elapsed_time:.2f} seconds.')
    logger.debug(f'Transcribed text length: {len(response_text)} characters.')

    return response_text

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/survey')
def survey():
    return render_template('survey.html')

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/get_config', methods=['GET'])
def get_config():
    try:
        config_data = {
            'DURATION': DURATION,
            'SAMPLE_RATE': SAMPLE_RATE
        }
        return jsonify(config_data)
    except Exception as e:
        logger.exception("An error occurred while getting config data.")
        return jsonify({'error': str(e)}), 500

@app.route('/get_questions', methods=['GET'])
def get_questions():
    try:
        logger.debug(f'Loading questions from CSV file: {TEXTS_FILE}')
        texts_df = pd.read_csv(TEXTS_FILE)
        texts = texts_df['질문'].tolist()
        
        # "질문X:" 형식을 제거
        clean_texts = [re.sub(r'^질문\d+:\s*', '', text) for text in texts]
        
        logger.debug(f'Loaded {len(clean_texts)} questions')
        
        audio_files_pattern = os.path.join(OUTPUT_DIR, '*.mp3')
        audio_files = sorted(glob.glob(audio_files_pattern))
        audio_files = [os.path.join('static/audio/대인관계음성', os.path.basename(file)) for file in audio_files]
        
        logger.debug(f'Found {len(audio_files)} audio files')

        if len(audio_files) != len(clean_texts):
            logger.error('음성 파일의 수와 텍스트의 수가 일치하지 않습니다.')
            return jsonify({'error': '음성 파일의 수와 텍스트의 수가 일치하지 않습니다.'}), 400
        
        questions = [{'question': question, 'audio': audio} for question, audio in zip(clean_texts, audio_files)]
        return jsonify(questions)
    except Exception as e:
        logger.exception("An error occurred while getting questions.")
        return jsonify({'error': str(e)}), 500

@app.route('/record_response', methods=['POST'])
def record_response():
    try:
        data = request.json
        question_id = data['question_id']
        
        recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=2)
        sd.wait()  # 녹음이 끝날 때까지 대기

        temp_dir = tempfile.mkdtemp()
        temp_audio_file = os.path.join(temp_dir, "recording.wav")
        write(temp_audio_file, SAMPLE_RATE, recording)  # 녹음된 오디오를 WAV 파일로 저장

        model = whisper.load_model(WHISPER_MODEL)
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

        # 여기서 변환 시작
        logger.debug("Starting transcription with Whisper model.")
        response_text = transcribe_with_progress(model, temp_audio_file)
        logger.debug(f'Transcribed text: {response_text}')

        os.remove(temp_audio_file)  # 임시 오디오 파일 삭제
        os.rmdir(temp_dir)  # 임시 디렉토리 삭제

        if not response_text.strip():
            return jsonify({'error': '녹음된 내용이 이해되지 않았습니다. 다시 녹음해주세요.'}), 400

        preds = classifier(response_text, top_k=None)
        score = preds[0]['score']  # 감정 점수

        # 결과를 CSV 파일에 저장
        texts_df = pd.read_csv(TEXTS_FILE)
        current_text = texts_df.iloc[question_id]['질문']

        result_data = {
            'question_id': question_id,
            'question': current_text,
            'response': response_text,
            'score': score  # 감정 점수 추가
        }

        # 결과 파일이 존재하지 않거나 비어 있으면 초기화
        if not os.path.exists(RESULT_FILE) or os.stat(RESULT_FILE).st_size == 0:
            result_df = pd.DataFrame(columns=['question_id', 'question', 'response', 'score'])
            result_df.to_csv(RESULT_FILE, index=False)
            logger.debug('Initialized results.csv with headers.')

        # 결과 파일에 데이터 추가
        result_df = pd.read_csv(RESULT_FILE)
        result_df = pd.concat([result_df, pd.DataFrame([result_data])], ignore_index=True)
        result_df.to_csv(RESULT_FILE, index=False)

        logger.debug(f'Result data saved: {result_data}')

        result = {
            'response': response_text,
            'score': score  # 점수 반환
        }

        return jsonify(result)

    except Exception as e:
        logger.exception("An error occurred during the recording of the response.")
        return jsonify({'error': str(e)}), 500

@app.route('/final_result', methods=['GET'])
def final_result():
    try:
        if not os.path.exists(RESULT_FILE):
            return jsonify({'error': '결과 파일이 존재하지 않습니다.'}), 400

        result_df = pd.read_csv(RESULT_FILE)
        average_score = result_df['score'].mean()  # 평균 점수 계산
        sentiment = '긍정' if average_score > 0.5 else '부정'  # 평균 점수를 기준으로 감정 결과 결정

        return jsonify({'average_score': average_score, 'sentiment': sentiment})
    except Exception as e:
        logger.exception("An error occurred while calculating the final result.")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
