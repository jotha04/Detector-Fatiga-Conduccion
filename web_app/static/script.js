// Connect to WebSocket
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

// Audio setup
let alertAudio = new Audio('/static/music.wav');
alertAudio.loop = true;
alertAudio.preload = 'auto';
alertAudio.load();
let isPlayingAlert = false;
let audioEnabled = document.getElementById('audioToggle').checked;
let audioUnlocked = false;

function unlockAudio() {
    if (audioUnlocked) return;
    alertAudio.play().then(() => {
        audioUnlocked = true;
        setTimeout(() => {
            if (!isPlayingAlert) {
                try {
                    alertAudio.pause();
                    alertAudio.currentTime = 0;
                } catch (e) {}
            }
        }, 50);
        console.log("Audio desbloqueado correctamente");
    }).catch(e => {
        // En espera de interacción física
    });
}

// Intentar desbloquear al cargar y con cualquier interacción o foco
unlockAudio();
['click', 'pointerdown', 'keydown', 'touchstart', 'focus'].forEach(evt => {
    window.addEventListener(evt, unlockAudio, { passive: true });
});

document.getElementById('audioToggle').addEventListener('change', (e) => {
    audioEnabled = e.target.checked;
    if (!audioEnabled) {
        stopAlert();
    }
});

// Slider de umbral EAR - envía cambios al servidor en tiempo real
const earSlider = document.getElementById('earSlider');
earSlider.disabled = false; // Habilitar el slider
earSlider.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    document.getElementById('sliderVal').innerText = val.toFixed(2);
    // Enviar al backend
    fetch('/set_threshold', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threshold: val })
    }).catch(err => console.error('Error enviando umbral:', err));
});

// Chart setup for EAR history
let chart = null;
const earCanvas = document.getElementById('earChart');
const maxDataPoints = 150; // ~15 seconds at 10Hz telemetry
const earData = Array(maxDataPoints).fill(0);
const labels = Array(maxDataPoints).fill('');

if (typeof Chart !== 'undefined' && earCanvas) {
    try {
        const ctx = earCanvas.getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Apertura de Ojos',
                    data: earData,
                    borderColor: '#00F0FF',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    fill: true,
                    backgroundColor: 'rgba(0, 240, 255, 0.1)'
                },
                {
                    label: 'Límite de Alerta',
                    data: Array(maxDataPoints).fill(0.20), // Initial threshold
                    borderColor: 'rgba(255, 51, 102, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 0.4,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#8E9BAE', stepSize: 0.1 }
                    },
                    x: {
                        display: false
                    }
                }
            }
        });
    } catch (e) {
        console.warn("No se pudo inicializar Chart:", e);
    }
}

// Play the continuous alert sound
function playAlert() {
    if (!audioEnabled) return;
    const playPromise = alertAudio.play();
    if (playPromise !== undefined) {
        playPromise.then(() => {
            isPlayingAlert = true;
        }).catch(e => {
            console.warn("Reproducción de audio bloqueada temporalmente por el navegador:", e.message);
            isPlayingAlert = false; // Permite reintentar tan pronto haya interacción
        });
    }
}

// Stop the alert sound
function stopAlert() {
    isPlayingAlert = false;
    try {
        alertAudio.pause();
        alertAudio.currentTime = 0;
    } catch (e) {}
}

// Websocket updates
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    // Update chart if available
    if (chart) {
        earData.shift();
        earData.push(data.ear);
        const currentThreshold = data.threshold_ear;
        chart.data.datasets[1].data = Array(maxDataPoints).fill(currentThreshold);
        chart.update('none');
    }

    // Update stats
    document.getElementById('val-fps').innerText = data.fps_real;
    document.getElementById('val-ear').innerText = data.ear.toFixed(2);
    document.getElementById('val-mar').innerText = data.mar.toFixed(2);
    document.getElementById('val-pitch').innerText = data.head_pitch + "°";
    document.getElementById('val-thresh-ear').innerText = data.threshold_ear.toFixed(2);

    // Update Main Status
    const statusEl = document.getElementById('fatigueStatus');
    const typeEl = document.getElementById('fatigueType');
    const fillEl = document.getElementById('fatigueBar');
    
    if (data.fatigueLevel === "ALTO" || data.fatigueLevel === "HIGH") {
        statusEl.innerText = "ALERTA FATIGA";
        statusEl.classList.add('alert');
        typeEl.innerText = data.fatigueType === "MICRO_SLEEP" ? "¡Microsueño Detectado!" : "¡Cabeceo / Pérdida de Atención!";
        fillEl.classList.add('alert');
        
        if (!isPlayingAlert) {
            playAlert();
        }
    } else {
        statusEl.classList.remove('alert');
        fillEl.classList.remove('alert');
        
        if (data.camera_status === "Buscando rostro...") {
            statusEl.innerText = "EN ESPERA";
            typeEl.innerText = "Buscando rostro...";
        } else {
            statusEl.innerText = "NORMAL";
            typeEl.innerText = "Conducción Segura";
        }
        
        if (isPlayingAlert) {
            stopAlert();
        }
    }
};

ws.onclose = function(e) {
    console.error('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
    document.getElementById('fatigueStatus').innerText = "DESCONECTADO";
    document.getElementById('fatigueStatus').classList.add('alert');
};

ws.onerror = function(err) {
    console.error('Socket encountered error: ', err.message, 'Closing socket');
    ws.close();
};
