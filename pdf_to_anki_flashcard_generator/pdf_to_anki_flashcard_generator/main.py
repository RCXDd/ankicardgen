import click
import fitz  # PyMuPDF
import re

def segment_text_to_chunks(text: str, max_chars: int) -> list[str]:
    """Segments text into chunks of a maximum character length, trying to respect paragraphs."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue

        # If the paragraph itself fits, or if the current chunk is empty and the paragraph fits
        if len(current_chunk) + len(paragraph) + 2 <= max_chars or (not current_chunk and len(paragraph) <= max_chars):
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
        # If the paragraph is too long to add to the current chunk, or if it's too long on its own
        else:
            # Finalize the current_chunk if it has content
            if current_chunk:
                chunks.append(current_chunk)
            
            # Now deal with the oversized paragraph
            # If the paragraph itself is larger than max_chars, split it further
            if len(paragraph) > max_chars:
                # Simple split by sentences (basic regex, can be improved)
                sentences = re.split(r'(?<=[.!?])\s+', paragraph.replace('\n', ' '))
                temp_paragraph_chunk = ""
                for sentence in sentences:
                    if len(temp_paragraph_chunk) + len(sentence) + 1 <= max_chars:
                        if temp_paragraph_chunk:
                            temp_paragraph_chunk += " " + sentence
                        else:
                            temp_paragraph_chunk = sentence
                    else:
                        if temp_paragraph_chunk:
                            chunks.append(temp_paragraph_chunk)
                        # Handle very long sentences that exceed max_chars
                        if len(sentence) > max_chars:
                            # Force split the long sentence
                            for i in range(0, len(sentence), max_chars):
                                chunks.append(sentence[i:i+max_chars])
                            temp_paragraph_chunk = ""
                        else:
                            temp_paragraph_chunk = sentence
                if temp_paragraph_chunk: # Add any remaining part of the split paragraph
                    chunks.append(temp_paragraph_chunk)
                current_chunk = "" # Reset current_chunk after processing a large paragraph
            else:
                current_chunk = paragraph # Start a new chunk with this paragraph

    if current_chunk: # Add the last chunk if it has content
        chunks.append(current_chunk)
    
    return chunks

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

@cli.command(name="process-pdf")
@click.argument('pdf_path', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option('--max-chars-per-chunk', default=2000, show_default=True, help='Maximum characters per text chunk.')
def process_pdf(pdf_path: str, max_chars_per_chunk: int):
    """Processes a PDF file, extracts text, and segments it into chunks.

    PDF_PATH: The path to the PDF file to process.
    """
    try:
        doc = fitz.open(pdf_path)
        extracted_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            extracted_text += page.get_text()

        if not extracted_text.strip():
            click.echo(f"No text found in {pdf_path}. It might be an image-only PDF or empty.")
            return

        chunks = segment_text_to_chunks(extracted_text, max_chars_per_chunk)

        if not chunks:
            click.echo("No text chunks could be generated.")
            return

        click.echo(f"--- Extracted {len(chunks)} Chunks ---")
        for i, chunk_text in enumerate(chunks):
            click.echo(f"\n--- Chunk {i+1}/{len(chunks)} (Length: {len(chunk_text)}) ---")
            click.echo(chunk_text)

    except Exception as e:
        click.echo(f"Error processing PDF {pdf_path}: {e}", err=True)

if __name__ == '__main__':
    cli() 