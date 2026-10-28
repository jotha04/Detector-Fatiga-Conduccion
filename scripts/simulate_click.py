#!/usr/bin/env python3
import ctypes
import time
import subprocess

# 1. Traer Google Chrome al frente
try:
    subprocess.run([
        "osascript", "-e",
        'tell application "Google Chrome" to activate\n'
        'tell application "System Events" to tell process "Google Chrome" to set frontmost to true'
    ], check=True, capture_output=True)
except Exception as e:
    print(f"Aviso activando Chrome: {e}")

time.sleep(0.8)

# 2. Utilizar CoreGraphics de macOS para emitir eventos de ratón reales
try:
    cg = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')

    class CGRect(ctypes.Structure):
        _fields_ = [
            ('origin_x', ctypes.c_double), ('origin_y', ctypes.c_double),
            ('size_w', ctypes.c_double), ('size_h', ctypes.c_double)
        ]

    class CGPoint(ctypes.Structure):
        _fields_ = [('x', ctypes.c_double), ('y', ctypes.c_double)]

    cg.CGMainDisplayID.restype = ctypes.c_uint32
    cg.CGDisplayBounds.restype = CGRect
    cg.CGDisplayBounds.argtypes = [ctypes.c_uint32]

    cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
    cg.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, CGPoint, ctypes.c_uint32]
    cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]

    main_id = cg.CGMainDisplayID()
    bounds = cg.CGDisplayBounds(main_id)
    w = bounds.size_w if bounds.size_w > 0 else 1920.0
    h = bounds.size_h if bounds.size_h > 0 else 1080.0

    # Clic en el centro de la pantalla
    center_pt = CGPoint(w / 2.0, h / 2.0)
    
    # Mover cursor
    move_evt = cg.CGEventCreateMouseEvent(None, 5, center_pt, 0)
    cg.CGEventPost(0, move_evt)
    time.sleep(0.05)

    # Clic (Down + Up)
    down_evt = cg.CGEventCreateMouseEvent(None, 1, center_pt, 0)
    up_evt = cg.CGEventCreateMouseEvent(None, 2, center_pt, 0)
    cg.CGEventPost(0, down_evt)
    time.sleep(0.05)
    cg.CGEventPost(0, up_evt)

    # Segundo clic de respaldo a 1/3 de la pantalla
    time.sleep(0.1)
    backup_pt = CGPoint(w / 3.0, h / 2.0)
    down_evt2 = cg.CGEventCreateMouseEvent(None, 1, backup_pt, 0)
    up_evt2 = cg.CGEventCreateMouseEvent(None, 2, backup_pt, 0)
    cg.CGEventPost(0, down_evt2)
    time.sleep(0.05)
    cg.CGEventPost(0, up_evt2)

    print("Interacción física de ratón simulada exitosamente con CoreGraphics.")
except Exception as err:
    print(f"Error simulando interacción con CoreGraphics: {err}")
