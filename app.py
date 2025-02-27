import streamlit as st
import fitz  # PyMuPDF
import pytesseract
import spacy
import re
import os
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import io

# Laad Nederlands taalmodel
model_name = "nl_core_news_lg"
try:
    nlp = spacy.load(model_name)
except OSError:
    import subprocess
    subprocess.run(["python3", "-m", "spacy", "download", model_name], check=True)
    nlp = spacy.load(model_name)

# Regex-patronen voor extra anonimisatie
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"\b(?:\+31|0)(6\d{8}|\d{2}-\d{7}|\d{3}-\d{6})\b"

# Functie om tekst te anonimiseren
def anonymize_text(text):
    doc = nlp(text)
    anonymized_text = text

    # Anonimiseer entiteiten (namen, locaties, organisaties)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "GPE", "ORG", "LOC"]:  # Personen, plaatsen, organisaties
            anonymized_text = anonymized_text.replace(ent.text, "[GEANONIMISEERD]")

    # Verwijder e-mails en telefoonnummers met regex
    anonymized_text = re.sub(EMAIL_REGEX, "[EMAIL]", anonymized_text)
    anonymized_text = re.sub(PHONE_REGEX, "[TELEFOON]", anonymized_text)

    return anonymized_text

# Functie om tekst uit een PDF te halen (OCR + standaard tekstherkenning)
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_text = ""

    for page in doc:
        text = page.get_text("text")
        if not text.strip():  # Als geen tekst gevonden, gebruik OCR
            image = convert_from_path(pdf_path, first_page=page.number + 1, last_page=page.number + 1)[0]
            text = pytesseract.image_to_string(image, lang="nld")
        extracted_text += text + "\n"

    return extracted_text

# Functie om geanonimiseerde tekst terug in PDF te zetten
def save_anonymized_pdf(original_pdf, anonymized_text, output_pdf):
    doc = fitz.open(original_pdf)
    output_doc = fitz.open()

    for i, page in enumerate(doc):
        new_page = output_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_text((50, 50), anonymized_text, fontsize=11, color=(0, 0, 0))

    output_doc.save(output_pdf)
    output_doc.close()

# Streamlit interface
st.title("📄 PDF Anonimiseerder")
st.write("Upload een PDF en ontvang een geanonimiseerde versie.")

uploaded_file = st.file_uploader("Upload een PDF-bestand", type=["pdf"])
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_file.read())
        temp_pdf_path = temp_pdf.name

    st.write("**Stap 1: Tekst extractie...**")
    extracted_text = extract_text_from_pdf(temp_pdf_path)
    st.write("**Stap 2: Anonimiseren...**")
    anonymized_text = anonymize_text(extracted_text)

    output_pdf_path = temp_pdf_path.replace(".pdf", "_geanonimiseerd.pdf")
    save_anonymized_pdf(temp_pdf_path, anonymized_text, output_pdf_path)

    st.write("**Geanonimiseerde PDF klaar!** ✅")
    with open(output_pdf_path, "rb") as file:
        st.download_button("📥 Download geanonimiseerde PDF", file, "geanonimiseerd.pdf", "application/pdf")
