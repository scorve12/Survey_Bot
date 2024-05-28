document.getElementById("start-survey").addEventListener("click", () => {
  fetch("/process")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
        return;
      }
      let questionDiv = document.getElementById("question");
      let responseDiv = document.getElementById("response");
      let resultDiv = document.getElementById("result");

      resultDiv.innerHTML = `<h2>설문 결과</h2>`;

      let score = data.reduce(
        (sum, item) => sum + (item.sentiment === "positive" ? 1 : 0),
        0
      );

      data.forEach((item, index) => {
        resultDiv.innerHTML += `<p><b>질문 ${index + 1}:</b> ${
          item.display_text
        }</p>`;
        resultDiv.innerHTML += `<p><b>응답 ${index + 1}:</b> ${
          item.response_text
        } (${item.sentiment})</p>`;
      });

      resultDiv.innerHTML += `<h3>총 감정 분석 점수: ${score}</h3>`;
    })
    .catch((error) => console.error("Error:", error));
});
