document.addEventListener("DOMContentLoaded", () => {
  const startButton = document.getElementById("start-survey");
  const nextButton = document.getElementById("next-question");

  if (!startButton) {
    console.error("Start survey button not found");
    return;
  }

  if (!nextButton) {
    console.error("Next question button not found");
    return;
  }

  startButton.addEventListener("click", () => {
    fetch("/get_questions")
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((questions) => {
        let questionDiv = document.getElementById("question");
        let responseDiv = document.getElementById("response");
        let recordingStatusDiv = document.getElementById("recording-status");
        let resultDiv = document.getElementById("result");
        let currentQuestion = 0;
        let totalScore = 0;

        function processNextQuestion() {
          if (currentQuestion < questions.length) {
            let question = questions[currentQuestion];
            questionDiv.innerHTML = `<p><b>질문 ${currentQuestion + 1}:</b> ${question.question}</p>`;
            recordingStatusDiv.innerHTML = '';

            let audio = new Audio(question.audio);
            audio.play();

            audio.onended = () => {
              recordingStatusDiv.innerHTML = `<p>질문에 대한 응답을 해주세요.</p>`;
              console.log("질문에 대한 응답을 해주세요.");

              // 녹음 시작
              navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                  const mediaRecorder = new MediaRecorder(stream);
                  const audioChunks = [];

                  mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                  };

                  mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks);
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'response.wav');

                    recordingStatusDiv.innerHTML = `<p>녹음을 마칩니다.</p>`;
                    console.log("녹음을 마칩니다.");

                    // 서버에 녹음 요청
                    fetch('/record_response', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json'
                      },
                      body: JSON.stringify({ question_id: currentQuestion })
                    })
                      .then(response => response.json())
                      .then(responseData => {
                        if (responseData.error) {
                          alert(responseData.error);
                          recordingStatusDiv.innerHTML = `<p>${responseData.error}</p>`;
                          return;
                        }

                        responseDiv.innerHTML += `<p><b>응답 ${currentQuestion + 1}:</b> ${responseData.response} (${responseData.sentiment})</p>`;
                        totalScore += responseData.sentiment === 'positive' ? 1 : 0;
                        currentQuestion++;
                        nextButton.style.display = 'block';
                      })
                      .catch(error => {
                        console.error("Error:", error);
                        alert('서버와의 통신 중 오류가 발생했습니다.');
                      });
                  };

                  mediaRecorder.start();
                  setTimeout(() => {
                    mediaRecorder.stop();
                  }, DURATION * 1000);
                })
                .catch(error => {
                  console.error("Error:", error);
                  alert('녹음 장치를 사용할 수 없습니다.');
                });
            };
          } else {
            resultDiv.innerHTML = `<h2>설문 결과</h2><p>총 감정 분석 점수: ${totalScore}</p>`;
          }
        }

        nextButton.addEventListener("click", () => {
          nextButton.style.display = 'none';
          processNextQuestion();
        });

        processNextQuestion();
      })
      .catch((error) => {
        console.error("Error:", error);
        alert('질문을 불러오는 중 오류가 발생했습니다.');
      });
  });
});
