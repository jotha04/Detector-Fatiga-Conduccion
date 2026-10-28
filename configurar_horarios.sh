#!/bin/bash
# ==========================================================
# SANCHEZ POLO - CONFIGURADOR DE HORARIOS DE ENCENDIDO Y APAGADO
# ==========================================================

# Si no somos root, solicitar permisos usando sudo directamente en esta terminal
if [ "$EUID" -ne 0 ]; then
    clear
    echo "=========================================================="
    echo "       DETECTOR DE FATIGA - SANCHEZ POLO"
    echo "  CONFIGURACION DE HORARIOS DE ENCENDIDO Y APAGADO"
    echo "=========================================================="
    echo ""
    echo "Para configurar el hardware y el sistema se requieren"
    echo "permisos de administrador."
    echo ""
    echo "Por favor escribe tu contraseña de Mac a continuación:"
    echo "(Al escribir no verás los caracteres por seguridad, solo presiona Enter)"
    echo ""
    
    sudo bash "$0" "$@"
    EXIT_CODE=$?
    
    echo ""
    read -n 1 -s -r -p "Presiona cualquier tecla para salir..."
    echo ""
    exit $EXIT_CODE
fi

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAEMON_SRC="$PROJECT_DIR/scripts/com.sanchezpolo.autoshutdown.plist"
DAEMON_DST="/Library/LaunchDaemons/com.sanchezpolo.autoshutdown.plist"

clear
echo "=========================================================="
echo " Configurando Horarios Sanchez Polo:"
echo " - Encendido: Lunes a Sábado a las 7:00 AM (Domingo: APAGADO)"
echo " - Apagado:   Lunes a Viernes a las 7:00 PM (19:00)"
echo "              Sábados a las 2:00 PM (14:00)"
echo "=========================================================="
echo ""

# 1. Configurar Encendido / Wake en el hardware (pmset)
echo "[1/3] Configurando encendido de hardware (pmset)..."
# MTWRFS = Lunes, Martes, Miércoles, Jueves, Viernes, Sábado (U/Domingo excluido)
pmset repeat wakeorpoweron MTWRFS 07:00:00

# 2. Instalar el servicio de apagado programado en el sistema
echo "[2/3] Instalando servicio de apagado automático (LaunchDaemon)..."
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$DAEMON_SRC" > "$DAEMON_DST"
chown root:wheel "$DAEMON_DST"
chmod 644 "$DAEMON_DST"

# Recargar servicio en launchd
launchctl unload "$DAEMON_DST" 2>/dev/null
launchctl load "$DAEMON_DST" 2>/dev/null

# 3. Confirmar estado
echo "[3/3] Verificando programación activa:"
echo ""
echo "--- Horarios de Encendido en Hardware (pmset) ---"
pmset -g sched
echo ""
echo "--- Servicio de Apagado Instalado en macOS ---"
ls -la "$DAEMON_DST"

echo ""
echo "=========================================================="
echo " ¡CONFIGURACION COMPLETADA CON EXITO!"
echo "=========================================================="
echo "1. Tu Mac encenderá automáticamente a las 7:00 AM de lunes a sábado."
echo "2. Los domingos permanecerá apagada."
echo "3. Se apagará sola a las 7:00 PM (L-V) y a las 2:00 PM (Sábados)."
echo "4. El detector iniciará maximizado con audio activo al encender."
echo "=========================================================="
