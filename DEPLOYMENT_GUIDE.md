# 🚀 Guide de Déploiement Complet

## ✅ Votre requirements.txt contient TOUT ce qu'il faut!

### 📦 Dépendances incluses:

**Core Django:**
- ✅ Django 5.2.13
- ✅ Django Ninja (API REST)
- ✅ Django Channels (WebSockets)
- ✅ Daphne (ASGI Server)
- ✅ Gunicorn (WSGI Server)
- ✅ Whitenoise (Static files)

**Database:**
- ✅ mysqlclient (MySQL)
- ✅ psycopg2-binary (PostgreSQL)
- ✅ dj-database-url

**Real-time:**
- ✅ channels_redis
- ✅ Redis
- ✅ msgpack

**AI/ML:**
- ✅ Google Gemini
- ✅ Groq
- ✅ Mistral AI
- ✅ DeepSeek
- ✅ PyTorch
- ✅ OpenCV
- ✅ scikit-image

**Document Processing:**
- ✅ PyMuPDF
- ✅ reportlab
- ✅ weasyprint
- ✅ python-docx
- ✅ pypdf
- ✅ pytesseract
- ✅ Pillow

**Security:**
- ✅ cryptography
- ✅ pyOpenSSL
- ✅ bcrypt
- ✅ PyJWT

**Task Queue:**
- ✅ Celery
- ✅ django-celery-beat
- ✅ django-celery-results

**Nouvelles dépendances ajoutées:**
- ✅ python-multipart (Upload fichiers)
- ✅ pytz (Timezone)
- ✅ aioredis (WebSocket enhancements)
- ✅ django-pwa (PWA support)
- ✅ django-redis (Cache optimization)
- ✅ filetype (Détection type fichier)
- ✅ moviepy (Video processing - optionnel)

---

## 🎯 Étapes de Déploiement

### 1️⃣ Installation Rapide

```bash
# Cloner le projet
cd /sdcard/Download/numerique-ia-composition-main1/numerique-ia-composition-main1

# Créer un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate

# Installer TOUTES les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Créer les dossiers média
mkdir -p media/showcase_videos media/showcase_thumbnails media/documents

# Lancer les migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superuser
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Lancer le serveur
python manage.py runserver 0.0.0.0:8000
```

### 2️⃣ Vérification

Après le lancement, vérifiez ces URLs:

| URL | Statut |
|-----|--------|
| http://localhost:8000/ | ✅ Vitrine vidéo |
| http://localhost:8000/app/ | ✅ App principale |
| http://localhost:8000/admin/ | ✅ Admin |
| http://localhost:8000/videoconf/ | ✅ Salles de réunion |
| http://localhost:8000/forums/ | ✅ Forums |
| http://localhost:8000/calendar/ | ✅ Calendrier |
| http://localhost:8000/documents/ | ✅ Documents |
| http://localhost:8000/analytics/ | ✅ Analytiques |
| http://localhost:8000/api/v1/ | ✅ API |

### 3️⃣ Production Setup

Pour la production, utilisez:

```bash
# Serveur Web (HTTP)
gunicorn academie_numerique.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120

# WebSockets (ASGI)
daphne -b 0.0.0.0 -p 8001 academie_numerique.asgi:application

# Celery Worker (Tâches asynchrones)
celery -A academie_numerique worker --loglevel=info

# Celery Beat (Tâches planifiées)
celery -A academie_numerique beat --loglevel=info
```

### 4️⃣ Nginx Configuration (Optionnel)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }

    # Proxy vers Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Proxy WebSocket vers Daphne
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔧 Troubleshooting

### Problème: "ModuleNotFoundError: No module named 'django'"
**Solution:** Activez votre environnement virtuel
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problème: Migration errors
**Solution:** 
```bash
python manage.py makemigrations --empty video_showcase
python manage.py makemigrations
python manage.py migrate --run-syncdb
```

### Problème: WebSockets ne fonctionnent pas
**Solution:** Vérifiez que Redis tourne
```bash
redis-cli ping  # Doit retourner "PONG"
redis-server    # Pour démarrer Redis
```

### Problème: Vidéos ne s'affichent pas
**Solution:** Vérifiez les permissions
```bash
chmod -R 755 media/
chown -R www-data:www-data media/
```

---

## 📋 Checklist Pré-Déploiement

- [ ] `requirements.txt` installé (`pip install -r requirements.txt`)
- [ ] Fichier `.env` configuré avec vos valeurs
- [ ] Base de données créée et configurée
- [ ] Migrations appliquées (`python manage.py migrate`)
- [ ] Superuser créé (`python manage.py createsuperuser`)
- [ ] Fichiers statiques collectés (`python manage.py collectstatic`)
- [ ] Dossiers média créés avec permissions
- [ ] Redis installé et démarré
- [ ] Clés API IA configurées (Gemini, Groq, etc.)
- [ ] Vidéos placées dans `media/showcase_videos/`
- [ ] Domaine configuré dans `ALLOWED_HOSTS`
- [ ] HTTPS activé (Let's Encrypt)

---

## 🎬 Pour Ajouter des Vidéos

1. Placez vos fichiers `.mp4` dans `media/showcase_videos/`
2. Allez dans `/admin/` → **Vitrine Vidéo** → **Annonces Vidéo**
3. Cliquez sur **Ajouter**
4. Remplissez:
   - Titre
   - Sélectionnez le fichier vidéo
   - Catégorie (Promo, Tutoriel, etc.)
   - Ordre (0 = premier)
   - Cochez "Active" et "Jouer automatiquement"
5. Sauvegardez

**Les vidéos apparaîtront sur la page d'accueil en oblique et joueront en boucle!**

---

## 🚀 Commandes Utiles

```bash
# Voir toutes les URLs
python manage.py show_urls

# Vérifier les migrations
python manage.py showmigrations

# Shell Django
python manage.py shell

# Créer un superuser automatiquement
echo "from accounts.models import User; User.objects.create_superuser('admin@test.com', 'admin123')" | python manage.py shell

# Backup base de données
python manage.py dumpdata > backup.json

# Restore
python manage.py loaddata backup.json

# Voir les logs
tail -f logs/django.log
```

---

**Votre app est prête pour la production! 🎉**
