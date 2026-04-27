# 🚀 Académie Numérique IA - Setup & Deploy

## 🎉 Nouvelles Fonctionnalités Ajoutées

### 1. 📹 Vitrine Vidéo (Pre-Homepage)
- Page plein écran avec vidéos en oblique qui滑ent en boucle
- Vidéos auto-play **inarrêtables** (pas de contrôles, pas de pause)
- Effet parallax avec la souris
- Animation de fond dynamique

### 2. 🎥 Salles de Réunion (Vidéoconférence)
- Création de salles par les admins
- Intégration Google Meet
- Chat en temps réel via WebSocket
- Modération (mute, kick, promote)
- Salon d'attente, code d'accès

### 3. 💬 Forums & Communauté
- Forums par catégorie
- Sujets et messages
- Groupes d'étude
- Système de likes

### 4. 📅 Calendrier
- Événements (examens, cours, dates limites)
- Rappels automatiques
- Suivi des présences

### 5. 📁 Documents & Fichiers
- Upload et partage de documents
- Catégories (cours, examens, ressources)
- Téléchargement avec compteur
- Commentaires sur les documents

### 6. 📊 Analytiques
- Tableau de bord avec graphiques
- Suivi des performances
- Statistiques d'étude
- Activité récente

### 7. 🎨 Thème Clair/Sombre
- Toggle dans la barre supérieure
- Sauvegarde dans localStorage

### 8. 📱 Support PWA
- Installable sur mobile
- Service Worker pour le cache
- Manifest.json configuré

## 📁 Structure des Médias

### Vidéos de la Vitrine
```
media/showcase_videos/       ← Place tes fichiers .mp4 ici
media/showcase_thumbnails/   ← Images de couverture (.jpg, .png)
```

### Documents Uploadés
```
media/documents/{user_id}/   ← Documents par utilisateur
```

## 🚀 Installation & Déploiement

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Créer les migrations
```bash
python manage.py makemigrations
python manage.py makemigrations video_showcase
python manage.py makemigrations social
python manage.py makemigrations calendar_app
python manage.py makemigrations documents
```

### 3. Appliquer les migrations
```bash
python manage.py migrate
```

### 4. Créer un superuser
```bash
python manage.py createsuperuser
```

### 5. Collecter les fichiers statiques
```bash
python manage.py collectstatic
```

### 6. Lancer le serveur
```bash
# Développement
python manage.py runserver 0.0.0.0:8000

# Production (avec Daphne pour WebSockets)
daphne -b 0.0.0.0 -p 8000 academie_numerique.asgi:application
```

## 📂 URLs de l'Application

| Page | URL |
|------|-----|
| **Vitrine Vidéo** | `/` ou `/showcase/` |
| **Application Principale** | `/app/` |
| **Admin** | `/admin/` |
| **Salles de Réunion** | `/videoconf/` |
| **Forums** | `/forums/` |
| **Calendrier** | `/calendar/` |
| **Documents** | `/documents/` |
| **Analytiques** | `/analytics/` |
| **API** | `/api/v1/` |

## 🎬 Ajouter des Vidéos à la Vitrine

1. Place tes fichiers MP4 dans `media/showcase_videos/`
2. Va dans l'admin: `/admin/`
3. Clique sur **"Annonces Vidéo"** sous **"Vitrine Vidéo"**
4. Ajoute chaque vidéo avec:
   - Titre & description
   - Fichier vidéo
   - Miniature (optionnel)
   - Catégorie
   - Ordre d'affichage
5. Active et sauvegarde

## 🎨 Personnalisation

### Couleurs du Thème
Dans `templates/base.html`:
- Primary: `#4F46E5` (Indigo)
- Secondary: `#7C3AED` (Purple)
- Accent: `#0891B2` (Cyan)

### Icônes des Forums
Utilise les classes FontAwesome: `fa-solid fa-xxx`

## 🔧 Configuration Production

### Variables d'environnement (.env)
```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
DB_ENGINE=mysql
DB_NAME=academie_numerique
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Commandes de Production
```bash
# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput

# Start with Gunicorn + Daphne
gunicorn academie_numerique.wsgi:application --bind 0.0.0.0:8000
daphne -b 0.0.0.0 -p 8001 academie_numerique.asgi:application
```

## 📱 Installation PWA (Mobile)

1. Ouvre l'app dans Chrome/Safari
2. Clique sur "Ajouter à l'écran d'accueil"
3. L'app s'installe comme une app native

## 🛡️ Sécurité

- CSRF protection activée
- XSS prevention
- SQL injection protection (ORM Django)
- Password hashing (bcrypt)
- Session security (7 jours)

## 📞 Support

Pour toute question ou problème, consulte:
- L'admin Django: `/admin/`
- Les logs: `logs/django.log`
- La documentation Django: https://docs.djangoproject.com/

---

**Développé avec ❤️ pour l'Académie Numérique IA**
