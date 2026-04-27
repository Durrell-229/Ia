# Dossier Technique : Académie Numérique (Solution IA Éducative)

## 1. Vue d'ensemble
L'Académie Numérique est une plateforme éducative souveraine intégrant une intelligence artificielle de pointe pour la génération de contenus pédagogiques, la correction automatique de copies manuscrites, et la gestion hiérarchisée des flux de validation académique.

## 2. Stack Technique
- **Framework Web** : Django (Python 3.14)
- **Base de données** : SQLite (Migrable vers PostgreSQL)
- **Orchestrateur IA** : `SmartOrchestrator` (Redondance : Groq, Mistral AI, Agents IA)
- **OCR & Vision** : `EasyOCR` (Open Source, local) & `Mistral Vision` (API)
- **Gestion des tâches** : Celery & Redis (Prêt pour la production)
- **Frontend** : Tailwind CSS, Alpine.js

## 3. Fonctionnalités Clés
- **Génération Intelligente (QCM)** : Création de contenus pédagogiques via LLM avec basculement automatique en cas de défaillance (Groq -> Mistral).
- **Correction Automatique de Copies** : Analyse par vision artificielle (OCR + LLM) des copies manuscrites (JPG/PNG).
- **Workflow Hiérarchisé** : Système d'approbation obligatoire (Professeur -> Administrateur) pour toute publication de contenu ou bulletin.
- **Souveraineté des données** : Architecture locale et confidentielle, respectant les normes ministérielles.

## 4. Bibliothèques & Dépendances
- **IA** : `groq`, `mistralai`
- **OCR** : `easyocr`, `opencv-python-headless`
- **Développement** : `django`, `django-ninja`
- **Traitement de données** : `pillow`, `scipy`, `numpy`, `torch`, `torchvision`

## 5. Rôles & Accès
- **Élèves** : Téléversement des copies, passation des évaluations.
- **Enseignants** : Génération de QCM, révision des corrections automatiques.
- **Administrateurs** : Approbation finale, publication des contenus, gestion des bulletins.

## 6. Infrastructure de Déploiement
- Architecture conteneurisée (Docker).
- Stratégie d'hébergement : Oracle Cloud (Instance Ampere, Always Free).

---
**Développeur : ADEGBOLA LEONARD DURRELL**
