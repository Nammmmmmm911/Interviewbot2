from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os
import pandas as pd
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash  # Import for password hashing
from flask import Flask, request, jsonify
from chromadb import Client
import chromadb
import os
from werkzeug.utils import secure_filename
from langchain_openai import OpenAIEmbeddings
from models.rag_model import process_resume
from models.job_matching import get_best_job_match

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Namratha@9113*",
    database="hr_bot_db"
)

# Configure the upload folder
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize ChromaDB Client
chroma_client = chromadb.Client()

# Create or get the collection
collection_name = "company_data"
collection = chroma_client.get_or_create_collection(collection_name)

def load_company_data_to_chromadb(file_path):
    """Load company details from an Excel file into ChromaDB if not already loaded."""
    # Read the data from Excel
    df = pd.read_excel(file_path, usecols=["jobTitle", "jobUrl", "jobDescription"])

    # Fetch existing metadata to find already stored job titles
    existing_metadatas = collection.get(include=["metadatas"])["metadatas"]
    existing_ids = {metadata["jobTitle"] for metadata in existing_metadatas}

    # Insert data into ChromaDB only if it doesn't already exist
    new_records = 0
    for _, row in df.iterrows():
        if row["jobTitle"] not in existing_ids:  # Check if the jobTitle is already in the collection
            collection.add(
                documents=[row["jobDescription"]],  # Add the job description as the document
                metadatas=[{"jobTitle": row["jobTitle"], "jobUrl": row["jobUrl"]}],  # Add metadata
                ids=[row["jobTitle"]]  # Use jobTitle as a unique identifier
            )
            new_records += 1
            print(f"New record added: {row['jobTitle']}")  # Print newly added record

    if new_records == 0:
        print("No new records added, all records already exist.")
    else:
        print(f"{new_records} new records added to ChromaDB.")

# Route for Home
@app.route('/')
def home():
    return render_template('home.html')

# Route for Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, password))
        db.commit()
        return redirect(url_for('signin'))
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        print("POST request received for sign-in.")
        username = request.form['username']
        password = request.form['password']
        
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        
        if user:
            session['username'] = user[1]
            print("Redirecting to upload_resume")
            return redirect(url_for('upload_resume'))
        else:
            print("Invalid credentials")
            return "Invalid Credentials", 401
    print("GET request received for sign-in.")
    return render_template('signin.html')

@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        # Check if a file is part of the request
        if 'resume' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        resume_file = request.files['resume']
        
        # Ensure the file is provided and is a PDF
        if resume_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Save the file to the upload folder
        filename = secure_filename(resume_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(file_path)

        try:
            # Use the process_resume function to process the uploaded file
            extracted_text = process_resume(file_path)  # Pass the file path to the function
            # Instead of returning JSON, render the result in a template
            return render_template('result.html', extracted_text=extracted_text)  # Return the extracted text to be displayed on the page
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # If it's a GET request, render the upload resume form
    return render_template('upload_resume.html')  # Ensure you have this template

@app.route('/job_matching', methods=['GET'])
def job_matching():
    # Get extracted_text from session
    extracted_text = session.get('extracted_text', None)

    if extracted_text:
        # Perform job matching
        job_result = get_best_job_match(extracted_text)  # Pass the extracted text here
        return render_template('job_matching_form.html', job_result=job_result)
    else:
        return render_template('job_matching_form.html', job_result=None)

if __name__ == '__main__':
    print("Loading company data into ChromaDB...")
    load_company_data_to_chromadb('company_data.xlsx')  # Call it only once
    app.run(debug=True)
