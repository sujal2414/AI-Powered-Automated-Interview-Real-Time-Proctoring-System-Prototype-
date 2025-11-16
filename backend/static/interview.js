// static/js/interview.js
// Complete interview front-end script
// Features: robust STT start/stop, blinking red dot, moving waveform (type C), follow-up handling.
// No UI markup changes required.

(() => {
  // ======= state =======
  let currentIndex = 0;
  let currentQuestion = "";
  let recognition = null;
  let recognizing = false;
  let finalTranscript = "";
  let followUpActive = false;
  let lastQAs = [];
  let manuallyStopped = false; // <= critical: must exist

  const SESSION_ID = "{{ session_id }}";
  const AUTO_SPEAK = true;

  // ======= elements =======
  const questionText = document.getElementById("questionText");
  const answerBox = document.getElementById("answerText");
  const info = document.getElementById("info");
  const camEl = document.getElementById("camera");
  const logEl = document.getElementById("log");
  const startBtn = document.getElementById("startBtn");
  const stopBtn = document.getElementById("stopBtn");
  const repeatBtn = document.getElementById("repeatBtn");
  const playBtn = document.getElementById("playBtn");
  const retryBtn = document.getElementById("retryBtn");
  const submitBtn = document.getElementById("submitBtn");

  function logMsg(msg) {
    const t = new Date().toLocaleTimeString();
    if (logEl) logEl.innerHTML = `<div>[${t}] ${msg}</div>` + logEl.innerHTML;
  }
  function setInfo(t) { if (info) info.innerText = "Status: " + t; }
  function speak(text) {
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "en-US";
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch (e) { console.warn("TTS failed:", e); }
  }

  // ======= Load question =======
  async function loadQuestion(index = 0) {
    setInfo("loading question...");
    try {
      const r = await fetch("/get_question", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: SESSION_ID, index })
      });
      const j = await r.json();
      if (!j) throw new Error("Bad /get_question response");
      if (j.done) {
        questionText.innerText = "All questions completed. Submit interview.";
        return;
      }
      currentQuestion = j.question;
      followUpActive = false;
      questionText.innerText = currentQuestion;
      if (AUTO_SPEAK) speak(currentQuestion);
      setInfo("question ready");
    } catch (e) {
      console.warn("loadQuestion error:", e);
      setInfo("Failed to load question");
    }
  }

  // ======= SpeechRecognition lifecycle =======
  function createRecognition() {
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Rec) return null;
    const r = new Rec();
    r.lang = "en-US";
    r.interimResults = true;
    r.continuous = true;

    r.onstart = () => {
      recognizing = true;
      setInfo("Recording… 🎤");
      startVisuals();
    };

    r.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        const txt = (res[0] && res[0].transcript) ? res[0].transcript : "";
        if (res.isFinal) finalTranscript += " " + txt;
        else interim += txt;
      }
      if (answerBox) answerBox.innerText = (finalTranscript + " " + interim).trim();
    };

    r.onerror = (ev) => {
      console.warn("SpeechRecognition error:", ev);
      // reflect error to user
      if (ev && ev.error) setInfo("STT error: " + ev.error);
    };

    r.onend = () => {
      recognizing = false;
      // only stop visuals/UI here if not manuallyStopped (to avoid double-stop edge cases)
      if (!manuallyStopped) {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        startBtn.innerText = "🎤 Start Recording";
        stopVisuals();
      }
    };

    return r;
  }

  // safe start wrapper
  function safeStartRecognition() {
    if (!recognition) recognition = createRecognition();
    if (!recognition) {
      setInfo("SpeechRecognition not supported. Use Chrome/Edge.");
      return;
    }
    try {
      recognition.start();
    } catch (e) {
      // Some browsers throw if start() called while already starting - handle gracefully.
      console.warn("recognition.start() exception:", e);
    }
  }

  // ======= Visuals: dot + moving waveform (C) =======
  const visuals = {
    dotWrap: null,
    wfWrapper: null,
    canvas: null,
    ctx: null,
    audioCtx: null,
    analyser: null,
    dataArray: null,
    source: null,
    stream: null,
    rafId: null
  };

  function ensureStyles() {
    if (document.getElementById("ai-intv-styles")) return;
    const s = document.createElement("style");
    s.id = "ai-intv-styles";
    s.innerHTML = `
      .ai-rec-dot-wrap { display:inline-flex; align-items:center; gap:6px; margin-left:8px; font-weight:600; color:#ef4444; }
      .ai-rec-dot { width:10px; height:10px; border-radius:50%; background:#ef4444; box-shadow:0 0 8px rgba(239,68,68,0.9); animation:ai-blink 1s infinite; }
      @keyframes ai-blink { 0%{opacity:1}50%{opacity:0.3}100%{opacity:1} }
      .ai-wave-wrapper { width:100%; height:56px; margin-top:10px; border-radius:8px; overflow:hidden; }
      .ai-wave-canvas { width:100%; height:100%; display:block; }
    `;
    document.head.appendChild(s);
  }

  function createVisualElements() {
    if (visuals.dotWrap) return;
    ensureStyles();

    // dot wrap next to startBtn
    const dotWrap = document.createElement("div");
    dotWrap.className = "ai-rec-dot-wrap";
    dotWrap.style.display = "none";
    const dot = document.createElement("span");
    dot.className = "ai-rec-dot";
    const lbl = document.createElement("span");
    lbl.innerText = "Recording";
    lbl.style.fontSize = "13px";
    dotWrap.appendChild(dot);
    dotWrap.appendChild(lbl);
    if (startBtn && startBtn.parentNode) startBtn.parentNode.insertBefore(dotWrap, startBtn.nextSibling);
    else document.body.appendChild(dotWrap);

    // waveform wrapper appended after .controls
    const controls = document.querySelector(".controls");
    const wfWrapper = document.createElement("div");
    wfWrapper.className = "ai-wave-wrapper";
    wfWrapper.style.display = "none";
    const canvas = document.createElement("canvas");
    canvas.className = "ai-wave-canvas";
    wfWrapper.appendChild(canvas);

    if (controls && controls.parentNode) controls.parentNode.insertBefore(wfWrapper, controls.nextSibling);
    else document.body.appendChild(wfWrapper);

    visuals.dotWrap = dotWrap;
    visuals.wfWrapper = wfWrapper;
    visuals.canvas = canvas;
    visuals.ctx = canvas.getContext("2d");
  }

  function startVisuals() {
    createVisualElements();
    if (!visuals.dotWrap) return;
    visuals.dotWrap.style.display = "inline-flex";
    visuals.wfWrapper.style.display = "block";
    startWaveform();
  }

  function stopVisuals() {
    if (visuals.dotWrap) visuals.dotWrap.style.display = "none";
    if (visuals.wfWrapper) visuals.wfWrapper.style.display = "none";
    stopWaveform();
  }

  // waveform functions
  function startWaveform() {
    if (visuals.rafId) return; // already running
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;

    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(stream => {
        visuals.stream = stream;
        try {
          const AudioCtx = window.AudioContext || window.webkitAudioContext;
          visuals.audioCtx = new AudioCtx();
          visuals.source = visuals.audioCtx.createMediaStreamSource(stream);
          visuals.analyser = visuals.audioCtx.createAnalyser();
          visuals.analyser.fftSize = 2048;
          const bufferLength = visuals.analyser.fftSize;
          visuals.dataArray = new Uint8Array(bufferLength);
          visuals.source.connect(visuals.analyser);

          resizeCanvas();
          drawWaveform();
        } catch (e) {
          console.warn("AudioContext init error:", e);
        }
      })
      .catch(err => {
        console.warn("getUserMedia (waveform) denied or failed:", err);
      });
  }

  function stopWaveform() {
    if (visuals.rafId) {
      cancelAnimationFrame(visuals.rafId);
      visuals.rafId = null;
    }
    if (visuals.stream) {
      visuals.stream.getTracks().forEach(t => t.stop());
      visuals.stream = null;
    }
    if (visuals.audioCtx) {
      try { visuals.audioCtx.close(); } catch (e) {}
      visuals.audioCtx = null;
      visuals.analyser = null;
      visuals.dataArray = null;
      visuals.source = null;
    }
    if (visuals.ctx && visuals.canvas) {
      visuals.ctx.clearRect(0, 0, visuals.canvas.width, visuals.canvas.height);
    }
  }

  function resizeCanvas() {
    if (!visuals.canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = visuals.canvas.getBoundingClientRect();
    const w = Math.max(300, Math.floor(rect.width * dpr));
    const h = Math.max(56, Math.floor(rect.height * dpr));
    if (visuals.canvas.width !== w || visuals.canvas.height !== h) {
      visuals.canvas.width = w;
      visuals.canvas.height = h;
    }
  }

  function drawWaveform() {
    if (!visuals.analyser || !visuals.ctx) return;
    const canvas = visuals.canvas;
    const ctx = visuals.ctx;
    const bufferLength = visuals.analyser.fftSize;

    function draw() {
      visuals.rafId = requestAnimationFrame(draw);
      visuals.analyser.getByteTimeDomainData(visuals.dataArray);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.lineWidth = 2;
      ctx.strokeStyle = 'rgba(59,130,246,0.95)';
      ctx.beginPath();
      const sliceWidth = canvas.width / bufferLength;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = visuals.dataArray[i] / 128.0; // 0..2
        const y = (v * canvas.height) / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();

      // center line subtle
      ctx.strokeStyle = 'rgba(15,23,42,0.06)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
    }

    resizeCanvas();
    draw();
  }

  // ======= Start / Stop logic (robust + idempotent) =======
  function startRecordingUI() {
    startBtn.innerText = "🎤 Recording…";
    startBtn.disabled = true;
    stopBtn.disabled = false;
    setInfo("Recording… 🎤");
    startVisuals();
  }

  function stopRecordingUI() {
    startBtn.innerText = "🎤 Start Recording";
    startBtn.disabled = false;
    stopBtn.disabled = true;
    stopVisuals();
  }

  startBtn.addEventListener("click", () => {
    finalTranscript = "";
    answerBox && (answerBox.innerText = "");
    manuallyStopped = false;

    if (!recognition) recognition = createRecognition();
    // recognition may be in 'ended' state; start safely
    try {
      recognition && recognition.start();
    } catch (e) {
      // ignore repeated-start errors
      console.warn("recognition.start() error (ignored):", e);
      // try recreate then start
      recognition = createRecognition();
      try { recognition && recognition.start(); } catch (err) { console.warn("start retry failed:", err); }
    }

    startRecordingUI();
  });

  stopBtn.addEventListener("click", async () => {
    manuallyStopped = true;

    try {
      recognition && recognition.stop();
    } catch (e) {
      console.warn("recognition.stop error:", e);
    }

    // reset UI immediately
    stopRecordingUI();

    // save answer flow
    const ans = (answerBox && answerBox.innerText) ? answerBox.innerText.trim() : "";
    if (!ans) {
      setInfo("No answer detected. Please retry.");
      return;
    }

    setInfo("Saving answer…");

    try {
      await fetch("/submit_answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: SESSION_ID, question: currentQuestion, answer: ans })
      });
      lastQAs.push(`Q: ${currentQuestion}\nA: ${ans}`);
      if (lastQAs.length > 10) lastQAs.shift();
    } catch (e) {
      console.warn("submit_answer failed:", e);
    }

    // generate follow-up
    let followUp = null;
    try {
      const r = await fetch("/generate_followup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: SESSION_ID,
          question: currentQuestion,
          answer: ans,
          history: lastQAs.slice(-3)
        })
      });
      const j = await r.json();
      if (j && j.ok && j.follow_up) followUp = j.follow_up;
    } catch (e) {
      console.warn("generate_followup error:", e);
    }

    if (followUp) {
      followUpActive = true;
      currentQuestion = followUp;
      finalTranscript = "";
      answerBox && (answerBox.innerText = "");
      questionText && (questionText.innerText = currentQuestion);
      if (AUTO_SPEAK) speak(currentQuestion);
      setInfo("Follow-up question ready.");
      // keep visuals stopped until next record
      stopVisuals();
      return;
    }

    // advance to next main question
    currentIndex++;
    finalTranscript = "";
    answerBox && (answerBox.innerText = "");
    await loadQuestion(currentIndex);
    setInfo("Ready to record.");
  });

  // ======= Other controls =======
  retryBtn && retryBtn.addEventListener("click", () => {
    manuallyStopped = true;
    try { recognition && recognition.stop(); } catch (e) {}
    stopVisuals();
    finalTranscript = "";
    answerBox && (answerBox.innerText = "");
    setInfo("Retry your answer.");
    startBtn.innerText = "🎤 Start Recording";
  });

  repeatBtn && repeatBtn.addEventListener("click", () => {
    try { recognition && recognition.stop(); } catch (e) {}
    finalTranscript = "";
    answerBox && (answerBox.innerText = "");
    if (currentQuestion) speak(currentQuestion);
    stopVisuals();
  });

  playBtn && playBtn.addEventListener("click", () => {
    if (currentQuestion) speak(currentQuestion);
  });

  // keyboard shortcut 'n' for stop/next
  window.addEventListener("keydown", (e) => {
    if (e.key && e.key.toLowerCase() === "n") {
      stopBtn && stopBtn.click();
    }
  });

  // ======= Camera + Countdown (unchanged) =======
  async function initCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (camEl) camEl.srcObject = stream;
      const cs = document.getElementById("camStatus");
      if (cs) cs.innerText = "camera: on";
    } catch (e) {
      logMsg("Camera error: " + e);
    }
  }

  async function startCountdown() {
    let t = 5;
    const counter = document.getElementById("count");
    const timer = setInterval(() => {
      if (counter) counter.innerText = t;
      if (t === 0) {
        clearInterval(timer);
        loadQuestion(0);
      }
      t--;
    }, 1000);
  }

  // ======= init =======
  (async () => {
    try { await initCamera(); } catch (e) {}
    startCountdown();
  })();

})();
