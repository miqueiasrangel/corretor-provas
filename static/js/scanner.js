/**
 * scanner.js - Captura de câmera ao vivo e feedback em tempo real
 * Utiliza navigator.mediaDevices.getUserMedia e Canvas API.
 */

let videoStream = null;
let isScanning = false;
let isProcessingFrame = false;

const video = document.getElementById('videoFeed');
const canvas = document.getElementById('overlayCanvas');
const statusBadge = document.getElementById('statusBadge');
const stabilityProgressBar = document.getElementById('stabilityProgress');
const sharpnessText = document.getElementById('sharpnessText');
const btnStart = document.getElementById('btnStartCamera');
const btnStop = document.getElementById('btnStopCamera');
const btnCaptureNow = document.getElementById('btnCaptureNow');
const answerKeySelect = document.getElementById('answerKeySelect');
const studentNameInput = document.getElementById('studentNameInput');

async function startCamera() {
    try {
        const constraints = {
            video: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        };

        videoStream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = videoStream;
        await video.play();

        isScanning = true;
        btnStart.classList.add('d-none');
        btnStop.classList.remove('d-none');
        btnCaptureNow.classList.remove('d-none');
        statusBadge.textContent = "Buscando folha de respostas...";
        statusBadge.className = "badge bg-warning text-dark";

        requestAnimationFrame(processLoop);
    } catch (err) {
        console.error("Erro ao acessar a câmera:", err);
        statusBadge.textContent = "Erro ao acessar câmera: " + err.message;
        statusBadge.className = "badge bg-danger";
        alert("Não foi possível acessar a câmera. Verifique se o navegador possui permissão ou use a opção de 'Upload de Foto'.");
    }
}

function stopCamera() {
    isScanning = false;
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    video.srcObject = null;
    btnStart.classList.remove('d-none');
    btnStop.classList.add('d-none');
    btnCaptureNow.classList.add('d-none');
    clearOverlay();
    statusBadge.textContent = "Câmera desligada";
    statusBadge.className = "badge bg-secondary";
}

function clearOverlay() {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

async function processLoop() {
    if (!isScanning) return;

    if (!isProcessingFrame && video.readyState === video.HAVE_ENOUGH_DATA) {
        isProcessingFrame = true;
        await analyzeCurrentFrame(false);
        isProcessingFrame = false;
    }

    // Intervalo de amostragem suave para não sobrecarregar o cliente nem o servidor (~200ms)
    setTimeout(() => {
        if (isScanning) {
            requestAnimationFrame(processLoop);
        }
    }, 200);
}

async function analyzeCurrentFrame(forceGrade = false) {
    if (!video.videoWidth || !video.videoHeight) return;

    // Ajusta o tamanho interno do canvas de overlay para coincidir com o vídeo
    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
    }

    // Cria um canvas temporário para extrair o frame como JPEG base64
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = 640; // Reduz tamanho para transmissão rápida em rede
    tempCanvas.height = Math.round((video.videoHeight / video.videoWidth) * 640);
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
    const frameBase64 = tempCanvas.toDataURL('image/jpeg', 0.7);

    const payload = {
        frame: frameBase64,
        key_id: answerKeySelect.value,
        student_name: studentNameInput.value.trim() || "Aluno via Webcam",
        force_grade: forceGrade
    };

    try {
        const response = await fetch('/api/quadro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (!data.success) {
            drawStatus(null, 0, 0, false);
            return;
        }

        // Se a folha foi capturada e corrigida (ou por estabilidade ou botão)
        if (data.graded && data.redirect_url) {
            stopCamera();
            statusBadge.textContent = "Folha capturada e corrigida! Redirecionando...";
            statusBadge.className = "badge bg-success";
            window.location.href = data.redirect_url;
            return;
        }

        // Desenha cantos e progresso na tela
        drawStatus(data.corners, data.stable_frames, data.sharpness, data.ready, tempCanvas.width, tempCanvas.height);

    } catch (err) {
        console.warn("Erro no processamento de frame:", err);
    }
}

function drawStatus(corners, stableFrames, sharpness, isReady, frameW, frameH) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Atualiza indicadores numéricos
    if (sharpnessText) {
        sharpnessText.textContent = `Nitidez: ${Math.round(sharpness || 0)}`;
    }
    if (stabilityProgressBar) {
        const pct = Math.min(100, Math.round(((stableFrames || 0) / 5) * 100));
        stabilityProgressBar.style.width = pct + '%';
        stabilityProgressBar.setAttribute('aria-valuenow', pct);
    }

    if (!corners || corners.length !== 4) {
        statusBadge.textContent = "Aponte a câmera para a folha...";
        statusBadge.className = "badge bg-warning text-dark";
        return;
    }

    // Fator de escala entre o frame reduzido enviado e o canvas de visualização
    const scaleX = canvas.width / (frameW || canvas.width);
    const scaleY = canvas.height / (frameH || canvas.height);

    const scaledCorners = corners.map(pt => [pt[0] * scaleX, pt[1] * scaleY]);

    // Desenha polígono dos 4 cantos
    ctx.beginPath();
    ctx.moveTo(scaledCorners[0][0], scaledCorners[0][1]);
    for (let i = 1; i < 4; i++) {
        ctx.lineTo(scaledCorners[i][0], scaledCorners[i][1]);
    }
    ctx.closePath();

    if (isReady) {
        ctx.strokeStyle = '#16a34a'; // Verde forte
        ctx.fillStyle = 'rgba(22, 163, 74, 0.2)';
        statusBadge.textContent = "Folha estável! Capturando...";
        statusBadge.className = "badge bg-success";
    } else {
        ctx.strokeStyle = '#2563eb'; // Azul
        ctx.fillStyle = 'rgba(37, 99, 235, 0.15)';
        statusBadge.textContent = `Mantenha a folha parada (${stableFrames}/5)...`;
        statusBadge.className = "badge bg-info text-dark";
    }

    ctx.lineWidth = 4;
    ctx.stroke();
    ctx.fill();

    // Desenha círculos nos 4 vértices
    for (let i = 0; i < 4; i++) {
        ctx.beginPath();
        ctx.arc(scaledCorners[i][0], scaledCorners[i][1], 8, 0, 2 * Math.PI);
        ctx.fillStyle = isReady ? '#16a34a' : '#f59e0b';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

// Event Listeners
if (btnStart) btnStart.addEventListener('click', startCamera);
if (btnStop) btnStop.addEventListener('click', stopCamera);
if (btnCaptureNow) {
    btnCaptureNow.addEventListener('click', async () => {
        btnCaptureNow.disabled = true;
        btnCaptureNow.textContent = "Processando...";
        await analyzeCurrentFrame(true);
        btnCaptureNow.disabled = false;
        btnCaptureNow.textContent = "Capturar e Corrigir Agora";
    });
}

