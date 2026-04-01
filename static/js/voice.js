// voice.js — CogniSense
// Strictly scoped to voice-to-text via Web Speech API.
// Zero analysis logic. All scoring happens server-side in Flask.

(function () {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  const micBtn     = document.getElementById('mic-btn');
  const textarea   = document.getElementById('checkin-input');
  const voiceStatus = document.getElementById('voice-status');

  if (!micBtn || !textarea) return;

  // Graceful fallback if browser doesn't support Web Speech API
  if (!SpeechRecognition) {
    micBtn.disabled = true;
    micBtn.title = 'Voice input not supported in this browser. Try Chrome.';
    micBtn.style.opacity = '0.4';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  let isRecording = false;

  micBtn.addEventListener('click', function () {
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
    }
  });

  recognition.onstart = function () {
    isRecording = true;
    micBtn.classList.add('recording');
    micBtn.innerHTML = '🛑 Stop';
    if (voiceStatus) voiceStatus.classList.add('active');
  };

  recognition.onresult = function (event) {
    const transcript = event.results[0][0].transcript;
    // Append to existing text with a space if textarea already has content
    if (textarea.value.trim()) {
      textarea.value = textarea.value.trim() + ' ' + transcript;
    } else {
      textarea.value = transcript;
    }
  };

  recognition.onend = function () {
    isRecording = false;
    micBtn.classList.remove('recording');
    micBtn.innerHTML = '🎙 Speak';
    if (voiceStatus) voiceStatus.classList.remove('active');
  };

  recognition.onerror = function (event) {
    isRecording = false;
    micBtn.classList.remove('recording');
    micBtn.innerHTML = '🎙 Speak';
    if (voiceStatus) voiceStatus.classList.remove('active');

    let msg = 'Voice input error. Please try again.';
    if (event.error === 'not-allowed') {
      msg = 'Microphone access denied. Please allow mic permissions.';
    } else if (event.error === 'network') {
      msg = 'Network error during voice input.';
    } else if (event.error === 'no-speech') {
      msg = 'No speech detected. Please try again.';
    }

    // Show inline error
    if (voiceStatus) {
      voiceStatus.classList.add('active');
      const errSpan = voiceStatus.querySelector('.voice-err-text');
      if (errSpan) errSpan.textContent = msg;
      setTimeout(() => voiceStatus.classList.remove('active'), 3000);
    }
  };

  // Keyword chips → insert into textarea
  document.querySelectorAll('.keyword-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      const word = chip.dataset.word || chip.textContent.trim();
      const current = textarea.value.trim();
      textarea.value = current ? current + ' ' + word : word;
      textarea.focus();
    });
  });

})();