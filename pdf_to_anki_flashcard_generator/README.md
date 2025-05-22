# PDF-to-Anki Flashcard Generator

Dieses Projekt bietet Tools zur automatischen Umwandlung von PDF-Vorlesungsnotizen in Anki-Karteikarten, mit Unterstützung durch KI.

## Funktionen

- Extrahiert Text aus PDF-Dateien
- Analysiert den Inhalt mit KI, um sinnvolle Fragen und Antworten zu generieren
- Erstellt ein komplettes Anki-Deck (.apkg), das direkt in Anki importiert werden kann
- Automatische Erkennung und Formatierung mathematischer Formeln mit LaTeX-Syntax
- Unterstützt große PDF-Dateien durch intelligente Textaufteilung

## Verwendung

### GUI (Grafische Benutzeroberfläche)

Die benutzerfreundlichste Art, das Tool zu verwenden:

1. Navigieren Sie zum `web_app` Verzeichnis
2. Führen Sie das Startskript aus:
   ```
   ./run.sh
   ```
   Oder starten Sie die Komponenten manuell (siehe README in web_app/)
3. Öffnen Sie http://localhost:3000 in Ihrem Browser
4. Laden Sie eine PDF-Datei hoch, passen Sie die Einstellungen an und verarbeiten Sie die Datei

### Kommandozeile (CLI)

Für fortgeschrittene Benutzer oder zur Automatisierung:

```bash
poetry run ankicardgen process-pdf-to-anki [PDF_DATEI] --output-file [AUSGABEDATEI] --deck-name [DECK_NAME] --max-chars-per-chunk [MAX_ZEICHEN]
```

Beispiel:
```bash
poetry run ankicardgen process-pdf-to-anki examples/data/Komplexität.pdf --output-file test_output.apkg --deck-name "Test Deck" --max-chars-per-chunk 1000
```

## Installation

### Voraussetzungen

- Python 3.12 oder höher
- Poetry (Python-Abhängigkeitsverwaltung)
- OpenRouter API-Schlüssel oder anderer API-Schlüssel für den LLM-Zugriff

### Schritte

1. Repository klonen:
   ```
   git clone [repository-url]
   cd pdf_to_anki_flashcard_generator
   ```

2. Abhängigkeiten installieren:
   ```
   poetry install
   ```

3. API-Schlüssel einrichten:
   Erstellen Sie eine `.env`-Datei im Hauptverzeichnis mit:
   ```
   OPENROUTER_API_KEY=Ihr_API_Schlüssel
   ```

## Weitere Informationen

Für detaillierte Informationen zur Web-Anwendung, siehe die [Web App README](web_app/README.md). 