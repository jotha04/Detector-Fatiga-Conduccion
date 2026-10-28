#!/bin/bash
# ==========================================================
# SANCHEZ POLO - SCRIPT DE APAGADO AUTOMATICO PROGRAMADO
# ==========================================================
# Horarios:
# - Lunes a Viernes: Apagar a las 19:00 (7:00 PM)
# - Sábado: Apagar a las 14:00 (2:00 PM)
# - Domingo: No enciende
# ==========================================================

DOW=$(date +%u)    # 1=Lunes, 2=Martes, 3=Miércoles, 4=Jueves, 5=Viernes, 6=Sábado, 7=Domingo
HOUR=$(date +%H)   # 00-23
MIN=$(date +%M)    # 00-59

SHOULD_SHUTDOWN=false

# Lunes a Viernes (1 al 5) a las 19:00
if [ "$DOW" -ge 1 ] && [ "$DOW" -le 5 ]; then
    if [ "$HOUR" -eq 19 ] && [ "$MIN" -le 15 ]; then
        SHOULD_SHUTDOWN=true
    fi
fi

# Sábado (6) a las 14:00
if [ "$DOW" -eq 6 ]; then
    if [ "$HOUR" -eq 14 ] && [ "$MIN" -le 15 ]; then
        SHOULD_SHUTDOWN=true
    fi
fi

if [ "$SHOULD_SHUTDOWN" = true ]; then
    echo "$(date): [Sanchez Polo] Ejecutando apagado automático programado..." >> /var/log/sanchezpolo_shutdown.log
    /sbin/shutdown -h now
else
    echo "$(date): Verificación de apagado omitida (DOW=$DOW HOUR=$HOUR MIN=$MIN no corresponde)" >> /var/log/sanchezpolo_shutdown.log
fi
