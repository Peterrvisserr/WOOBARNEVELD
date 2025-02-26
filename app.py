import spacy
import subprocess

# ✅ Controleer of het Spacy-model bestaat, zo niet, download het
try:
    nlp = spacy.load("nl_core_news_sm")
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", "nl_core_news_lg"])
    nlp = spacy.load("nl_core_news_lg")
import streamlit as st
import fitz  # PyMuPDF
import pytesseract
import spacy
from pdf2image import convert_from_path
import re

# ✅ Laad het NLP-model
nlp = spacy.load("nl_core_news_lg")

# ✅ Webinterface
st.title("🔒 WOO Anonimiser")

uploaded_file = st.file_uploader("📄 Upload een PDF", type="pdf")

if uploaded_file:
    with open("input.pdf", "wb") as f:
        f.write(uploaded_file.read())

    def extract_text_from_pdf(pdf_path):
        images = convert_from_path(pdf_path, dpi=300)
        extracted_text = ""
        for image in images:
            page_text = pytesseract.image_to_string(image, lang="nld")
            extracted_text += page_text + "\n"
        return extracted_text

    def anonymize_text(text):
        doc = nlp(text)
        anonymized_text = text
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "MONEY", "EMAIL", "PHONE", "DATE"]:
                anonymized_text = anonymized_text.replace(ent.text, "[ANONIEM]")
        return anonymized_text

    def anonymize_pdf(input_pdf, output_pdf):
        extracted_text = extract_text_from_pdf(input_pdf)
        anonymized_text = anonymize_text(extracted_text)
        doc = fitz.open(input_pdf)
        for page in doc:
            for word in ["Geachte", "Heer", "Mevrouw", "Beste", "[ANONIEM]"]:
                text_instances = page.search_for(word)
                for inst in text_instances:
                    page.add_redact_annot(inst, fill=(0, 0, 0))
            page.apply_redactions()
        doc.save(output_pdf)

    anonymize_pdf("input.pdf", "geanonimiseerd.pdf")
    with open("geanonimiseerd.pdf", "rb") as f:
        st.download_button("📥 Download geanonimiseerde PDF", f, file_name="geanonimiseerd.pdf")
