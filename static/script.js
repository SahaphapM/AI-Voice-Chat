const recognition = new webkitSpeechRecognition()
recognition.lang = 'en-US'

recognition.onresult = async (event) => {
  const text = event.results[0][0].transcript
  document.getElementById("userText").innerText = text

  const formData = new FormData()
  formData.append("message", text)

  const res = await fetch("/chat", {
    method: "POST",
    body: formData
  })

  const data = await res.json()
  document.getElementById("aiReply").innerText = data.reply

  const speech = new SpeechSynthesisUtterance(data.reply)
  speech.lang = 'en-US'
  speech.rate = 0.95
  speechSynthesis.speak(speech)
}

function startListening() {
  recognition.start()
}
