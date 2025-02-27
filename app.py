import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import spacy
import re
import io
from PIL import Image, ImageDraw

# Laad het NLP-model
nlp = spacy.load("nl_core_news_sm")

# Functie om gevoelige informatie te anonimiseren
def anonymize_text(text):
    doc = nlp(text)

    # Definieer patronen voor e-mail en telefoon
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\b\d{2,4}[-.\s]?\d{6,8}\b'

    # Zoek naar namen, locaties en organisaties
    entities_to_redact = {ent.text for ent in doc.ents if ent.label_ in ["PER", "ORG", "LOC"]}
    
    # Zoek naar e-mails en telefoonnummers
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)

    # Combineer alles wat geanonimiseerd moet worden
    entities_to_redact.update(emails)
    entities_to_redact.update(phones)

    # Vervang de gevonden entiteiten met [GEANONIMISEERD]
    for entity in entities_to_redact:
        text = text.replace(entity, "[GEANONIMISEERD]")

    return text

# Functie om tekst te anonimiseren binnen de PDF
def anonymize_pdf(pdf_path, output_path):
    doc = fitz.open(pdf_path)

    for page in doc:
        text = page.get_text("text")
        anonymized_text = anonymize_text(text)

        # Zoek de woorden en vervang ze met zwarte balken
        for entity in re.findall(r'\[GEANONIMISEERD\]', anonymized_text):
            for inst in page.search_for(entity):
                rect = inst
                page.add_redact_annot(rect, fill=(0, 0, 0))
        
        # Voer de redactie uit
        page.apply_redactions()

    doc.save(output_path)

# Streamlit interface
st.title("WOO-documenten Anonimiseren")

uploaded_file = st.file_uploader("Upload een PDF", type="pdf")

if uploaded_file is not None:
    # Sla het geüploade bestand tijdelijk op
    input_pdf_path = "input.pdf"
    output_pdf_path = "geanonimiseerd.pdf"

    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.read())

    # Voer de anonimisering uit
    anonymize_pdf(input_pdf_path, output_pdf_path)

    # Toon downloadknop
    with open(output_pdf_path, "rb") as f:
        st.download_button("Download Geanonimiseerde PDF", f, file_name="geanonimiseerd.pdf", mime="application/pdf")
