#!/bin/bash
# ============================================================
#  FaPi - Script de instalación automática
#  RPi Zero 2 W + MAX98357A + KY040
# ============================================================

set -e  # Para si hay algún error

echo "================================================"
echo "  FaPi - Instalación del entorno"
echo "================================================"

# ── 1. Actualizar sistema ────────────────────────────────────
echo ""
echo "[1/6] Actualizando el sistema..."
sudo apt update -y && sudo apt upgrade -y

# ── 2. Instalar dependencias del sistema ─────────────────────
echo ""
echo "[2/6] Instalando dependencias del sistema..."
sudo apt install -y \
    python3-dev \
    python3-venv \
    gcc \
    vlc \
    python3-vlc \
    alsa-utils \
    ffmpeg

# ── 3. Configurar audio I2S (MAX98357A) ──────────────────────
echo ""
echo "[3/6] Configurando audio I2S para MAX98357A..."

CONFIG_FILE="/boot/firmware/config.txt"

# Deshabilitar audio por defecto si no está ya
if grep -q "^dtparam=audio=on" "$CONFIG_FILE"; then
    sudo sed -i 's/^dtparam=audio=on/dtparam=audio=off/' "$CONFIG_FILE"
    echo "  -> Audio por defecto deshabilitado"
fi

# Añadir overlay hifiberry-dac si no existe
if ! grep -q "dtoverlay=hifiberry-dac" "$CONFIG_FILE"; then
    echo "" | sudo tee -a "$CONFIG_FILE"
    echo "# MAX98357A I2S amplifier" | sudo tee -a "$CONFIG_FILE"
    echo "dtoverlay=hifiberry-dac" | sudo tee -a "$CONFIG_FILE"
    echo "  -> Overlay hifiberry-dac añadido"
else
    echo "  -> Overlay hifiberry-dac ya presente"
fi

# ── 4. Configurar volumen por software (softvol) ─────────────
echo ""
echo "[4/6] Configurando softvol en ALSA..."

ASOUND_FILE="/etc/asound.conf"

if [ ! -f "$ASOUND_FILE" ]; then
    sudo tee "$ASOUND_FILE" > /dev/null <<'EOF'
pcm.softvol {
    type softvol
    slave.pcm "hw:0,0"
    control {
        name "Master"
        card 0
    }
}

pcm.!default {
    type softvol
    slave.pcm "hw:0,0"
    control {
        name "Master"
        card 0
    }
}
EOF
    echo "  -> /etc/asound.conf creado"
else
    echo "  -> /etc/asound.conf ya existe, no se modifica"
fi

# ── 5. Crear entorno virtual Python e instalar librerías ─────
echo ""
echo "[5/6] Creando entorno virtual Python..."

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  -> Entorno virtual creado en $PROJECT_DIR/venv"
else
    echo "  -> Entorno virtual ya existe"
fi

source venv/bin/activate
pip install --upgrade pip
pip install RPi.GPIO python-vlc flask
deactivate

echo "  -> Librerías instaladas: RPi.GPIO, python-vlc"

# ── 6. Crear carpeta de audios ───────────────────────────────
echo ""
echo "[6/6] Creando estructura de carpetas..."
mkdir -p "$PROJECT_DIR/audios"
mkdir -p "$PROJECT_DIR/tmp"
echo "  -> Carpeta audios/ creada"

# ── Resumen final ────────────────────────────────────────────
echo ""
echo "================================================"
echo "  Instalación completada"
echo "================================================"
echo ""
echo "  Directorio del proyecto : $PROJECT_DIR"
echo "  Entorno virtual         : $PROJECT_DIR/venv"
echo "  Carpeta de audios       : $PROJECT_DIR/audios"
echo ""
echo "  Para activar el entorno:"
echo "    cd $PROJECT_DIR && source venv/bin/activate"
echo ""
echo "  IMPORTANTE: Se requiere reiniciar para que"
echo "  el overlay I2S tenga efecto."
echo ""
read -p "  ¿Reiniciar ahora? (s/n): " respuesta
if [[ "$respuesta" == "s" || "$respuesta" == "S" ]]; then
    sudo reboot
else
    echo "  Recuerda reiniciar antes de usar el proyecto."
fi
