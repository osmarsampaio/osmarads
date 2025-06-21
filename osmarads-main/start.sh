#!/bin/bash
# start.sh

echo "Criando diretório de uploads..."
mkdir -p uploads

echo "Iniciando o servidor..."
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:$PORT app:app --timeout 120
