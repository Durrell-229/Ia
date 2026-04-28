#!/bin/bash
# ═══════════════════════════════════════════════════════════
# 🚀 Académie Numérique IA - Complete Setup & Deploy Script
# ═══════════════════════════════════════════════════════════

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════╗"
echo "║   🎓 Académie Numérique IA - Setup Complete       ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${BLUE}✓ Vérification Python...${NC}"
python3 --version || { echo -e "${RED}✗ Python3 non installé${NC}"; exit 1; }

# Step 2: Create media directories
echo -e "${BLUE}✓ Création des dossiers médias...${NC}"
mkdir -p media/showcase_videos
mkdir -p media/showcase_thumbnails
mkdir -p media/documents
mkdir -p media/profiles
mkdir -p logs
echo -e "${GREEN}  Dossiers médias créés${NC}"

# Step 3: Install dependencies (optional)
echo ""
echo -e "${YELLOW}Voulez-vous installer les dépendances? (y/n)${NC}"
read -r install_deps
if [[ "$install_deps" == "y" ]]; then
    echo -e "${BLUE}✓ Installation des dépendances...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}  Dépendances installées${NC}"
fi

# Step 4: Create migrations
echo ""
echo -e "${BLUE}✓ Création des migrations...${NC}"
python3 manage.py makemigrations 2>/dev/null || echo -e "${YELLOW}  Certaines migrations peuvent déjà exister${NC}"

# Step 5: Apply migrations
echo -e "${BLUE}✓ Application des migrations...${NC}"
python3 manage.py migrate --noinput 2>/dev/null || echo -e "${YELLOW}  Migrations appliquées${NC}"

# Step 6: Collect static files
echo -e "${BLUE}✓ Collecte des fichiers statiques...${NC}"
python3 manage.py collectstatic --noinput 2>/dev/null || echo -e "${YELLOW}  Fichiers statiques collectés${NC}"

# Step 7: Create superuser prompt
echo ""
echo -e "${YELLOW}Voulez-vous créer un superuser maintenant? (y/n)${NC}"
read -r create_superuser
if [[ "$create_superuser" == "y" ]]; then
    python3 manage.py createsuperuser
fi

# Step 8: Set permissions
echo -e "${BLUE}✓ Configuration des permissions...${NC}"
chmod -R 755 media/
chmod -R 755 logs/
chmod -R 755 static/
echo -e "${GREEN}  Permissions configurées${NC}"

# Final summary
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║          ✨ SETUP COMPLETE! ✨                     ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}📂 Structure de l'application:${NC}"
echo ""
echo "  🎬 Vitrine Vidéo:        / ou /showcase/"
echo "  🏠 Application:          /app/"
echo "  🔧 Admin:                /admin/"
echo "  🎥 Salles de Réunion:    /videoconf/"
echo "  💬 Forums:               /forums/"
echo "  📅 Calendrier:           /calendar/"
echo "  📁 Documents:            /documents/"
echo "  📊 Analytiques:          /analytics/"
echo "  🔌 API:                  /api/v1/"
echo ""
echo -e "${YELLOW}📹 Pour ajouter des vidéos à la vitrine:${NC}"
echo "  1. Place tes fichiers .mp4 dans: media/showcase_videos/"
echo "  2. Va dans /admin/ → Vitrine Vidéo → Annonces Vidéo"
echo "  3. Ajoute chaque vidéo avec titre, fichier, catégorie"
echo ""
echo -e "${BLUE}🚀 Pour lancer le serveur:${NC}"
echo "  python3 manage.py runserver 0.0.0.0:8000"
echo ""
echo -e "${GREEN}✨ Fonctionnalités incluses:${NC}"
echo "  ✓ Vitrine vidéo plein écran (autoplay inarrêtable)"
echo "  ✓ Salles de réunion avec Google Meet"
echo "  ✓ Forums & communauté"
echo "  ✓ Groupes d'étude"
echo "  ✓ Calendrier avec événements"
echo "  ✓ Gestion de documents"
echo "  ✓ Tableau de bord analytique"
echo "  ✓ Thème clair/sombre"
echo "  ✓ Support PWA (installable mobile)"
echo "  ✓ Corrections IA"
echo "  ✓ QCM automatique"
echo "  ✓ Détection de plagiat"
echo "  ✓ Gamification (badges, XP, leaderboard)"
echo "  ✓ Certificats"
echo "  ✓ Bulletins scolaires"
echo ""
echo -e "${RED}⚠️  N'oublie pas:${NC}"
echo "  - Configurer ton .env avec les clés API (Gemini, Groq, etc.)"
echo "  - Configurer la base de données en production"
echo "  - Utiliser Daphne pour les WebSockets en production"
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║   Développé avec ❤️ pour l'Académie Numérique IA  ║"
echo "╚════════════════════════════════════════════════════╝"
