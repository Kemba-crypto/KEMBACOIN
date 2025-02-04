# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

import requests
import json
import PyPDF2
from docx import Document
import difflib
import os
from flask import Flask, request, jsonify
from ai_librarian import AILibrarian
from blockchain.transactions import LibraryTransaction

app = Flask(__name__)
ai_librarian = AILibrarian()

# Cloudinary configuration
CLOUDINARY_CLOUD_NAME = "your-cloud-name"
CLOUDINARY_API_KEY = "your-api-key"
CLOUDINARY_API_SECRET = "your-api-secret"
CLOUDINARY_UPLOAD_PRESET = "your-upload-preset"
CLOUDINARY_URL = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/upload"

@app.route('/process', methods=['POST'])
def process_content():
    data = request.json
    content = data.get('content')
    metadata = data.get('metadata', {})
    
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    try:
        updated_metadata = ai_librarian.process_content(content, metadata)
        return jsonify(updated_metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/train', methods=['POST'])
def train_model():
    data = request.json
    documents = data.get('documents', [])
    n_clusters = data.get('n_clusters', 5)
    
    if not documents:
        return jsonify({"error": "Documents are required for training"}), 400
    
    try:
        ai_librarian.train_model(documents, n_clusters)
        return jsonify({"message": "Model trained successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        # Upload file to Cloudinary
        response = requests.post(CLOUDINARY_URL, files={"file": file}, data={"upload_preset": CLOUDINARY_UPLOAD_PRESET})
        data = response.json()
        
        if "secure_url" not in data:
            return jsonify({"error": "Upload failed"}), 500

        file_url = data["secure_url"]
        metadata = extract_metadata_from_url(file_url)

        # Copyright and plagiarism checks
        if check_copyright_status(metadata):
            return jsonify({"status": "error", "message": "This document appears to be copyrighted."})
        
        if check_plagiarism(file_url):
            return jsonify({"status": "error", "message": "This document contains plagiarized content."})
        
        return jsonify({"status": "success", "message": "Document uploaded successfully.", "file_url": file_url})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Extract metadata from Cloudinary URL
def extract_metadata_from_url(file_url):
    metadata = {"author": None, "title": None, "keywords": None}
    
    file_path = file_url.split('/')[-1]
    if file_path.endswith('.pdf'):
        response = requests.get(file_url)
        with open("temp.pdf", 'wb') as f:
            f.write(response.content)
        
        with open("temp.pdf", 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            info = reader.metadata
            metadata["author"] = info.author if info else None
            metadata["title"] = info.title if info else None
            metadata["keywords"] = info.subject if info else None
    
    elif file_path.endswith('.docx'):
        response = requests.get(file_url)
        with open("temp.docx", 'wb') as f:
            f.write(response.content)
        
        doc = Document("temp.docx")
        core_props = doc.core_properties
        metadata["author"] = core_props.author
        metadata["title"] = core_props.title
        metadata["keywords"] = core_props.keywords
    
    return metadata

# Check copyright status using Google Books API
def check_copyright_status(metadata):
    title = metadata.get('title', '')
    author = metadata.get('author', '')
    google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author}"
    
    response = requests.get(google_books_url)
    if response.status_code == 200:
        data = response.json()
        return 'items' in data  # Returns True if a matching book is found
    return False

# Check plagiarism using difflib
def check_plagiarism(file_url):
    response = requests.get(file_url)
    document_content = response.text if response.status_code == 200 else ""
    
    sample_db = ["Sample copyrighted content", "Another text in the database", "Original material"]
    for text in sample_db:
        similarity = difflib.SequenceMatcher(None, document_content, text).ratio()
        if similarity > 0.8:
            return True
    return False

if __name__ == '__main__':
    app.run(debug=True)
