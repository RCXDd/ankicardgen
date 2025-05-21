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

def _parse_qna_from_llm_response(llm_response: str) -> tuple[str | None, str | None]:
    """Parses Question and Answer from LLM response. Expects 'Q: ...\nA: ...' format."""
    question = None
    answer = None
    lines = llm_response.strip().split('\n')
    
    for line in lines:
        if line.lower().startswith("q:"):
            question = line[2:].strip()
        elif line.lower().startswith("a:"):
            answer = line[2:].strip()
            break # Assume Q precedes A and we only want the first pair
    
    if question and answer:
        return question, answer
    return None, None # Return None if parsing fails

def _generate_qna_from_chunk_via_llm(client: OpenAI, text_chunk: str, model: str, anki_model_name: str) -> tuple[str | None, str | None]:
    """Generates a Q/A pair from a text chunk using LLM. Returns (question, answer) or (None, None)."""
    try:
        # Updated prompt to enforce German output
        prompt_template = f"""Analysiere den folgenden Text und erstelle eine prägnante Frage und eine passende Antwort auf DEUTSCH. Diese sind für eine Anki-Lernkartei mit den Feldnamen des Modells '{anki_model_name}' gedacht.
Antworte ausschließlich im folgenden Format:
Q: [Deine Frage auf Deutsch]
A: [Deine Antwort auf Deutsch]

Text: {{chunk}}"""
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte im Erstellen von Lernkarten. Alle von dir generierten Inhalte (Fragen und Antworten) MÜSSEN auf DEUTSCH sein. Erstelle präzise und korrekte Frage-Antwort-Paare auf DEUTSCH. Stelle sicher, dass Frage und Antwort unterschiedlich sind und ein logisches Paar zum Lernen bilden."
                },
                {
                    "role": "user", 
                    "content": prompt_template.format(chunk=text_chunk)
                }
            ],
            temperature=0.5 # Adjust for creativity vs. predictability
        )
        
        llm_response = completion.choices[0].message.content
        if llm_response:
            return _parse_qna_from_llm_response(llm_response)
        return None, None

    except Exception as e:
        click.echo(f"Warning: LLM request failed for a chunk: {e}", err=True)
        return None, None

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
                    'qfmt': '{{Question}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
                },
            ])

        anki_deck = genanki.Deck(
            deck_id=generate_unique_id(deck_name), # Unique ID for the deck
            name=deck_name
        )

        click.echo(f"Generating flashcards using Openrouter model: {model}...")
        successful_cards = 0
        for i, chunk in enumerate(chunks):
            click.echo(f"Processing chunk {i+1}/{len(chunks)}...", nl=False)
            question, answer = _generate_qna_from_chunk_via_llm(client, chunk, model, anki_model_name)
            if question and answer:
                note = genanki.Note(model=anki_card_model, fields=[question, answer])
                anki_deck.add_note(note)
                successful_cards += 1
                click.echo(" Card generated.")
            else:
                click.echo(" Failed to generate/parse card for this chunk.")
        
        if successful_cards == 0:
            click.echo("No flashcards were successfully generated. No .apkg file will be created.")
            return

        genanki_package = genanki.Package(anki_deck)
        # Ensure output file has .apkg extension
        if not output_file.lower().endswith(".apkg"):
            output_file += ".apkg"
            
        genanki_package.write_to_file(output_file)
        click.echo(f"\nSuccessfully generated {successful_cards} flashcards.")
        click.echo(f"Anki deck '{deck_name}' saved to: {os.path.abspath(output_file)}")

    except click.ClickException as e: 
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


if __name__ == '__main__':
    cli() 