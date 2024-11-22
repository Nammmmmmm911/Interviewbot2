import chromadb
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from models.rag_model import process_resume  # Ensure this import is correct
# Initialize ChromaDB Client
chroma_client = chromadb.Client()

# Get or create the collection
collection_name = "company_data"
collection = chroma_client.get_or_create_collection(collection_name)

def get_best_job_match(pdf_file):
    """
    Finds the most suitable job role by comparing extracted resume text with job descriptions in ChromaDB.
    
    Args:
    - pdf_file (file-like object or file path): The resume PDF to extract text from.

    Returns:
    - dict: Dictionary containing the best job title and similarity score.
    """
    # Use the process_resume function from rag_model.py to get the extracted text
    extracted_text = process_resume(pdf_file)  # This will give us the 'extracted_text'

# Function to calculate cosine similarity
def get_cosine_similarity(vector1, vector2):
    """Calculate the cosine similarity between two vectors."""
    return cosine_similarity([vector1], [vector2])[0][0]

def get_best_job_match(extracted_text):
    """
    Finds the most suitable job role by comparing extracted resume text with job descriptions in ChromaDB.
    
    Args:
    - extracted_text (str): Text extracted from the resume.

    Returns:
    - dict: Dictionary containing the best job title and similarity score.
    """
    # Retrieve all job descriptions and their metadata from ChromaDB
    results = collection.get(include=["documents", "metadatas", "ids"])
    job_titles = [metadata["jobTitle"] for metadata in results["metadatas"]]
    job_descriptions = results["documents"]

    # Vectorizing extracted resume text and job descriptions
    vectorizer = TfidfVectorizer(stop_words='english')
    all_documents = [extracted_text] + job_descriptions  # Add extracted resume text as the first document
    tfidf_matrix = vectorizer.fit_transform(all_documents)

    # Compute cosine similarity between extracted resume and job descriptions
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Get the best match based on highest similarity
    best_match_idx = np.argmax(cosine_similarities)
    best_job_title = job_titles[best_match_idx]
    best_similarity = cosine_similarities[best_match_idx]

    return {"job_title": best_job_title, "similarity": best_similarity}

