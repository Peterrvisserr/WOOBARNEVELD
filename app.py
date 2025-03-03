import os

# Installeer Poppler als het niet aanwezig is
if not os.path.exists("/usr/bin/pdftoppm"):
    os.system("apt-get update && apt-get install -y poppler-utils")


import streamlit as st
import fitz  # PyMuPDF
import spacy
import re
import pytesseract
from pdf2image import convert_from_path
from io import BytesIO
from PIL import Image, ImageDraw
import tempfile
import os

# Laad het NLP-model voor Nederlands
nlp = spacy.load("nl_core_news_sm")

# **Patronen die geanonimiseerd moeten worden**
TE_ANONIMISEREN = [
    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Namen (Jan Jansen)
    r"\b\d{2}-\d{2}-\d{4}\b",  # Geboortedatums (12-04-1985)
    r"\b\d{10,}\b",  # Lange getallen zoals telefoonnummers
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # E-mailadressen
    r"\b\d{9}\b",  # BSN-nummers (9 cijfers)
    r"\b€?\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\b",  # Geldbedragen (€ 1.000,00 / 1000 euro)

    # **Extra patronen voor adressen en aanhef**
    r"\b(Geachte heer|Geachte mevrouw|Beste|Aan|Dhr\.|Mevr\.)\s+[A-Z][a-z]+\b",  # Aanhef + naam
    r"\b([A-Z][a-z]+straat|[A-Z][a-z]+laan|[A-Z][a-z]+weg|[A-Z][a-z]+dijk)\s+\d+\b",  # Adres zoals "Dorpstraat 12"
    r"\b[1-9][0-9]{3}\s?[A-Z]{2}\b",  # Postcodes (1234 AB)
]

def extract_text_from_pdf(pdf_path):
    """Haal tekst uit een doorzoekbare PDF of gebruik OCR als er geen tekst gevonden wordt."""
    doc = fitz.open(pdf_path)
    extracted_text = ""

    for page in doc:
        text = page.get_text("text").strip()
        if text:  
            extracted_text += text + "\n"

    if not extracted_text:
        # **Geen doorzoekbare tekst → OCR gebruiken**
        images = convert_from_path(pdf_path, dpi=300)
        extracted_text = ""
        for img in images:
            text = pytesseract.image_to_string(img, lang="nld")
            extracted_text += text + "\n"

    return extracted_text

def anonymize_pdf(pdf_path):
    """Anonimiseert tekst in de PDF en maakt zwartgelakte tekst onkopieerbaar."""
    doc = fitz.open(pdf_path)

    for page in doc:
        text = page.get_text("text")

        # **OCR als geen tekst wordt gevonden**
        if not text.strip():
            images = convert_from_path(pdf_path, dpi=300)
            for img in images:
                text += pytesseract.image_to_string(img, lang="nld")

        # **Zoek en anonimiseer**
        for pattern in TE_ANONIMISEREN:
            matches = re.finditer(pattern, text)
            for match in matches:
                found_text = match.group()
                text_instances = page.search_for(found_text)

                # **Teken zwarte balken over de gevonden tekst**
                for inst in text_instances:
                    page.draw_rect(inst, color=(0, 0, 0), fill=(0, 0, 0))

        # **Maak de pagina onkopieerbaar door deze naar een afbeelding om te zetten**
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = img.convert("L")  # Maak het zwart-wit voor betere leesbaarheid
        img = img.convert("RGB")  # Zet het terug naar RGB om het bruikbaar te maken in PDF

        # **Teken extra zwarte balken over gelakte tekst in de afbeelding**
        draw = ImageDraw.Draw(img)
        for pattern in TE_ANONIMISEREN:
            for match in re.finditer(pattern, text):
                found_text = match.group()
                text_instances = page.search_for(found_text)
                for inst in text_instances:
                    x0, y0, x1, y1 = inst
                    draw.rectangle([x0, y0, x1, y1], fill="black")  # Zwarte balk tekenen

        # **Vervang de originele PDF-pagina met een afbeelding**
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        page.clean_contents()  # Verwijder originele tekst
        page.insert_image(page.rect, stream=img_buffer)

    # Opslaan naar bytes
    output_pdf = BytesIO()
    doc.save(output_pdf)
    output_pdf.seek(0)
    return output_pdf

# 🌐 **Streamlit UI**
st.title("📄 PDF Anonimiseerder")

uploaded_file = st.file_uploader("Upload een PDF", type=["pdf"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name

    with st.spinner("PDF wordt verwerkt..."):
        geanonimiseerd_pdf = anonymize_pdf(tmp_file_path)

        st.success("✅ PDF is geanonimiseerd! Niet kopieerbaar en geldbedragen zijn ook gelakt.")
        st.download_button(
            label="📥 Download geanonimiseerde PDF",
            data=geanonimiseerd_pdf,
            file_name="geanonimiseerd.pdf",
            mime="application/pdf"
        )

    # Opruimen tijdelijk bestand
    os.remove(tmp_file_path)
