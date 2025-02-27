import streamlit as st
import fitz  # PyMuPDF voor PDF-verwerking
import pytesseract  # OCR voor gescande PDF's
from pdf2image import convert_from_path  # Converteert PDF-pagina's naar afbeeldingen voor OCR
import spacy
import io
import os

# 🚀 **Laad het NLP-model vooraf**
try:
    nlp = spacy.load("nl_core_news_lg")
except OSError:
    st.error("Het Nederlandse taalmodel kon niet worden geladen. Controleer of het in requirements.txt staat.")

# 🎨 **Streamlit UI**
st.title("📄 PDF Anonimiseren")
st.write("Upload een PDF en download een geanonimiseerde versie.")

# 📤 **Upload een PDF-bestand**
uploaded_file = st.file_uploader("Kies een PDF-bestand", type="pdf")

# 🎯 **Functie om tekst uit PDF te halen (via OCR als nodig)**
def extract_text_from_pdf(pdf_path):
    text = ""
    pdf_document = fitz.open(pdf_path)

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text += page.get_text("text")

        if not text.strip():  # Gebruik OCR als er geen tekst is
            images = convert_from_path(pdf_path)
            for image in images:
                text += pytesseract.image_to_string(image, lang="nld")

    return text

# 🔒 **Functie om tekst te anonimiseren**
def anonymize_text(text):
    doc = nlp(text)
    anonymized_text = text
    for ent in doc.ents:
        anonymized_text = anonymized_text.replace(ent.text, "[REDACTED]")
    return anonymized_text

# ✍️ **Functie om een nieuwe PDF met geanonimiseerde tekst te maken**
def create_anonymized_pdf(original_pdf, anonymized_text):
    pdf_document = fitz.open(original_pdf)
    output_pdf = fitz.open()

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        new_page = output_pdf.new_page(width=page.rect.width, height=page.rect.height)

        new_page.insert_text((50, 50), anonymized_text, fontsize=10, color=(0, 0, 0))

    return output_pdf

# 🏁 **Verwerk de PDF als er een bestand is geüpload**
if uploaded_file:
    # 📜 **Bewaar geüploade PDF tijdelijk**
    temp_pdf_path = "/tmp/input.pdf"
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # 🔍 **Extract en anonimiseer tekst**
    extracted_text = extract_text_from_pdf(temp_pdf_path)
    anonymized_text = anonymize_text(extracted_text)

    # 📄 **Maak een nieuwe PDF met de geanonimiseerde tekst**
    anonymized_pdf = create_anonymized_pdf(temp_pdf_path, anonymized_text)
    
    # 💾 **Bewaar het als een bestand en geef downloadoptie**
    output_path = "/tmp/geanonimiseerd.pdf"
    anonymized_pdf.save(output_path)

    with open(output_path, "rb") as file:
        st.download_button("💾 Download Geanonimiseerde PDF", file, file_name="geanonimiseerd.pdf", mime="application/pdf")

    st.success("✅ Geanonimiseerde PDF gegenereerd!")

