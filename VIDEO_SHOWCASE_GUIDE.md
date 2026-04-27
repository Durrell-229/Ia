# 📹 Guide: Ajouter des Vidéos à la Vitrine

## Structure des dossiers

Les vidéos doivent être placées dans:
```
media/showcase_videos/       ← Vos fichiers vidéo (.mp4 recommandé)
media/showcase_thumbnails/   ← Images de couverture (.jpg, .png)
```

## Comment ajouter une vidéo

### Méthode 1: Via l'Admin Django

1. Accédez à: `http://localhost:8000/admin/`
2. Connectez-vous avec votre superuser
3. Cliquez sur **"Annonces Vidéo"** sous **"Vitrine Vidéo"**
4. Cliquez sur **"Ajouter Annonce Vidéo"**
5. Remplissez:
   - **Titre**: Nom de la vidéo
   - **Description**: Courte description (optionnel)
   - **Vidéo**: Sélectionnez votre fichier MP4
   - **Miniature**: Image de couverture (optionnel)
   - **Catégorie**: 
     - Promotion
     - Tutoriel
     - Annonce
     - Témoignage
     - Fonctionnalité
   - **Ordre**: Numéro d'ordre (0 = premier)
   - **Active**: Cochez pour afficher
   - **Jouer automatiquement**: Cochez pour autoplay
6. Cliquez sur **"Enregistrer"**

### Méthode 2: Directement dans le dossier

1. Placez votre fichier vidéo dans:
   ```
   media/showcase_videos/
   ```
   Exemple: `media/showcase_videos/ma_video.mp4`

2. (Optionnel) Placez une image de couverture dans:
   ```
   media/showcase_thumbnails/
   ```
   Exemple: `media/showcase_thumbnails/ma_miniature.jpg`

3. Créez l'entrée via l'Admin Django en sélectionnant le fichier

## Recommandations

### Format Vidéo
- **Format**: MP4 (H.264 codec)
- **Taille maximale**: 100MB
- **Résolution**: 1920x1080 (Full HD) ou 1280x720 (HD)
- **Durée**: 15-60 secondes recommandé
- **Ratio**: 16:9

### Miniature
- **Format**: JPG ou PNG
- **Taille**: 1280x720 pixels
- **Ratio**: 16:9

### Nombre de vidéos
- **Minimum recommandé**: 10 vidéos pour un effet optimal
- **Maximum**: Illimité (mais 10-20 est idéal)

## Exemple de noms de fichiers

```
media/
├── showcase_videos/
│   ├── welcome.mp4
│   ├── features_overview.mp4
│   ├── student_testimonial.mp4
│   ├── ai_correction_demo.mp4
│   ├── exam_creation.mp4
│   ├── dashboard_tour.mp4
│   ├── mobile_app.mp4
│   ├── teacher_testimonial.mp4
│   ├── results_analytics.mp4
│   └── call_to_action.mp4
└── showcase_thumbnails/
    ├── welcome_thumb.jpg
    ├── features_thumb.jpg
    ├── student_thumb.jpg
    ├── ai_correction_thumb.jpg
    ├── exam_creation_thumb.jpg
    ├── dashboard_thumb.jpg
    ├── mobile_thumb.jpg
    ├── teacher_thumb.jpg
    ├── results_thumb.jpg
    └── cta_thumb.jpg
```

## Page de la vitrine

La page est accessible à: `http://localhost:8000/showcase/`

La page d'accueil (`http://localhost:8000/`) redirige automatiquement vers la vitrine.

Le bouton **"Accéder à l'application"** en haut à droite mène à l'application principale.
