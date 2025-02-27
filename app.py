import streamlit as st
import fitz  # PyMuPDF
import spacy
import re
from io import BytesIO

# Laad het NLP-model voor Nederlands
nlp = spacy.load("nl_core_news_sm")

# Lijst met woorden en patronen die geanonimiseerd moeten worden
TE_ANONIMISEREN = [
    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Herkent namen (bijv. "Jan Jansen")
    r"\b\d{2}-\d{2}-\d{4}\b",  # Datums (bijv. 12-04-2025)
    r"\b\d{10,}\b",  # Lange getallen (zoals telefoonnummers)
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # E-mailadressen
    r"\b\d{9}\b",  # BSN-nummers (9 cijfers)
    
    # **Nieuwe patronen voor adres en aanhef**
    r"\b(Geachte heer|Geachte mevrouw|Beste|Aan|Dhr\.|Mevr\.)\s+[A-Z][a-z]+\b",  # Aanhef + naam
    r"\b([A-Z][a-z]+straat|[A-Z][a-z]+laan|[A-Z][a-z]+weg|[A-Z][a-z]+dijk)\s+\d+\b",  # Adres zoals "Dorpstraat 12"
    r"\b[1-9][0-9]{3}\s?[A-Z]{2}\b",  # Postcodes (bijv. 1234 AB)
]

def anonymize_pdf(pdf_bytes):
    """Verwerkt een PDF en anonimiseert gevoelige informatie door zwarte balken te plaatsen."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    for page in doc:
        text = page.get_text("text")

        # Zoek termen die geanonimiseerd moeten worden
        for pattern in TE_ANONIMISEREN:
            matches = re.finditer(pattern, text)
            for match in matches:
                found_text = match.group()
                text_instances = page.search_for(found_text)
                
                # Teken zwarte balken over de gevonden tekst
                for inst in text_instances:
                    page.draw_rect(inst, color=(0, 0, 0), fill=(0, 0, 0))

    # Opslaan naar bytes
    output_pdf = BytesIO()
    doc.save(output_pdf)
    output_pdf.seek(0)
    return output_pdf

# 🌐 **Streamlit UI**
st.title("📄 PDF Anonimiseerder")

uploaded_file = st.file_uploader("Upload een PDF", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("PDF wordt verwerkt..."):
        geanonimiseerd_pdf = anonymize_pdf(uploaded_file.read())

        st.success("✅ PDF is geanonimiseerd!")
        st.download_button(
            label="📥 Download geanonimiseerde PDF",
            data=geanonimiseerd_pdf,
            file_name="geanonimiseerd.pdf",
            mime="application/pdf"
        )
