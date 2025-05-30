import streamlit as st
import pytesseract
import pandas as pd
import tempfile
import re
import io
from PIL import Image
import fitz  # PyMuPDF
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Infos Bulletins"

st.title("🔍 Extraction d'informations de bulletin de salaire")
uploaded_file = st.file_uploader("📄 Téléversez un fichier PDF", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    doc = fitz.open(tmp_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    img_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_bytes))

    full_text = pytesseract.image_to_string(image, lang="eng")

    st.subheader("📝 Texte OCR extrait")
    st.text_area("Texte brut", full_text, height=300)

    en_tetes = ["Fichier","Page", "Employeur","Matricule", "Nom", "Prénom","Adresse",
                "Date entrée","Emploi", "Catégorie", "Paiement le", "Horaire",
                "Salaire",  "Num Sécurité Sociale"]

    def extraire_infos(page_text):
        infos = {clé: "" for clé in en_tetes}
        lines = page_text.split('\n')
        full_text = ' '.join(lines)

        match_nom = re.search(r'(Monsieur|Madame|Mme|M)\s+([A-Za-z\-]+)\s+([A-ZÉÈÀÂÙÎÏÔÇ\-]{2,})', page_text)
        if match_nom:
            infos["Prénom"] = match_nom.group(2).strip()
            infos["Nom"] = match_nom.group(3).strip()
        else:
            match_nom = re.search(r'\b(Mme|M|Mr|Madame|Monsieur)\s+([A-ZÉÈÀÂÙÎÏÔÇ\-]{2,})\s+([A-Za-zéèêëîïôöüàâùûç\'\- ]+)', full_text)
            if match_nom:
                infos["Nom"] = match_nom.group(2).strip()
                infos["Prénom"] = match_nom.group(3).strip()
            else:
                match_nom2 = re.search(r'\b([A-Za-zéèêëîïôöüàâùûç\'\- ]+)\s+(Monsieur|Madame|Mme|M|Mr)\s+([A-ZÉÈÀÂÙÎÏÔÇ\-]{2,})\b', full_text)
                if match_nom2:
                    infos["Prénom"] = match_nom2.group(1).strip()
                    infos["Nom"] = match_nom2.group(3).strip()

        for idx, line in enumerate(lines):
            if infos["Horaire"] == "":
                match_horaire = re.search(r'(Horaire|Heures|Nb heures|Nombre d\'heures)[^\d]{0,20}(1[0-9]{2}\.[0-9]{2})', line, re.IGNORECASE)
                if match_horaire:
                    infos["Horaire"] = match_horaire.group(2)

            match_paiement = re.search(r'(Paiement le|Période du)[^\d]{0,10}([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})', line)
            if match_paiement:
                infos["Paiement le"] = match_paiement.group(2)

            if "Matricule" in line:
                match_matricule = re.search(r'Matricule\s*[:\-]?\s*([A-Z0-9]+)', line)
                if match_matricule:
                    infos["Matricule"] = match_matricule.group(1)

            match_sec = re.search(r'(N° Séc\.?\.?Soc\.?|SS)\s*[:\-]?\s*([\d ]{10,})', line, re.IGNORECASE)
            if match_sec:
                infos["Num Sécurité Sociale"] = match_sec.group(2).replace(' ', '')

            if "Emploi" in line:
                match_emploi = re.search(r'Emploi\s*[:\-]?\s*(.+)', line)
                if match_emploi:
                    infos["Emploi"] = match_emploi.group(1).strip()

            if idx <= 3 and infos["Employeur"] == "":
                if re.search(r'(SARL|SAS|SOCIETE|ENTREPRISE)', line.upper()):
                    infos["Employeur"] = line.strip()
                elif line.strip():
                    infos["Employeur"] = line.strip()

        if infos["Date entrée"] == "":
            dates = re.findall(r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})', full_text)
            if dates:
                infos["Date entrée"] = dates[0]

        match_salaire = re.search(r'(Salaire|Net|Payé)[^\d]{0,20}([0-9]{4}[\.,][0-9]{2})', full_text, re.IGNORECASE)
        if match_salaire:
            valeur = match_salaire.group(2).replace(',', '.')
            infos["Salaire"] = valeur

        return infos

    infos = extraire_infos(full_text)
    infos["Fichier"] = uploaded_file.name
    infos["Page"] = "1"

    df = pd.DataFrame([infos])

    st.dataframe(df)
    st.download_button("📥 Télécharger en CSV", data=df.to_csv(index=False), file_name="infos_bulletin.csv")
    st.download_button("📥 Télécharger en JSON", data=df.to_json(orient="records", force_ascii=False), file_name="infos_bulletin.json")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Infos')
    output.seek(0)
    st.download_button(
        label="📥 Télécharger en XLSX",
        data=output,
        file_name="infos_bulletin.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
