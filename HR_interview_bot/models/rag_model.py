import fitz  # PyMuPDF for PDF handling
from transformers import AutoModelForCausalLM, AutoTokenizer
import io

# Load GPT-Neo model and tokenizer
model_name = "EleutherAI/gpt-neo-1.3B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def extract_text_from_pdf(pdf_input):
    """
    Extracts text from a PDF file.

    Args:
    - pdf_input: A file-like object or a file path (str).

    Returns:
    - str: Extracted text from the PDF.
    """
    import io

    if isinstance(pdf_input, str):  # If it's a file path (for local testing)
        with open(pdf_input, 'rb') as file:
            pdf_stream = io.BytesIO(file.read())
    else:  # If it's a file-like object (e.g., from Flask upload)
        pdf_input.seek(0)  # Reset the file pointer
        pdf_stream = io.BytesIO(pdf_input.read())

    text = ""
    with fitz.open(stream=pdf_stream, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()

    return text

def format_resume_text(resume_text):
    lines = resume_text.split("\n")
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if line.isupper() and len(line.split()) < 6:
            formatted_lines.append(f"\n\n### {line} ###\n")
        elif line:
            formatted_lines.append(line)

    return "\n".join(formatted_lines)

def extract_skills_using_ai(resume_text):
    prompt = f"""
    You are a highly intelligent resume parser. Your task is to extract the skills section from the following resume text. 
    Return only the text below the 'Skills' section. If the 'Skills' section is not found, return an empty string.

    Resume Text:
    {resume_text}
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=500)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.strip()

def process_resume(pdf_file):
    resume_text = extract_text_from_pdf(pdf_file)
    extracted_text = extract_skills_using_ai(resume_text)
    return extracted_text
    
