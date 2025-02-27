import streamlit as st
import fitz  # PyMuPDF voor PDF-verwerking
import spacy  # NLP voor naamherkenning
import re
from io import BytesIO

# **Laad het NLP-model voor Nederlands**
@st.cache_resource
def load_nlp_model():
    return spacy.load("nl_core_news_sm")

nlp = load_nlp_model()

# **Regex patronen voor gevoelige informatie (exclusief gewone datums)**
TE_ANONIMISEREN = [
    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Namen (bijv. "Jan Jansen")
    r"\b\d{2}-\d{2}-\d{4}\b",  # Datums (bijv. 12-04-2025) → Alleen geboortedata worden straks gefilterd
    r"\b\d{2}/\d{2}/\d{4}\b",  # Datums met slash (12/04/2025)
    r"\b06[-\s]?\d{8}\b",  # Mobiele nummers (06-12345678 of 06 12345678)
    r"\b[1-9][0-9]{3}\s?[A-Z]{2}\b",  # Postcodes (bijv. 1234 AB)
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # E-mailadressen
    r"\b\d{9}\b",  # Mogelijke BSN-nummers (9 cijfers)

    # **Nieuwe patronen voor adres en aanhef**
    r"\b(Geachte heer|Geachte mevrouw|Beste|Aan|Dhr\.|Mevr\.)\s+[A-Z][a-z]+\b",  # Aanhef + naam
    r"\b([A-Z][a-z]+straat|[A-Z][a-z]+laan|[A-Z][a-z]+weg|[A-Z][a-z]+dijk)\s+\d+\b",  # Adressen zoals "Dorpstraat 12"
    
    # **Herkenning van opdrachtgevers en werkgevers**
    r"\b(Opdrachtgever|Werkgever|Bedrijf|Contactpersoon):?\s+[A-Z][a-z]+\b",  # "Opdrachtgever: Jansen BV"
]

def is_geboortedatum(text):
    """Checkt of een gevonden datum een geboortedatum is (leeftijdsindicatie < 100 jaar)."""
    match = re.match(r"\b(\d{2})[-/](\d{2})[-/](\d{4})\b", text)
    if match:
        dag, maand, jaar = map(int, match.groups())
        if 1900 <= jaar <= 2025 and jaar <= 2025 - 100:  # Waarschijnlijke geboortedatum
            return True
    return False

# **Functie om tekst in de PDF te anonimiseren**
def anonymize_pdf(pdf_bytes):
    """Verwerkt een PDF en anonimiseert gevoelige informatie door zwarte balken te plaatsen."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    for page in doc:
        text = page.get_text("text")

        # **Verwerk NLP-gegevens voor entiteiten**
        doc_nlp = nlp(text)
        ents_to_redact = set()

        for ent in doc_nlp.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "FAC"]:
                ents_to_redact.add(ent.text)
            elif ent.label_ == "DATE" and is_geboortedatum(ent.text):
                ents_to_redact.add(ent.text)  # Alleen geboortedata lakken

        # **Zoek extra patronen via regex**
        for pattern in TE_ANONIMISEREN:
            matches = re.finditer(pattern, text)
            for match in matches:
                ents_to_redact.add(match.group())

        # **Teken zwarte balken over alle gevonden entiteiten**
        for found_text in ents_to_redact:
            text_instances = page.search_for(found_text)
            for inst in text_instances:
                page.add_redact_annot(inst, fill=(0, 0, 0))  # Zwarte balk
                page.apply_redactions()

    # **Opslaan naar bytes**
    output_pdf = BytesIO()
    doc.save(output_pdf)
    output_pdf.seek(0)
    return output_pdf

# **🌐 Streamlit UI**
st.title("📄 PDF Anonimiseerder")

uploaded_file = st.file_uploader("Upload een PDF", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("📄 PDF wordt verwerkt..."):
        geanonimiseerd_pdf = anonymize_pdf(uploaded_file.read())

        st.success("✅ PDF is geanonimiseerd!")

        # **Downloadknop voor geanonimiseerde PDF**
        st.download_button(
            label="📥 Download geanonimiseerde PDF",
            data=geanonimiseerd_pdf,
            file_name="geanonimiseerd.pdf",
            mime="application/pdf"
        )
