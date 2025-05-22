from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
import tempfile
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/process-pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file format. Only PDF files are allowed.'}), 400
    
    # Get form parameters
    deck_name = request.form.get('deckName', 'Generated Anki Deck')
    max_chars = request.form.get('maxChars', '1800')
    
    # Generate unique filenames
    unique_id = str(uuid.uuid4())
    pdf_filename = secure_filename(f"{unique_id}_{file.filename}")
    output_filename = f"{unique_id}_output.apkg"
    
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)
    
    # Save uploaded PDF
    file.save(pdf_path)
    
    try:
        # Build the command
        command = [
            "poetry", "run", "ankicardgen", "process-pdf-to-anki", 
            pdf_path,
            "--output-file", output_path,
            "--deck-name", deck_name,
            "--max-chars-per-chunk", max_chars
        ]
        
        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if output file was created
        if not os.path.exists(output_path):
            return jsonify({
                'error': 'Failed to generate Anki deck',
                'output': result.stdout,
                'error_output': result.stderr
            }), 500
        
        # Return the file for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{deck_name}.apkg",
            mimetype='application/octet-stream'
        )
    
    except subprocess.CalledProcessError as e:
        return jsonify({
            'error': 'Process failed',
            'output': e.stdout,
            'error_output': e.stderr
        }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up temporary files
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(output_path):
            os.remove(output_path)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 