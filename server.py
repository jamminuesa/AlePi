#!/usr/bin/env python3
"""
server.py - Servidor web FaPi
Sirve la interfaz de gestión en http://<ip-rpi>:8000

Endpoints:
  GET  /               → Interfaz web
  GET  /api/audios     → Lista de audios disponibles
  POST /api/upload     → Subir nuevo audio
  DELETE /api/audio/<nombre> → Eliminar audio
  GET  /api/assignments      → Leer asignaciones NFC
  POST /api/save             → Guardar asignaciones NFC
"""

import os
import json
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# ── Configuración ────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
AUDIOS_DIR      = os.path.join(BASE_DIR, "audios")
WEB_DIR         = os.path.join(BASE_DIR, "web")
ASSIGNMENTS_FILE = os.path.join(BASE_DIR, "assignments.json")
TEMP_DIR        = os.path.join(BASE_DIR, "tmp")
ALLOWED_EXT     = {"mp3", "wav", "ogg", "m4a"}
PORT            = 8000

os.makedirs(AUDIOS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Redirigir archivos temporales a la SD en lugar de /tmp (RAM)
tempfile.tempdir = TEMP_DIR

app = Flask(__name__, static_folder=WEB_DIR)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1 GB máximo

# ── Helpers ──────────────────────────────────────────────────
def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def load_assignments():
    if os.path.exists(ASSIGNMENTS_FILE):
        with open(ASSIGNMENTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_assignments(data):
    with open(ASSIGNMENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── Rutas ────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(WEB_DIR, 'index.html')

@app.route('/api/audios', methods=['GET'])
def get_audios():
    files = []
    for f in sorted(os.listdir(AUDIOS_DIR)):
        if allowed(f):
            size = os.path.getsize(os.path.join(AUDIOS_DIR, f))
            files.append({"name": f, "size": size})
    return jsonify(files)

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No se recibió ningún archivo"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400
    if not allowed(file.filename):
        return jsonify({"error": "Formato no permitido. Usa MP3, WAV u OGG"}), 400

    filename = secure_filename(file.filename)
    dest = os.path.join(AUDIOS_DIR, filename)
    file.save(dest)
    # Limpiar archivos temporales residuales
    for f in os.listdir(TEMP_DIR):
        try:
            os.remove(os.path.join(TEMP_DIR, f))
        except:
            pass
    size = os.path.getsize(dest)
    return jsonify({"name": filename, "size": size}), 201

@app.route('/api/audio/<filename>', methods=['DELETE'])
def delete_audio(filename):
    filename = secure_filename(filename)
    path = os.path.join(AUDIOS_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Archivo no encontrado"}), 404
    os.remove(path)
    # Limpiar asignaciones que usaban este audio
    assignments = load_assignments()
    assignments = {uid: aud for uid, aud in assignments.items() if aud != filename}
    save_assignments(assignments)
    return jsonify({"ok": True})

@app.route('/api/assignments', methods=['GET'])
def get_assignments():
    return jsonify(load_assignments())

@app.route('/api/save', methods=['POST'])
def save():
    data = request.get_json()
    if not data or 'assignments' not in data:
        return jsonify({"error": "Datos inválidos"}), 400
    save_assignments(data['assignments'])
    return jsonify({"ok": True})

# ── Arranque ─────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"🎵 FaPi server arrancando en http://0.0.0.0:{PORT}")
    print(f"   Audios en  : {AUDIOS_DIR}")
    print(f"   Asignaciones: {ASSIGNMENTS_FILE}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
