import streamlit as st
import fitz  # PyMuPDF voor PDF-verwerking
import pytesseract  # OCR voor gescande PDF's
import spacy
import subprocess
from pdf2image import convert_from_path
import os

# ✅ Automatisch het Spacy-model downloaden en instellen
model_name = "nl_core_news_sm"
spacy_model_path = os.path.expanduser(f"~/.local/share/spacy/{model_name}")

if not os.path.exists(spacy_model_path):
    st.info("🔄 Downloading Spacy model... (eenmalig)")
    subprocess.run(["python", "-m", "spacy", "download", model_name], check=True)

nlp = spacy.load(model_name)

# ✅ Webinterface
st.title("🔒 WOO Anonimiser")

# 📤 PDF Upload
uploaded_file = st.file_uploader("📄 Upload een PDF", type="pdf")

if uploaded_file:
    with open("input.pdf", "wb") as f:
        f.write(uploaded_file.read())

    # ✅ Tekstextractie uit PDF (OCR voor gescande bestanden)
    def extract_text_from_pdf(pdf_path):
        images = convert_from_path(pdf_path, dpi=300)
        extracted_text = ""
        for image in images:
            page_text = pytesseract.image_to_string(image, lang="nld")
            extracted_text += page_text + "\n"
        return extracted_text

    # ✅ Anonimiseer de herkende tekst
    def anonymize_text(text):
        doc = nlp(text)
        anonymized_text = text
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "MONEY", "EMAIL", "PHONE", "DATE"]:
                anonymized_text = anonymized_text.replace(ent.text, "[ANONIEM]")
        return anonymized_text

    # ✅ Verwerk en anonimiseer de PDF
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

    # ✅ Downloadknop voor de geanonimiseerde PDF
    with open("geanonimiseerd.pdf", "rb") as f:
        st.download_button("📥 Download geanonimiseerde PDF", f, file_name="geanonimiseerd.pdf")

