import hashlib
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import joblib  # For model persistence
from blockchain.transactions import LibraryTransaction  # Importing the LibraryTransaction class

# Configure logging
logging.basicConfig(level=logging.INFO)

class AILibrarian:
    def __init__(self):
        """
        Initialize the AI Librarian with a vectorizer and clustering model.
        """
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.model = None  # Placeholder for the clustering model

    def hash_content(self, content):
        """
        Generate a SHA-256 hash for the content.

        :param content: The content to hash
        :return: The hash value as a hex string
        """
        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            return content_hash
        except Exception as e:
            logging.error(f"Error hashing content: {e}")
            raise

    def train_model(self, documents, n_clusters=5):
        """
        Train a KMeans model to categorize content into clusters.

        :param documents: List of textual documents
        :param n_clusters: Number of clusters/categories
        """
        if not documents or len(documents) == 0:
            logging.error("No documents provided for training.")
            raise ValueError("Document list is empty.")

        try:
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            self.model = KMeans(n_clusters=n_clusters, random_state=42)
            self.model.fit(tfidf_matrix)
            logging.info("AI Librarian model successfully trained for categorization.")
        except Exception as e:
            logging.error(f"Error during model training: {e}")
            raise

    def save_model(self, model_path):
        """
        Save the trained model to a file.

        :param model_path: Path to save the model
        """
        try:
            joblib.dump({"model": self.model, "vectorizer": self.vectorizer}, model_path)
            logging.info(f"Model and vectorizer saved to {model_path}.")
        except Exception as e:
            logging.error(f"Error saving model: {e}")
            raise

    def load_model(self, model_path):
        """
        Load a trained model from a file.

        :param model_path: Path to the model file
        """
        try:
            data = joblib.load(model_path)
            self.model = data["model"]
            self.vectorizer = data["vectorizer"]
            logging.info(f"Model and vectorizer loaded from {model_path}.")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise

    def categorize_content(self, content):
        """
        Categorize content using the trained model.

        :param content: Text content to categorize
        :return: Predicted category index
        """
        if not self.model:
            logging.error("AI model is not trained or loaded.")
            raise ValueError("AI model is not trained or loaded.")

        try:
            vectorized_content = self.vectorizer.transform([content])
            category = self.model.predict(vectorized_content)[0]
            logging.info(f"Content categorized into cluster {category}.")
            return category
        except Exception as e:
            logging.error(f"Error categorizing content: {e}")
            raise

    def process_content(self, content, metadata):
        """
        Hash and categorize content, returning updated metadata, and ensure proper transaction creation.

        :param content: The content to process
        :param metadata: Existing metadata for the content
        :return: Updated metadata with hash and category
        """
        try:
            content_hash = self.hash_content(content)
            category = self.categorize_content(content)
            metadata.update({
                "hash": content_hash,
                "category": category,
            })
            logging.info(f"Content processed successfully. Metadata updated.")
            
            # Optionally, create a library transaction if this content is to be uploaded
            fee_kemites = 100  # Example fee, adapt as needed
            lib_tx = LibraryTransaction(uploader="some_address", 
                                        title=metadata.get("title"), 
                                        hash_value=content_hash, 
                                        category=category, 
                                        fee_kemites=fee_kemites)
            logging.info("Library transaction created successfully.")
            
            return metadata
        except Exception as e:
            logging.error(f"Error processing content: {e}")
            raise

