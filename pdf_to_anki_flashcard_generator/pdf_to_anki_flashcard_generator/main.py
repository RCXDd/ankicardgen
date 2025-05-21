import click
import fitz  # PyMuPDF
import re
import os
import random # For generating unique IDs
import time # For generating unique IDs
from openai import OpenAI
from dotenv import load_dotenv
import genanki # Added for Anki deck generation

# Helper function to initialize OpenAI client for Openrouter
def get_openrouter_client():
    load_dotenv() 
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    if not api_key:
        raise click.ClickException("OPENROUTER_API_KEY not found in .env file or environment variables.")
    return OpenAI(api_key=api_key, base_url=base_url)

# Helper function to generate a somewhat unique ID for decks/models
def generate_unique_id(name: str) -> int:
    # Simple hash combined with timestamp for more uniqueness
    name_hash = sum(ord(c) for c in name)
    timestamp_component = int(time.time() * 1000) % 100000 # Use milliseconds part
    return abs(name_hash + timestamp_component + random.randint(100000, 999999))

def segment_text_to_chunks(text: str, max_chars: int) -> list[str]:
    """Segments text into chunks, trying to respect paragraphs and then sentences."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph_stripped = paragraph.strip()
        if not paragraph_stripped:
            continue

        # If current_chunk is empty and paragraph fits, or if paragraph can be added
        if (not current_chunk and len(paragraph_stripped) <= max_chars) or \
           (current_chunk and len(current_chunk) + len("\n\n") + len(paragraph_stripped) <= max_chars):
            if current_chunk:
                current_chunk += "\n\n" + paragraph_stripped
            else:
                current_chunk = paragraph_stripped
        else:
            # Finalize current_chunk if it has content
            if current_chunk:
                chunks.append(current_chunk)
            
            # Now deal with the paragraph that doesn't fit or is too long on its own
            if len(paragraph_stripped) > max_chars:
                # Split oversized paragraph by sentences
                # A more robust sentence splitter might be needed for complex texts
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', paragraph_stripped.replace('\n', ' '))
                temp_sentence_chunk = ""
                for sentence in sentences:
                    sentence_stripped = sentence.strip()
                    if not sentence_stripped:
                        continue
                    
                    if (not temp_sentence_chunk and len(sentence_stripped) <= max_chars) or \
                       (temp_sentence_chunk and len(temp_sentence_chunk) + len(" ") + len(sentence_stripped) <= max_chars):
                        if temp_sentence_chunk:
                            temp_sentence_chunk += " " + sentence_stripped
                        else:
                            temp_sentence_chunk = sentence_stripped
                    else:
                        if temp_sentence_chunk:
                            chunks.append(temp_sentence_chunk)
                        
                        # If a single sentence is still too long, force split it
                        if len(sentence_stripped) > max_chars:
                            for i in range(0, len(sentence_stripped), max_chars):
                                chunks.append(sentence_stripped[i:i+max_chars])
                            temp_sentence_chunk = "" # Reset after force split
                        else:
                            temp_sentence_chunk = sentence_stripped # Start new chunk with this sentence
                
                if temp_sentence_chunk: # Add any remaining part from sentence splitting
                    chunks.append(temp_sentence_chunk)
                current_chunk = "" # Oversized paragraph processed, reset current_chunk
            else:
                 # The paragraph itself becomes the new current_chunk (it was too big to append but fits on its own)
                current_chunk = paragraph_stripped

    if current_chunk: # Add the last chunk if it has content
        chunks.append(current_chunk)
    
    return chunks

def _parse_multiple_qna_from_llm_response(llm_response: str) -> list[tuple[str, str]]:
    """Parses multiple Question and Answer pairs from LLM response. 
    Returns a list of (question, answer) tuples.
    Also handles SKIP responses when a chunk is not suitable for flashcard creation."""
    
    # Check if the LLM decided to skip this chunk entirely
    if llm_response.upper().startswith("SKIP:"):
        skip_reason = llm_response[5:].strip()  # Extract reason after "SKIP:"
        click.echo(f" Skipping: {skip_reason}")
        return []  # Empty list indicates no cards were generated
    
    # Look for multiple card markers
    if "CARD " in llm_response.upper() and ("Q:" in llm_response or "A:" in llm_response):
        cards = []
        # Attempt to split by "CARD X:" pattern or similar
        card_blocks = re.split(r'CARD\s+\d+[:.]', llm_response)
        
        # If the split worked, process each card block
        if len(card_blocks) > 1:
            # First element might be empty or preamble
            card_blocks = [block for block in card_blocks if block.strip()]
            
            for block in card_blocks:
                q_match = re.search(r'(?:^|\n)Q:\s*(.*?)(?=\n[A]:|$)', block, re.DOTALL)
                a_match = re.search(r'(?:^|\n)A:\s*(.*?)(?=\n[Q]:|$)', block, re.DOTALL)
                
                if q_match and a_match:
                    question = q_match.group(1).strip()
                    answer = a_match.group(1).strip()
                    if question and answer:
                        cards.append((question, answer))
            
            if cards:
                return cards
    
    # Fallback to single card parsing if the above didn't work
    question = None
    answer = None
    lines = llm_response.strip().split('\n')
    
    for i, line in enumerate(lines):
        if line.lower().startswith("q:"):
            question = line[2:].strip()
        elif line.lower().startswith("a:"):
            answer = line[2:].strip()
            # If we found a Q/A pair, return it as a single card
            if question and answer:
                return [(question, answer)]
            break
    
    # No valid cards found
    return []

def _generate_multiple_qna_from_chunk_via_llm(client: OpenAI, text_chunk: str, model: str, anki_model_name: str) -> list[tuple[str, str]]:
    """Generates multiple Q/A pairs from a text chunk using LLM.
    Returns a list of (question, answer) tuples."""
    try:
        # Enhanced prompt for multiple card extraction with improved LaTeX instructions
        prompt_template = f"""Erstelle evidenzbasierte Karteikarten auf Deutsch zum folgenden Text über Algorithmen und Datenstrukturen.

WISSENSCHAFTLICHE BASIS & BEGRÜNDUNG:
- Der "Testing Effect" belegt, dass aktives Wissensabrufen die Gedächtnisleistung stärker fördert als passives Wiederholen
- Die "Kognitive Belastungstheorie" zeigt, dass atomare Inhalte (ein Konzept pro Karte) die intrinsische kognitive Belastung reduzieren
- "Spaced Repetition" und optimale Wiederholungsintervalle werden durch klare, eindeutige Fragen unterstützt
- Meta-Analysen belegen, dass explizite Frageformulierungen mit klaren Subjekten und Prädikaten den Abruferfolg steigern

WICHTIG - QUALITÄT UND ATOMARITÄT:
- Analysiere den Text und identifiziere einzelne, spezifische Konzepte, Fakten oder Definitionen
- Erstelle für JEDES relevante Konzept EINE separate Karteikarte (1-5 Karten pro Text)
- Jede Karte sollte EINEN atomaren Inhalt behandeln (genau ein Konzept, kein Vermischen)
- Achte darauf, dass jede Karte für sich stehen kann und vollständig ist

STRENGE FORMATTING-REGELN FÜR MATHEMATISCHE NOTATION:
- Mathematische Ausdrücke MÜSSEN in LaTeX-Syntax mit \( \) für inline oder \[ \] für display stehen: \(O(n^2)\)
- Wichtig: Verwende \(O(n)\) und NICHT O(n) für Big-O-Notation
- Stelle sicher, dass ALLE mathematischen Ausdrücke, Komplexitätsklassen, und Formeln von \( \) umschlossen sind
- Beispiele für korrekte Notation:
  * Richtig: Die Zeitkomplexität beträgt \(O(n^2)\)
  * Falsch: Die Zeitkomplexität beträgt O(n^2) (ohne \( \)-Zeichen)
  * Richtig: \(\Theta(n \log n)\) ist die Komplexität...
  * Richtig: Die Laufzeit ist in \(O(1)\)

NUR wenn der Text absolut KEINE brauchbaren Konzepte enthält:
SKIP: [Kurze Begründung, warum keine Karteikarte möglich ist]

PRÄZISE ANWEISUNGEN FÜR JEDE KARTEIKARTE:
1. EXPLIZITE FRAGE: Formuliere eine spezifische Frage mit klarem Subjekt und Prädikat
2. AKTIVER ABRUF: Die Frage muss aktives Wissen abrufen, nicht nur passives Erkennen ermöglichen
3. PRÄZISE ANTWORT: Die Antwort muss vollständig, aber ohne überflüssige Informationen sein
4. MATHEMATISCHE KLARHEIT: Verwende immer \(...\) für ALLE inline mathematischen Ausdrücke und \[...\] für ALLE display mathematischen Ausdrücke
5. ANWENDUNGSBEISPIEL: Bei abstrakteren Konzepten füge EIN kurzes Anwendungsbeispiel hinzu

AUSGABEFORMAT:
CARD 1:
Q: [Deine erste evidenzbasierte Frage auf Deutsch]
A: [Deine präzise Antwort auf Deutsch]

CARD 2:
Q: [Deine zweite evidenzbasierte Frage auf Deutsch]
A: [Deine präzise Antwort auf Deutsch]

Usw. für jedes Konzept, das du identifizierst (max. 5 Karten pro Text).

INPUT-TEXT:
{{chunk}}"""
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte für wissenschaftlich fundierte Lernmethoden und Gedächtnisforschung mit Spezialwissen in aktiver Wissensabruf-Praxis (Testing Effect), Spaced Repetition und kognitiver Belastungstheorie. Deine Aufgabe ist es, komplexe Informationen in mehrere atomare, evidenzbasierte Anki-Karteikarten zu zerlegen, die jeweils genau ein Konzept abdecken. Du erzeugst ausschließlich Karteikarten auf Deutsch für den Bereich Informatik/Algorithmen. Wichtig: Nutze für alle mathematischen Ausdrücke und Formeln die korrekte LaTeX-Syntax mit \\( und \\) für inline-Formeln oder \\[ und \\] für display-Formeln."
                },
                {
                    "role": "user", 
                    "content": prompt_template.format(chunk=text_chunk)
                }
            ],
            temperature=0.2 # Etwas höhere Temperatur für mehr Kreativität bei der Zerlegung
        )
        
        llm_response = completion.choices[0].message.content
        if llm_response:
            return _parse_multiple_qna_from_llm_response(llm_response)
        return []

    except Exception as e:
        click.echo(f"Warning: LLM request failed for a chunk: {e}", err=True)
        return []

@click.group()
def cli():
    """
    PDF-to-Anki Flashcard Generator
    A CLI tool to automatically convert PDF lecture scripts into Anki flashcards.
    """
    pass

@cli.command()
@click.option('--name', default='World', help='The person to greet.')
def hello(name: str):
    """Simple program that greets NAME."""
    click.echo(f"Hello {name}!")

@cli.command(name="process-pdf-to-anki")
@click.argument('pdf_path', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option('--output-file', default="output_deck.apkg", show_default=True, help='Name of the generated .apkg file.')
@click.option('--deck-name', default="Generated Anki Deck", show_default=True, help='Name of the Anki deck.')
@click.option('--model', default=os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-3.5-turbo"), show_default=True, help="The Openrouter model for card generation.")
@click.option('--max-chars-per-chunk', default=1800, show_default=True, help='Maximum characters per text chunk for LLM processing.')
@click.option('--anki-model-name', default='Basic (Simple Q&A)', show_default=True, help='Name for the Anki card model to be created.')
def process_pdf_to_anki(pdf_path: str, output_file: str, deck_name: str, model: str, max_chars_per_chunk: int, anki_model_name: str):
    """Processes a PDF, generates Q/A flashcards via LLM, and creates an .apkg Anki deck.

    PDF_PATH: The path to the PDF file to process.
    """
    try:
        client = get_openrouter_client()
        click.echo(f"Processing {pdf_path} to create Anki deck '{deck_name}'...")

        doc = fitz.open(pdf_path)
        extracted_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            extracted_text += page.get_text()

        if not extracted_text.strip():
            click.echo(f"No text found in {pdf_path}.")
            return

        chunks = segment_text_to_chunks(extracted_text, max_chars_per_chunk)
        if not chunks:
            click.echo("No text chunks could be generated.")
            return
        
        click.echo(f"Segmented PDF into {len(chunks)} chunks.")

        # Define Anki model (simple Q/A)
        # PRD F3: Kartentypen: "Frage/Antwort", "Cloze Deletion" - Starting with Q/A
        anki_card_model = genanki.Model(
            model_id=generate_unique_id(anki_model_name), # Unique ID for the model
            name=anki_model_name,
            fields=[
                {'name': 'Question'}, 
                {'name': 'Answer'}
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''
<div class="question">{{Question}}</div>
''',
                    'afmt': '''
<div class="question">{{Question}}</div>
<hr id="answer">
<div class="answer">{{Answer}}</div>
''',
                },
            ],
            css='''
.card {
    font-family: arial;
    font-size: 20px;
    text-align: left;
    color: black;
    background-color: white;
    padding: 20px;
}
.question {
    margin-bottom: 10px;
}
.answer {
    margin-top: 10px;
}
.MathJax {
    font-size: 115%;
}
''')

        anki_deck = genanki.Deck(
            deck_id=generate_unique_id(deck_name), # Unique ID for the deck
            name=deck_name
        )

        click.echo(f"Generating flashcards using Openrouter model: {model}...")
        total_cards_generated = 0
        skipped_chunks = 0
        failed_chunks = 0
        
        for i, chunk in enumerate(chunks):
            click.echo(f"Processing chunk {i+1}/{len(chunks)}...", nl=False)
            cards = _generate_multiple_qna_from_chunk_via_llm(client, chunk, model, anki_model_name)
            
            if cards:
                click.echo(f" Generated {len(cards)} cards.")
                for j, (question, answer) in enumerate(cards):
                    note = genanki.Note(model=anki_card_model, fields=[question, answer])
                    anki_deck.add_note(note)
                total_cards_generated += len(cards)
            else:
                # Entweder wurde der Chunk übersprungen (wird bereits in _parse_multiple_qna_from_llm_response ausgegeben)
                # oder es gab einen technischen Fehler
                if " Skipping: " not in str(click.get_text_stream('stdout')):
                    click.echo(" Failed to generate any cards for this chunk.")
                    failed_chunks += 1
                else:
                    skipped_chunks += 1
        
        if total_cards_generated == 0:
            click.echo("No flashcards were successfully generated. No .apkg file will be created.")
            return

        genanki_package = genanki.Package(anki_deck)
        # Ensure output file has .apkg extension
        if not output_file.lower().endswith(".apkg"):
            output_file += ".apkg"
            
        genanki_package.write_to_file(output_file)
        click.echo(f"\nErfolgreiche Verarbeitung:")
        click.echo(f"- {total_cards_generated} Karteikarten generiert")
        click.echo(f"- {skipped_chunks} Chunks übersprungen (da nicht karteikartenwürdig)")
        click.echo(f"- {failed_chunks} Chunks fehlgeschlagen (technische Fehler)")
        click.echo(f"- Anki-Deck '{deck_name}' gespeichert: {os.path.abspath(output_file)}")

    except click.ClickException as e: 
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


if __name__ == '__main__':
    cli() 