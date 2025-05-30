import streamlit as st
import pytesseract 
from pdf2image import convert_from_bytes
import pandas as pd
import tempfile
import re
import io
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Infos Bulletins"

# Configuration Tesseract et Poppler
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\Users\thek7\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"

st.title("🔍 Extraction d'informations de bulletin de salaire")
ws.title = "Infos Bulletins"
uploaded_file = st.file_uploader("📄 Téléversez un fichier PDF", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    pages = convert_from_bytes(open(tmp_path, 'rb').read(), fmt='jpeg', poppler_path=poppler_path)
    full_text = pytesseract.image_to_string(pages[0], lang="eng")

    st.subheader("📝 Texte OCR extrait")
    st.text_area("Texte brut", full_text, height=300)

    # 🔍 Fonction d'extraction pour 1 page
    en_tetes = ["Fichier","Page", "Employeur","Matricule", "Nom", "Prénom","Adresse","Date entrée","Emploi", "Catégorie", "Paiement le", "Horaire", "Salaire",  "Num Sécurité Sociale"]
    def extraire_infos(page_text):
        infos = {clé: "" for clé in en_tetes}
        lines = page_text.split('\n')
        full_text = ' '.join(lines)

        # 🔹 Nom & Prénom (dans tout le texte)
        # Cas 1 : Titre + NOM (maj) + Prénom (après)
        # Cas 0 : "Monsieur Prénom NOM" dans le texte (OCR parfois dans cet ordre)
        match_nom = re.search(r'(Monsieur|Madame|Mme|M)\s+([A-Za-z\-]+)\s+([A-ZÉÈÀÂÙÎÏÔÇ\-]{2,})', page_text)
        if match_nom:
            infos["Prénom"] = match_nom.group(2).strip()
            infos["Nom"] = match_nom.group(3).strip()
        else:
            # Cas 1 : Titre + NOM (maj) + Prénom (après)
            match_nom = re.search(r'\b(Mme|M|Mr|Madame|Monsieur)\s+([A-ZÉÈÀÂÙÎÏÔÇ\-]{2,})\s+([A-Za-zéèêëîïôöüàâùûç\'\- ]+)', full_text)
            if match_nom:
                infos["Nom"] = match_nom.group(2).strip()
                infos["Prénom"] = match_nom.group(3).strip()
            else:
                # Cas 2 : Prénom (min) + "Monsieur" + NOM (maj)
                match_nom2 = re.search(r'\b([A-Za-zéèêëîïôöüàâùûç\'\- ]+)\s+(Monsieur|Madame|Mme|M|Mr)\s+([A-ZÉÈÀÂÙÎÏÔÇ\-]{2,})\b', full_text)
                if match_nom2:
                    infos["Prénom"] = match_nom2.group(1).strip()
                    infos["Nom"] = match_nom2.group(3).strip()

        for idx, line in enumerate(lines):
            
            # Chercher Horaire (nombre d'heures) sur la ligne courante et les suivantes
            if infos["Horaire"] == "":
                # Cherche un horaire au format strict 1xx.xx (commence par 1, 2 chiffres, point, 2 chiffres)
                match_horaire = re.search(r'(Horaire|Heures|Nb heures|Nombre d\'heures)[^\d]{0,20}(1[0-9]{2}\.[0-9]{2})', line, re.IGNORECASE)
                if match_horaire:
                    infos["Horaire"] = match_horaire.group(2)
                else:
                    # Cherche sur les deux lignes suivantes
                    for k in range(1, 3):
                        if idx + k < len(lines):
                            match_horaire_next = re.search(r'(Horaire|Heures|Nb heures|Nombre d\'heures)[^\d]{0,20}(1[0-9]{2}\.[0-9]{2})', lines[idx + k], re.IGNORECASE)
                            if match_horaire_next:
                                infos["Horaire"] = match_horaire_next.group(2)
                                break
                # Si toujours rien, cherche dans tout le texte de la page
                if infos["Horaire"] == "":
                    match_horaire_full = re.search(r'(Horaire|Heures|Nb heures|Nombre d\'heures)[^\d]{0,20}(1[0-9]{2}\.[0-9]{2})', full_text, re.IGNORECASE)
                    if match_horaire_full:
                        infos["Horaire"] = match_horaire_full.group(2)
                # Si toujours rien, cherche un nombre isolé au format 1xx.xx
                if infos["Horaire"] == "":
                    match_horaire_simple = re.search(r'\b(1[0-9]{2}\.[0-9]{2})\b', line)
                    if match_horaire_simple:
                        infos["Horaire"] = match_horaire_simple.group(1)
                # Ajout : cherche un nombre entier de 3 chiffres commençant par 1 (ex: 100-199)
                if infos["Horaire"] == "":
                    match_horaire_int = re.search(r'\b(1[0-9]{2})\b', line)
                    if match_horaire_int:
                        infos["Horaire"] = match_horaire_int.group(1)

            # 🔹 Paiement le ou Période : chercher la date après ces mots-clés
            match_paiement = re.search(r'(Paiement le|Période|Période du)\s*[:\-]?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})', line, re.IGNORECASE)
            if match_paiement:
                infos["Paiement le"] = match_paiement.group(2)
            elif re.search(r'(Paiement le|Période|Période du)', line, re.IGNORECASE):
                # Cherche une date JJ/MM/AAAA sur les deux lignes suivantes
                found = False
                for k in range(1, 3):
                    if idx + k < len(lines):
                        match_date = re.search(r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})', lines[idx + k])
                        if match_date:
                            infos["Paiement le"] = match_date.group(1)
                            found = True
                            break
                # Si pas trouvé, cherche un mois texte + année (ex: août 2022)
                if not found:
                    mois_regex = r'(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)'
                    for k in range(0, 3):
                        if idx + k < len(lines):
                            match_mois = re.search(rf'{mois_regex}\s+[0-9]{{4}}', lines[idx + k], re.IGNORECASE)
                            if match_mois:
                                infos["Paiement le"] = match_mois.group(0)
                                break

            # 🔹 Matricule
            if "Matricule" in line:
                match_matricule = re.search(r'Matricule\s*[:\-]?\s*([A-Z0-9]+)', line)
                if match_matricule:
                    infos["Matricule"] = match_matricule.group(1)

            # 🔹 Num Sécurité Sociale
            match_sec = re.search(r'(N° Séc\.?\.?Soc\.?|SS)\s*[:\-]?\s*([\d ]{10,})', line, re.IGNORECASE)
            if match_sec:
                infos["Num Sécurité Sociale"] = match_sec.group(2).replace(' ', '')

            # 🔹 Catégorie
            # Chercher "collective" ou "catégorie" sur la ligne courante et les 2 suivantes
            match_categorie = None
            for k in range(3):
                if idx + k < len(lines):
                    l = lines[idx + k]
                    match_categorie = re.search(r'(Statut professionnel|catégorie)\s*[:\-]?\s*(.*?)(?:\s+Horaire|$)', l, re.IGNORECASE)
                    if match_categorie:
                        break
            if match_categorie:
                infos["Catégorie"] = match_categorie.group(2).strip()

            # 🔹 Catégorie (si non trouvée, chercher dans la case après "Emploi")
            if infos["Catégorie"] == "":
                for k in range(1, 3):
                    if idx + k < len(lines):
                        if "Emploi" in lines[idx]:
                            # Prend la ligne suivante après "Emploi"
                            candidate = lines[idx + k].strip()
                            # On prend la première ligne non vide qui n'est pas un intitulé courant
                            if candidate and not re.search(r'(Matricule|Entrée|Date|Salaire|Niveau|Employeur|Adresse|Séc|SS|Emploi)', candidate, re.IGNORECASE):
                                infos["Catégorie"] = candidate
                                break
                # Ajout du contrôle pour éviter l'erreur AttributeError
                if match_categorie:
                    infos["Catégorie"] = match_categorie.group(2).strip()

            # 🔹 Emploi
            if "Emploi" in line:
                match_emploi = re.search(r'Emploi\s*[:\-]?\s*(.+)', line)
                if match_emploi:
                    infos["Emploi"] = match_emploi.group(1).strip()

            # 🔹 Date entrée (ou toute date trouvée dans le texte)
            # Chercher toutes les dates dans le texte (formats JJ/MM/AAAA, JJ/MM/AA, mois AAAA, etc.)
            if infos["Date entrée"] == "":
                # Cherche toutes les dates JJ/MM/AAAA ou JJ/MM/AA dans tout le texte
                dates = re.findall(r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})', full_text)
                if dates:
                    infos["Date entrée"] = dates[0]
                else:
                    # Cherche les dates de type "mois AAAA" (ex: août 2022)
                    mois_regex = r'(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)'
                    dates_mois = re.findall(rf'{mois_regex}\s+[0-9]{{4}}', full_text, re.IGNORECASE)
                    if dates_mois:
                        infos["Date entrée"] = dates_mois[0]

            # 🔹 Salaire (doit être 4 chiffres, point ou virgule, puis 2 chiffres)
            match_salaire = None
            # Recherche sur la ligne courante et les deux suivantes
            for k in range(0, 3):
                if idx + k < len(lines):
                    line_to_check = lines[idx + k]
                    # Cherche un nombre de 4 chiffres, séparateur, 2 chiffres après les mots-clés
                    match_salaire = re.search(
                        r'(Salaire|Net|Payé|Paye|Total|brut|imposable)[^\d]{0,20}([0-9]{4}[\.,][0-9]{2})',
                        line_to_check, re.IGNORECASE)
                    if not match_salaire:
                        # Cas où le nombre est sur la ligne suivante
                        if re.search(r'(Salaire|Net|Payé|Paye|Total|brut|imposable)', line_to_check, re.IGNORECASE):
                            for l in range(1, 3):
                                if idx + k + l < len(lines):
                                    match_salaire_next = re.search(
                                        r'([0-9]{4}[\.,][0-9]{2})',
                                        lines[idx + k + l])
                                    if match_salaire_next:
                                        match_salaire = match_salaire_next
                                        break
                    if match_salaire:
                        valeur = match_salaire.group(2 if match_salaire.lastindex == 2 else 1)
                        valeur = valeur.replace(' ', '').replace('\u202f', '').replace(',', '.')
                        infos["Salaire"] = valeur
                        break
            # Si rien trouvé, chercher dans tout le texte après "Salaire", "Net" ou "Payé"
            if infos["Salaire"] == "":
                for mot_cle in ["Salaire", "Net", "Payé", "Paye", "Total", "brut", "imposable"]:
                    pattern = rf'{mot_cle}[^\d]{{0,20}}([0-9]{{4}}[\.,][0-9]{{2}})'
                    matches = re.findall(pattern, full_text, re.IGNORECASE)
                    if matches:
                        try:
                            valeurs = [float(m.replace(' ', '').replace('\u202f', '').replace(',', '.')) for m in matches]
                            infos["Salaire"] = str(max(valeurs))
                        except Exception:
                            infos["Salaire"] = matches[0].replace(' ', '').replace('\u202f', '').replace(',', '.')
                        break
            # Si toujours rien, essaye de trouver un nombre isolé de 4 chiffres, séparateur, 2 chiffres précédé de "euros" ou "€"
            if infos["Salaire"] == "":
                match_euro = re.search(r'([0-9]{4}[\.,][0-9]{2})\s*( )', full_text, re.IGNORECASE)
                if match_euro:
                    valeur = match_euro.group(1).replace(' ', '').replace('\u202f', '').replace(',', '.')
                    infos["Salaire"] = valeur

            # 🔹 Employeur : SAS, SARL ou ligne non vide du début
            if idx <= 3 and infos["Employeur"] == "":
                if re.search(r'(SARL|SAS|SOCIETE|ENTREPRISE)', line.upper()):
                    infos["Employeur"] = line.strip()
                elif infos["Employeur"] == "" and line.strip():
                    infos["Employeur"] = line.strip()

        # 🔹 Adresse (juste après la ligne employeur)
        if infos["Adresse"] == "" and infos["Employeur"] != "":
            index_emp = next((i for i, l in enumerate(lines) if infos["Employeur"] in l), -1)
            if index_emp != -1:
                for j in range(index_emp + 1, index_emp + 4):
                    if j < len(lines):
                        candidate = lines[j].strip()
                        if re.search(r'\d{2,}.*(RUE|AVENUE|BD|BOULEVARD|IMPASSE|PLACE|ALLÉE|CHEMIN|ROUTE)', candidate, re.IGNORECASE):
                            infos["Adresse"] = candidate
                            break
                        elif infos["Adresse"] == "" and len(candidate) > 10:
                            infos["Adresse"] = candidate  # fallback

        return infos

    infos = extraire_infos(full_text)
    infos["Fichier"] = uploaded_file.name
    infos["Page"] = "1"

    # Création du DataFrame à partir des infos extraites
    df = pd.DataFrame([infos])

    st.dataframe(df)
    st.download_button("📥 Télécharger en CSV", data=df.to_csv(index=False), file_name="infos_bulletin.csv")
    st.download_button("📥 Télécharger en JSON", data=df.to_json(orient="records", force_ascii=False), file_name="infos_bulletin.json")

    # Ajout du téléchargement XLSX
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
    