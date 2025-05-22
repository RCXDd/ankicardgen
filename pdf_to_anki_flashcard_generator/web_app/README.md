# Anki Karteikarten Generator - Web Interface

Diese Web-Anwendung bietet eine benutzerfreundliche Oberfläche für das `ankicardgen` Tool, mit dem PDF-Dateien in Anki-Karteikarten umgewandelt werden können.

## Funktionen

- PDF-Upload durch Drag & Drop oder Dateiauswahl
- Anpassbare Deck-Namen
- Einstellbare Textchunk-Größe für optimale Karteikarten-Generierung
- Automatischer Download des generierten Anki-Decks (.apkg)
- Echtzeit-Statusanzeige während der Verarbeitung

## Voraussetzungen

- Node.js (v16 oder höher)
- Python (v3.12 oder höher)
- Poetry (für die Backend-Komponente)
- Die `ankicardgen` CLI muss installiert und funktionsfähig sein

## Installation und Start

### Backend (Flask API)

1. Navigieren Sie zum `web_app` Verzeichnis:
   ```
   cd web_app
   ```

2. Installieren Sie die erforderlichen Python-Abhängigkeiten:
   ```
   pip install -r requirements.txt
   ```

3. Starten Sie den Flask-Server:
   ```
   python api.py
   ```
   Der Server läuft standardmäßig auf Port 5000.

### Frontend (Next.js)

1. Navigieren Sie zum `web_app` Verzeichnis (falls noch nicht dort):
   ```
   cd web_app
   ```

2. Installieren Sie die erforderlichen Node.js-Abhängigkeiten:
   ```
   npm install
   ```

3. Starten Sie den Entwicklungsserver:
   ```
   npm run dev
   ```
   Das Frontend läuft standardmäßig auf Port 3000.

4. Öffnen Sie Ihren Browser und navigieren Sie zu:
   ```
   http://localhost:3000
   ```

## Verwendung

1. Ziehen Sie eine PDF-Datei in den Upload-Bereich oder klicken Sie, um eine Datei auszuwählen.
2. Passen Sie den gewünschten Deck-Namen an (standardmäßig wird der Dateiname verwendet).
3. Stellen Sie die maximale Zeichenanzahl pro Textchunk ein.
4. Klicken Sie auf "PDF verarbeiten".
5. Warten Sie, während die Karteikarten generiert werden.
6. Nach Abschluss der Verarbeitung wird die .apkg-Datei automatisch heruntergeladen.
7. Importieren Sie die heruntergeladene .apkg-Datei in Anki.

## Fehlerbehebung

- Stellen Sie sicher, dass sowohl der Flask-Server (Backend) als auch der Next.js-Server (Frontend) ausgeführt werden.
- Überprüfen Sie, ob die `ankicardgen` CLI korrekt installiert ist und über die Poetry-Umgebung ausgeführt werden kann.
- Die maximale Upload-Größe für PDF-Dateien beträgt 50MB.
- Bei Problemen prüfen Sie die Konsolenausgaben beider Server.
