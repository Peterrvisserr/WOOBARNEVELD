import streamlit as st
import fitz  # PyMuPDF voor PDF-verwerking
import pytesseract
from pdf2image import convert_from_path
import spacy
import re
from io import BytesIO

# Laad het SpaCy model
try:
    nlp = spacy.load("nl_core_news_sm")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "nl_core_news_sm"])
    nlp = spacy.load("nl_core_news_sm")

# Functie om tekst uit PDF te halen
def extract_text_from_pdf(pdf_path):
    text = ""
    images = convert_from_path(pdf_path)

    for image in images:
        text += pytesseract.image_to_string(image, lang="nld") + "\n"

    return text

# Functie om gevoelige gegevens te detecteren en lakken
def anonymize_text(text):
    doc = nlp(text)
    
    entities_to_redact = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "FAC"]:  # Meer categorieën toegevoegd
            entities_to_redact.append(ent.text)

    # Extra patronen voor contactgegevens, adressen en geboortedatum
    patterns = [
        r"\b[A-Za-z]+\s[A-Za-z]+\b",  # Namen (Voornaam + Achternaam)
        r"\b\d{2}-\d{2}-\d{4}\b",  # Geboortedata in DD-MM-YYYY formaat
        r"\b\d{10}\b",  # Nederlandse telefoonnummers (10 cijfers)
        r"\b\d{4}\s?[A-Z]{2}\b",  # Nederlandse postcode
        r"\b[A-Za-z]+straat\b",  # Straatnamen zoals "Hoofdstraat"
        r"\b[A-Za-z]+weg\b",  # Wegen zoals "Rijksweg"
        r"\b[A-Za-z]+laan\b",  # Laan zoals "Julianalaan"
        r"\b[A-Za-z]+plein\b"  # Plein zoals "Raadhuisplein"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        entities_to_redact.extend(matches)

    # Vervang de gevonden entiteiten door "████████"
    for entity in set(entities_to
