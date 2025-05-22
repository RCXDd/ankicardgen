#!/bin/bash

# Setze Working Directory
cd "$(dirname "$0")"

# Installiere Python-Abhängigkeiten
echo "Installiere Python-Abhängigkeiten..."
pip install -r requirements.txt

# Installiere Node.js-Abhängigkeiten, falls nötig
if [ ! -d "node_modules" ]; then
  echo "Installiere Node.js-Abhängigkeiten..."
  npm install
fi

# Starte Backend-Server im Hintergrund
echo "Starte Backend-Server..."
python api.py &
BACKEND_PID=$!

# Warte kurz, damit der Backend-Server starten kann
sleep 2

# Starte Frontend-Server
echo "Starte Frontend-Server..."
npm run dev

# Cleanup beim Beenden
function cleanup {
  echo "Beende Server..."
  kill $BACKEND_PID
  exit 0
}

# Registriere Cleanup-Funktion für SIGINT (Ctrl+C)
trap cleanup SIGINT

# Warte auf Frontend-Prozess
wait 