const recognition = new webkitSpeechRecognition()
recognition.lang = 'en-US'
recognition.interimResults = false
recognition.continuous = true

let micBtn = document.getElementById('micBtn')
let userText = document.getElementById('userText')
let aiReply = document.getElementById('aiReply')
let loading = document.getElementById('loading')
let isListening = false
let transcript = ''

micBtn.addEventListener('mousedown', () => {
  if (micBtn.disabled) return
  isListening = true
  transcript = ''
  micBtn.classList.add('recording')
  recognition.start()
})

micBtn.addEventListener('mouseup', () => {
  if (!isListening) return
  isListening = false
  micBtn.classList.remove('recording')
  recognition.stop()
})

recognition.onresult = (event) => {
  for (let i = event.resultIndex; i < event.results.length; ++i) {
    if (event.results[i].isFinal) {
      transcript += event.results[i][0].transcript + ' '
    }
  }
}

recognition.onend = async () => {
  if (!transcript.trim()) return
  userText.innerHTML = `You: <strong>${transcript}</strong>`
  micBtn.disabled = true
  loading.style.display = 'block'

  const formData = new FormData()
  formData.append("message", transcript)
  const res = await fetch("/chat", {
    method: "POST",
    body: formData
  })
  const data = await res.json()

  aiReply.innerHTML = `AI: ${data.reply}`

  const utterance = new SpeechSynthesisUtterance(data.reply)
  utterance.lang = 'en-US'
  utterance.rate = 0.95
  speechSynthesis.speak(utterance)

  micBtn.disabled = false
  loading.style.display = 'none'
}
