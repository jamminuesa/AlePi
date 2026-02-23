#!/usr/bin/env python3
"""
player.py - Reproductor de audio con control KY040
Reproduce audio con VLC, controla volumen con el encoder
y play/pause con el botón. El pin SD del MAX98357A se controla
por GPIO para eliminar ruido en pause.

Conexiones KY040:
  CLK -> GPIO17 (Pin 11)
  DT  -> GPIO27 (Pin 13)
  SW  -> GPIO22 (Pin 15)
  VCC -> 3.3V   (Pin 1 o 17)
  GND -> GND    (Pin 9)

Conexiones MAX98357A:
  VIN  -> 5V      (Pin 2)
  GND  -> GND     (Pin 6)
  BCLK -> GPIO18  (Pin 12)
  LRC  -> GPIO19  (Pin 35)
  DIN  -> GPIO21  (Pin 40)
  SD   -> GPIO24  (Pin 18)  ← Control mute por software
  GAIN -> 3.3V    (Pin 1)   ← 9dB, o dejarlo flotante para 6dB
"""

import RPi.GPIO as GPIO
import vlc
import time
import os

# ── Pines ────────────────────────────────────────────────────
CLK = 17
DT  = 27
SW  = 22
SD  = 24  # Control mute del MAX98357A

# ── Configuración ────────────────────────────────────────────
AUDIO_FILE  = os.path.expanduser("~/FaPi/audios/uploader_-_Musica_Para_Dormir_Bebes_y_Animacion_Para_Calmar.m4a")
VOLUME      = 15    # Volumen inicial (0-100)
VOLUME_STEP = 1     # Cambio por tick del encoder

# ── Setup GPIO ───────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SD,  GPIO.OUT)
GPIO.output(SD, GPIO.LOW)  # Amplificador muteado al inicio

ultimo_clk = GPIO.input(CLK)

# ── Setup VLC ────────────────────────────────────────────────
instance = vlc.Instance("--aout=alsa", "--alsa-audio-device=default")
player   = instance.media_player_new()
media    = instance.media_new(AUDIO_FILE)
player.set_media(media)

# ── Funciones ────────────────────────────────────────────────
def set_volume(vol):
    vol = max(0, min(80, vol))
    player.audio_set_volume(vol)
    print(f"Volumen: {vol}%")
    return vol

def amp_mute(mute):
    """True = silencia el amplificador, False = activa"""
    GPIO.output(SD, GPIO.LOW if mute else GPIO.HIGH)

def toggle_play_pause():
    state = player.get_state()
    if state == vlc.State.Playing:
        amp_mute(True)
        time.sleep(0.05)
        player.pause()
        print("Pausado")
    elif state in (vlc.State.Paused, vlc.State.Stopped,
                   vlc.State.NothingSpecial, vlc.State.Ended):
        player.play()
        time.sleep(0.05)
        amp_mute(False)
        print("Reproduciendo...")

# ── Inicio ───────────────────────────────────────────────────
if not os.path.exists(AUDIO_FILE):
    print(f"ERROR: No se encuentra el archivo: {AUDIO_FILE}")
    GPIO.cleanup()
    exit(1)

set_volume(VOLUME)
player.play()
time.sleep(0.1)
amp_mute(False)

print("Gira el encoder para ajustar volumen.")
print("Pulsa el botón para play/pause.")
print("Ctrl+C para salir.")

# ── Bucle principal ──────────────────────────────────────────
try:
    while True:
        # Encoder - volumen
        clk = GPIO.input(CLK)
        if clk != ultimo_clk:
            time.sleep(0.002)
            if GPIO.input(DT) != clk:
                VOLUME += VOLUME_STEP
                print("→ Sube")
            else:
                VOLUME -= VOLUME_STEP
                print("← Baja")
            VOLUME = set_volume(VOLUME)
        ultimo_clk = clk

        # Botón - play/pause
        if GPIO.input(SW) == GPIO.LOW:
            toggle_play_pause()
            time.sleep(0.3)  # debounce

        time.sleep(0.001)

except KeyboardInterrupt:
    print("\nSaliendo...")
finally:
    amp_mute(True)
    player.stop()
    GPIO.cleanup()
