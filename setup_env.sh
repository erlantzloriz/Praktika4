#!/usr/bin/env bash

set -e

VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Detectar Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "❌ Python no está instalado."
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creando entorno virtual '$VENV_DIR'..."
    $PYTHON_BIN -m venv "$VENV_DIR"
else
    echo "🔄 El entorno virtual '$VENV_DIR' ya existe."
fi

# Activar entorno virtual
source "$VENV_DIR/bin/activate"

# Actualizar herramientas base
python -m pip install --upgrade pip setuptools wheel

# Instalar dependencias
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "📥 Instalando dependencias desde '$REQUIREMENTS_FILE'..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "⚠️ No se encontró '$REQUIREMENTS_FILE'."
fi

echo "✅ Entorno virtual listo en '$VENV_DIR'"
echo "👉 Para activarlo manualmente:"
echo "source $VENV_DIR/bin/activate"