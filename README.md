
# 🧾 Extraction d'informations de bulletins de salaire (OCR + Streamlit)

Ce projet permet d'extraire automatiquement des informations clés à partir de bulletins de salaire au format PDF, à l'aide de la reconnaissance optique de caractères (OCR) et d'expressions régulières (regex). Une interface utilisateur simple est proposée via Streamlit.

## 🚀 Fonctionnalités

- 📂 Téléversement d’un fichier PDF
- 🖼️ Conversion automatique du PDF en image
- 🧠 OCR via Tesseract (pytesseract)
- 🔍 Extraction automatique de :
  - Nom / Prénom
  - Matricule
  - Emploi / Catégorie / Horaire
  - Date d’entrée
  - Numéro de sécurité sociale
  - Date de paiement
- 🧾 Affichage du texte brut OCR
- 💾 Export des données extraites en Excel (openpyxl)
- 📸 Démonstration (exemple)

![Aperçu de l'application Streamlit](screenshot.png)

## 🛠️ Technologies utilisées

- Python 3.9+
- Streamlit
- pytesseract
- pdf2image
- openpyxl
- Regex (expressions régulières)

## 📦 Installation

1. Cloner le dépôt

```bash
git clone https://github.com/ton-utilisateur/nom-du-projet.git
cd nom-du-projet
```

2. Créer et activer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Installer les dépendances

```bash
pip install -r requirements.txt
```

4. Installer Poppler (nécessaire pour pdf2image)

- 🔗 [Téléchargement Poppler pour Windows](http://blog.alivate.com.au/poppler-windows/)
- Sur Linux :
```bash
sudo apt install poppler-utils
```

5. Vérifier l’installation de Tesseract

- 🔗 [Télécharger Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

Ensuite, ajoutez le chemin vers `tesseract.exe` si nécessaire :

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## ▶️ Lancer l'application

```bash
streamlit run app.py
```

## 📁 Structure du projet

```
.
├── app.py                 # Application Streamlit principale
├── extract.py             # Fonctions d’extraction (regex + OCR)
├── requirements.txt       # Dépendances Python
├── README.md              # Ce fichier
└── screenshot.png         # Capture d'écran (optionnel)
```

## ✅ À faire (améliorations futures)

- Ajouter une détection automatique de champs mal lus (corrections OCR)
- Gérer les bulletins multi-pages
- Ajouter une base de données pour historiser les extractions
- Authentification utilisateur

## 👨‍💻 Auteur

Ton nom – [Ton LinkedIn](https://www.linkedin.com)
