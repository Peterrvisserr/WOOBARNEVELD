import streamlit as st
import fitz  # PyMuPDF voor PDF verwerking
import spacy  # NLP voor naamherkenning
import re
from io import BytesIO

# **Laad het NLP-model voor Nederlands**
@st.cache_resource
def load_nlp_model():
    return spacy.load("nl_core_news_sm")

nlp = load_nlp_model()

# **Regex patronen voor detectie van gevoelige informatie**
TE_ANONIMISEREN = [
    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Herkent namen (bijv. "Jan Jansen")
    r"\b\d{2}-\d{2}-\d{4}\b",  # Datums (bijv. 12-04-2025)
    r"\b\d{2}/\d{2}/\d{4}\b",  # Datums met slash (12/04/2025)
    r"\b\d{10,}\b",  # Lange getallen (zoals telefoonnummers)
    r"\b06[-\s]?\d{8}\b",  # Mobiele nummers (06-12345678 of 06 12345678)
    r"\b[1-9][0-9]{3}\s?[A-Z]{2}\b",  # Postcodes (bijv. 1234 AB)
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # E-mailadressen
    r"\b\d{9}\b",  # Mogelijke BSN-nummers (9 cijfers)

    # **Nieuwe patronen voor adres en aanhef**
    r"\b(Geachte heer|Geachte mevrouw|Beste|Aan|Dhr\.|Mevr\.)\s+[A-Z][a-z]+\b",  # Aanhef + naam
    r"\b([A-Z][a-z]+straat|[A-Z][a-z]+laan|[A-Z][a-z]+weg|[A-Z][a-z]+dijk)\s+\d+\b",  # Adressen zoals "Dorpstraat 12"
]

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
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "LOC", "FAC"]:
                ents_to_redact.add(ent.text)

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
        pdf_bytes = uploaded_file.read()
        geanonimiseerd_pdf = anonymize_pdf(pdf_bytes)

        st.success("✅ PDF is geanonimiseerd!")

        # **Toon voorbeeld van geanonimiseerde tekst**
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        eerste_pagina_text = doc[0].get_text("text")
        geanonimiseerde_tekst = eerste_pagina_text
        for pattern in TE_ANONIMISEREN:
            geanonimiseerde_tekst = re.sub(pattern, "[REDACTED]", geanonimiseerde_tekst)

        st.subheader("🔍 Geanonimiseerde tekst preview:")
        st.text(geanonimiseerde_tekst[:500])  # Eerste 500 tekens tonen als voorbeeld

        # **Downloadknop voor geanonimiseerde PDF**
        st.download_button(
            label="📥 Download geanonimiseerde PDF",
            data=geanonimiseerd_pdf,
            file_name="geanonimiseerd.pdf",
            mime="application/pdf"
        )
