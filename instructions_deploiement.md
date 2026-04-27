# Instructions de Déploiement - Académie Numérique

## 1. Prérequis
- Python 3.11+
- MySQL Server 8.0+
- Redis Server (pour Celery)
- Clé API Gemini ou DeepSeek

## 2. Installation
```bash
# Cloner le dépôt et entrer dans le dossier
cd numerique-ia-composition

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## 3. Configuration de la Base de Données
1. Créer une base de données MySQL nommée `academie_numerique`.
2. Copier `.env.example` vers `.env` et remplir les informations.
3. Appliquer les migrations :
```bash
python manage.py makemigrations
python manage.py migrate
```

## 4. Lancement des services
```bash
# Terminal 1 : Serveur Django
python manage.py runserver

# Terminal 2 : Celery Worker (Correction IA asynchrone)
celery -A academie_numerique worker --loglevel=info

# Terminal 3 : Redis (si non lancé en service)
redis-server
```

## 5. Mots de passe de rôle (Inscription)
- **ADMIN** : `admin2025`
- **CONSEILLER** : `cp2026`
- **PROFESSEUR** : `prof2026`

## 6. Fonctionnalités IA
L'application bascule automatiquement en mode **Simulation (Mock)** si aucune clé API n'est configurée dans le fichier `.env`. Pour activer la correction réelle, renseignez `GEMINI_API_KEY` ou `DEEPSEEK_API_KEY`.
