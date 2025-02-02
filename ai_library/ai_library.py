# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  


from flask import Flask, request, jsonify
from ai_librarian import AILibrarian
from blockchain.transactions import LibraryTransaction

app = Flask(__name__)
ai_librarian = AILibrarian()

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

if __name__ == '__main__':
    app.run(debug=True)

