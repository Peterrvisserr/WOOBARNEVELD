import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import spacy
import re
import subprocess
import os

# Modelnaam
model_name = "nl_core_news_sm"

# Controleer of het model geïnstalleerd is, zo niet: installeer het
try:
    nlp = spacy.load(model_name)
except OSError:
    st.warning("🔄 Downloading Spacy model... (eenmalig)")
    subprocess.run(["python3", "-m", "spacy", "download", model_name], check=True)
    nlp = spacy.load(model_name)

# Functie om tekst te anonimiseren
def anonymize_text(text):
    doc = nlp(text)

    # Regex patronen voor e-mail en telefoonnummers
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\b\d{2,4}[-.\s]?\d{6,8}\b'

    # Zoek entiteiten in de tekst
    entities_to_redact = {ent.text for ent in doc.ents if ent.label_ in ["PER", "ORG", "LOC"]}
    
    # Zoek naar e-mails en telefoonnummers
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)

    # Voeg alle gevonden gevoelige info samen
    entities_to_redact.update(emails)
    entities_to_redact.update(phones)

    # Vervang gevoelige gegevens met "[GEANONIMISEERD]"
    for entity in entities_to_redact:
        text = text.replace(entity, "[GEANONIMISEERD]")

    return text

# Functie om PDF te anonimiseren
def anonymize_pdf(pdf_path, output_path):
    doc = fitz.open(pdf_path)

    for page in doc:
        text = page.get_text("text")
        anonymized_text = anonymize_text(text)

        # Zoek en vervang de tekst in de PDF
        for entity in re.findall(r'\[GEANONIMISEERD\]', anonymized_text):
            for inst in page.search_for(entity):
                rect = inst
                page.add_redact_annot(rect, fill=(0, 0, 0))
        
        page.apply_redactions()

    doc.save(output_path)

# Streamlit interface
st.title("WOO-documenten Anonimiseren")

uploaded_file = st.file_uploader("Upload een PDF", type="pdf")

if uploaded_file is not None:
    input_pdf_path = "input.pdf"
    output_pdf_path = "geanonimiseerd.pdf"

    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.read())

    anonymize_pdf(input_pdf_path, output_pdf_path)

    with open(output_pdf_path, "rb") as f:
        st.download_button("Download Geanonimiseerde PDF", f, file_name="geanonimiseerd.pdf", mime="application/pdf")
