import streamlit as st
import fitz  # PyMuPDF voor PDF-verwerking
import pytesseract  # OCR voor gescande PDF's
import spacy  # Natuurlijke taalverwerking
import re
import io
from PIL import Image

# Laad NLP-model voor Nederlandse taal
@st.cache_resource
def load_nlp_model():
    return spacy.load("nl_core_news_sm")

nlp = load_nlp_model()

# Regex patronen voor extra gevoelige info
extra_patterns = [
    r"\b\d{2}-\d{2}-\d{4}\b",  # Datums zoals 12-03-1985
    r"\b\d{2}/\d{2}/\d{4}\b",  # Datums zoals 12/03/1985
    r"\b\d{2}\s\w+\s\d{4}\b",  # Datums zoals 12 maart 1985
    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Volledige namen
    r"\b\d{4}\s?[A-Z]{2}\b",  # Nederlandse postcodes zoals 1234 AB
    r"\b06-\d{8}\b",  # Mobiele nummers zoals 06-12345678
    r"\b06\s\d{8}\b",
    r"\b\d{10}\b"  # Mogelijke telefoonnummers
]

# Functie om tekst te anonimiseren
def redact_text(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "LOC", "FAC"]:
            text = text.replace(ent.text, "[REDACTED]")

    for pattern in extra_patterns:
        text = re.sub(pattern, "[REDACTED]", text)

    return text

# **Wijziging: Haalt tekst direct uit PDF zonder pdf2image!**
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_text = ""

    for page in doc:
        text = page.get_text("text")
        extracted_text += text + "\n"

    doc.close()
    return extracted_text.strip()

# Anonimiseer PDF met zwarte balken
def anonymize_pdf(input_pdf_path, output_pdf_path):
    doc = fitz.open(input_pdf_path)

    for page in doc:
        text = page.get_text("text")
        redacted_text = redact_text(text)

        words = text.split()
        redacted_words = redacted_text.split()

        for i, word in enumerate(words):
            if redacted_words[i] == "[REDACTED]":
                areas = page.search_for(word)
                for area in areas:
                    page.add_redact_annot(area, fill=(0, 0, 0))

        page.apply_redactions()

    doc.save(output_pdf_path)
    doc.close()

# Streamlit UI
st.title("🔏 PDF Anonimiseren")

uploaded_file = st.file_uploader("Upload een PDF-bestand", type=["pdf"])

if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()
    input_pdf_path = "input.pdf"
    output_pdf_path = "geanonimiseerd.pdf"

    with open(input_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    st.write("📄 Extractie van tekst uit PDF...")
    extracted_text = extract_text_from_pdf(input_pdf_path)
    redacted_text = redact_text(extracted_text)

    st.write("🔍 Originele tekst:")
    st.text(extracted_text[:500])  # Preview van tekst

    st.write("🚫 Geanonimiseerde tekst:")
    st.text(redacted_text[:500])  # Preview van geanonimiseerde tekst

    st.write("🛠 Genereren van geanonimiseerde PDF...")
    anonymize_pdf(input_pdf_path, output_pdf_path)

    with open(output_pdf_path, "rb") as f:
        st.download_button("📥 Download geanonimiseerde PDF", f, file_name="geanonimiseerd.pdf", mime="application/pdf")
