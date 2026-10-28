#!/bin/bash
# ==========================================================
# SANCHEZ POLO - INICIO AUTOMATICO DETECTOR EN GOOGLE CHROME
# ==========================================================

# Directorio base donde reside este script
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR" || exit 1

# Determinar intérprete de Python (entorno virtual local o python3 del sistema)
if [ -f "$PROJECT_DIR/.venv/bin/python3" ]; then
    PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python3"
elif [ -f "$PROJECT_DIR/venv/bin/python3" ]; then
    PYTHON_EXEC="$PROJECT_DIR/venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXEC="$(command -v python3)"
else
    PYTHON_EXEC="python3"
fi

# 1. Iniciar servidor web en segundo plano si no está activo
if ! pgrep -f "web_app/server.py" > /dev/null; then
    OPENCV_AVFOUNDATION_SKIP_AUTH=1 "$PYTHON_EXEC" "$PROJECT_DIR/web_app/server.py" > /dev/null 2>&1 &
fi

# 2. Esperar a que el servidor web responda en http://localhost:8000
for i in {1..20}; do
    if curl -s http://localhost:8000 >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# 3. Abrir la pestaña en Google Chrome, restablecer zoom al 100% y maximizar la ventana
osascript << 'APPLESCRIPT'
tell application "Google Chrome"
    activate
    open location "http://localhost:8000"
end tell
delay 0.5
tell application "System Events"
    tell process "Google Chrome"
        set frontmost to true
        try
            keystroke "0" using {command down}
        end try
        try
            perform action "AXZoomWindow" of window 1
        end try
    end tell
end tell
APPLESCRIPT

# 4. Esperar a que cargue la interfaz y simular clic físico para desbloquear audio
sleep 1.5
if [ -f "$PROJECT_DIR/scripts/simulate_click.py" ]; then
    "$PYTHON_EXEC" "$PROJECT_DIR/scripts/simulate_click.py" > /dev/null 2>&1
fi

exit 0
