#!/bin/bash

# Nombre del entorno virtual
ENV_DIR="spotify_venv"

# Verifica si el entorno virtual ya existe
if [ ! -d "$ENV_DIR" ]; then
  echo "🚀 Entorno virtual no encontrado. Creando el entorno..."
  python3 -m venv $ENV_DIR
  
  echo "📦 Activando entorno virtual..."
  source $ENV_DIR/bin/activate
  
  echo "📥 Instalando dependencias..."
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "🔍 Entorno virtual encontrado. Activando el entorno..."
  source $ENV_DIR/bin/activate
fi

echo "🔥 Ejecutando la aplicación Flask..."
python app.py