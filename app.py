import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import io

app = Flask(__name__)
CORS(app)

# 1. This tells the server to show your HTML page when people visit the URL
@app.route('/')
def home():
    return send_file('index.html')

# 2. This is the API that processes the PDF
@app.route('/api/clean-pdf', methods=['POST'])
def clean_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "File must be a PDF"}), 400

    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        
        labels = reader.page_labels
        
        if not labels:
            return jsonify({"error": "No logical page labels found. This tool requires progressive presentation PDFs (like LaTeX Beamer)."}), 400
            
        pages_to_keep = []
        
        for i in range(len(reader.pages)):
            if i == len(reader.pages) - 1:
                pages_to_keep.append(i)
            else:
                if labels[i] != labels[i + 1]:
                    pages_to_keep.append(i)
                    
        for p in pages_to_keep:
            writer.add_page(reader.pages[p])
            
        output_pdf = io.BytesIO()
        writer.write(output_pdf)
        output_pdf.seek(0)
        
        return send_file(
            output_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='cleaned_handout.pdf'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)