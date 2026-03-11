#!/usr/bin/env python3
"""
test_rfid.py - Prueba básica del lector RC522
Muestra el UID de cualquier tarjeta o tag NFC que acerques.

Conexiones RC522 → RPi:
  SDA  → GPIO8  (Pin 24)
  SCK  → GPIO11 (Pin 23)
  MOSI → GPIO10 (Pin 19)
  MISO → GPIO9  (Pin 21)
  RST  → GPIO25 (Pin 22)
  3.3V → Pin 17
  GND  → Pin 25
"""

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

reader = SimpleMFRC522()

print("=" * 40)
print("  Test RC522 RFID")
print("  Acerca una tarjeta o tag NFC...")
print("  Ctrl+C para salir")
print("=" * 40)

try:
    while True:
        uid, text = reader.read_no_block()
        if uid:
            print(f"\n✅ Tag detectado!")
            print(f"   UID  : {uid}")
            print(f"   UID hex: {format(uid, 'X')}")
            if text and text.strip():
                print(f"   Texto: {text.strip()}")
            print("-" * 40)
            time.sleep(1.5)  # Evita lecturas duplicadas
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nSaliendo...")
finally:
    GPIO.cleanup()
