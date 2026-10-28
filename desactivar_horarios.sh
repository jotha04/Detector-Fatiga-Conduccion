#!/bin/bash
# ==========================================================
# SANCHEZ POLO - DESACTIVAR HORARIOS DE ENCENDIDO Y APAGADO
# ==========================================================

if [ "$EUID" -ne 0 ]; then
    echo "Por favor ejecuta este script con permisos de administrador: sudo ./desactivar_horarios.sh"
    exit 1
fi

DAEMON_DST="/Library/LaunchDaemons/com.sanchezpolo.autoshutdown.plist"

echo "Eliminando programaciones automáticas..."
pmset repeat cancel
if [ -f "$DAEMON_DST" ]; then
    launchctl unload "$DAEMON_DST" 2>/dev/null
    rm -f "$DAEMON_DST"
fi

echo "Programación eliminada con éxito."
pmset -g sched
