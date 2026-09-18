from flask import Flask, request, jsonify, send_file
from flask import send_from_directory
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import io

app = Flask(__name__)
# Enable CORS to allow your HTML frontend to communicate with this API
# even if they are hosted on different ports/domains during development
CORS(app) 

@app.route('/api/clean-pdf', methods=['POST'])
def clean_pdf():
    # 1. Check if a file was actually sent in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file was uploaded."}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file was selected."}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Uploaded file is not a PDF."}), 400

    try:
        # 2. Read the PDF directly from the uploaded memory stream
        reader = PdfReader(file)
        writer = PdfWriter()
        
        labels = reader.page_labels
        
        # Guardrail: Ensure logical page labels exist
        if not labels:
            return jsonify({
                "error": "This PDF does not contain logical page labels. The script cannot detect where slides begin and end. (Best used with LaTeX Beamer PDFs)."
            }), 400
            
        pages_to_keep = []
        
        # 3. Core Logic: Find the final frame of each slide
        for i in range(len(reader.pages)):
            if i == len(reader.pages) - 1:
                pages_to_keep.append(i)
            else:
                if labels[i] != labels[i + 1]:
                    pages_to_keep.append(i)
        
        # 4. Write preserved pages to a new PDF object
        for p in pages_to_keep:
            writer.add_page(reader.pages[p])
            
        # 5. Save the output to a virtual file in memory
        output_pdf = io.BytesIO()
        writer.write(output_pdf)
        output_pdf.seek(0)
        
        # 6. Send the file back to the browser for download
        return send_file(
            output_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='cleaned_handout.pdf'
        )

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": "An internal server error occurred while processing the PDF."}), 500

@app.route('/')
def home():
    # This serves your index.html file to visitors
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    # Start the Flask server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)