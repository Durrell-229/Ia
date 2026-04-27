"""
Système de Gamification Complet - Inspiré Duolingo/Coursera/Discord
Badges, Leaderboards, XP, Streaks, Achievements, Classes Sociales
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date, timedelta


class Badge(models.Model):
    """
    Badges professionnels avec raretés et conditions sophistiquées
    Inspiré: Duolingo (badges quotidiens), Coursera (compétences)
    """
    class Categorie(models.TextChoices):
        ACADEMIQUE = 'academique', _('Académique')
        PARTICIPATION = 'participation', _('Participation')
        EXCELLENCE = 'excellence', _('Excellence')
        PROGRESSION = 'progression', _('Progression')
        SOCIAL = 'social', _('Social & Communautaire')
        SPECIAL = 'special', _('Spécial & Événementiel')
        COMPETITION = 'competition', _('Compétition')
        MENTORAT = 'mentorat', _('Mentorat & Aide')

    class Rarete(models.TextChoices):
        COMMUN = 'commun', _('Commun 🟢')
        RARE = 'rare', _('Rare 🔵')
        EPIQUE = 'epique', _('Épique 🟣')
        LEGENDAIRE = 'legendaire', _('Légendaire 🟠')
        MYTHIQUE = 'mythique', _('Mythique ⭐')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(_('nom'), max_length=100)
    description = models.TextField(_('description'))
    icone = models.CharField(_('icône emoji'), max_length=10, default='🏆')
    icone_svg = models.URLField(_('URL SVG icon'), blank=True, null=True)
    categorie = models.CharField(_('catégorie'), max_length=20, choices=Categorie.choices, default=Categorie.ACADEMIQUE)
    points_valeur = models.PositiveIntegerField(_('valeur en XP'), default=50)
    
    # Conditions d'obtention (JSON flexible)
    condition_obtention = models.JSONField(
        _('conditions'), 
        default=dict,
        help_text="Ex: {'compositions': 10, 'moyenne_min': 15}"
    )
    
    # Apparitions
    est_actif = models.BooleanField(_('actif'), default=True)
    visible_public = models.BooleanField(_('visible publiquement'), default=True)
    is_achievable = models.BooleanField(_('atteignable'), default=True)
    
    # Rareté & Progression
    rarete = models.CharField(_('rareté'), max_length=20, choices=Rarete.choices, default=Rarete.COMMUN)
    ordre_affichage = models.PositiveIntegerField(_('ordre affichage'), default=0)
    
    # Stats
    nb_attributions = models.PositiveIntegerField(default=0)
    dernier_attribution = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('badge')
        verbose_name_plural = _('badges')
        ordering = ['ordre_affichage', '-points_valeur', 'rarete']
        indexes = [
            models.Index(fields=['categorie', 'est_actif']),
            models.Index(fields=['rarete']),
        ]

    def __str__(self):
        return f"{self.icone} {self.nom} ({self.get_rarete_display()})"
    
    def atribuer_a_utilisateur(self, user, log_action=True):
        """Méthode utilitaire pour attribuer le badge à un utilisateur - SANS Celery"""
        UserBadge.objects.get_or_create(user=user, badge=self)
        
        # Mettre à jour compteur
        self.nb_attributions += 1
        self.dernier_attribution = timezone.now()
        self.save(update_fields=['nb_attributions', 'dernier_attribution'])
        
        # Log action XP directement (pas de Celery)
        if log_action:
            from .models import XPAction
            
            xp_action = XPAction.objects.create(
                user=user,
                action_type="badge_obtenu",
                points_gagnes=self.points_valeur,
                description=f"Badge débloqué: {self.nom}",
                metadata={'badge_id': str(self.id)}
            )
            
            logger = __import__('logging').getLogger(__name__)
            logger.info(f"[Gamification] Badge '{self.nom}' attribué à {user.full_name}: +{self.points_valeur} XP")


class UserBadge(models.Model):
    """
    Suivi badges utilisateurs avec effets visuels
    Type: "nouveau badge débloqué!" comme Duolingo
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='attributions')
    obtenu_at = models.DateTimeField(_('obtenu le'), default=timezone.now)
    est_nouveau = models.BooleanField(_('nouveau (non lu)'), default=True)
    
    # Statistiques spécifiques au badge
    performances = models.JSONField(
        _('performances sur ce badge'),
        default=dict,
        blank=True,
        help_text="Stats personnalisées ex: {'score_moyen': 16.5, 'tentatives': 3}"
    )
    
    class Meta:
        verbose_name = _('badge utilisateur')
        verbose_name_plural = _('badges utilisateur')
        unique_together = ['user', 'badge']
        ordering = ['-obtenu_at']
        indexes = [
            models.Index(fields=['user', 'est_nouveau']),
            models.Index(fields=['obtenu_at']),
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.badge.nom}"
    
    def marquer_comme_lu(self):
        self.est_nouveau = False
        self.save(update_fields=['est_nouveau'])


class GlobalLeaderboard(models.Model):
    """
    Leaderboards multi-dimensionnels inspirés de Discord/Coursera
    - Mondial, National, Classe, Institution
    - Périodes: Jour, Semaine, Mois, Année, Tous temps
    """
    class Periode(models.TextChoices):
        JOUR = 'jour', _('Journalier')
        SEMAINE = 'semaine', _('Hebdomadaire')
        MOIS = 'mois', _('Mensuel')
        ANNEE = 'annee', _('Annuel')
        ALL_TIME = 'all_time', _('Tous les temps')

    class Echelon(models.TextChoices):
        NOVICE = 'novice', _('Novice')
        APPRENTI = 'apprenti', _("Apprenti")
        ETUDIAN = 'etudiant', _('Étudiant')
        EXPERT = 'expert', _('Expert')
        MAITRE = 'maitre', _('Maître')
        SAGE = 'sage', _('Sage')
        LEGENDE = 'legende', _('Légende')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaderboard_entries')
    
    # Classification
    periode = models.CharField(_('période'), max_length=20, choices=Periode.choices, default=Periode.ALL_TIME)
    date_periode = models.DateField(_('date période référence'))
    
    # Rangements hiérarchiques
    rang_mondial = models.PositiveIntegerField(_('rang mondial'), default=99999)
    rang_national = models.PositiveIntegerField(_('rang national'), default=99999)
    rang_classe = models.PositiveIntegerField(_('rang dans classe'), default=99999)
    rang_institution = models.PositiveIntegerField(_('rang institution'), default=99999)
    
    # Score & Performance
    score_total = models.DecimalField(_('score total (XP+achievements)'), max_digits=10, decimal_places=2, default=0)
    points_xp = models.PositiveIntegerField(_('points XP totaux'), default=0)
    niveau = models.PositiveIntegerField(_('niveau actuel'), default=1)
    
    # Activité académique
    nb_compositions = models.PositiveIntegerField(_('compositions passées'), default=0)
    nb_excellentes = models.PositiveIntegerField(_('notes excellentes (≥16/20)'), default=0)
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, default=0)
    
    # Engagement communautaire
    streak_jours = models.PositiveIntegerField(_('série jours actifs'), default=0)
    badges_obtenus = models.PositiveIntegerField(_('nombre de badges'), default=0)
    interventions_communaute = models.PositiveIntegerField(_('contributions communautaires'), default=0)
    
    # Localisation
    pays = models.CharField(_('pays'), max_length=100, default='Non renseigné')
    ville = models.CharField(_('ville'), max_length=100, blank=True, null=True)
    
    # Performance actuelle
    classement_actuel = models.BooleanField(_('dans top 10%'), default=False)
    progression_semaine = models.DecimalField(_('progression cette semaine %'), max_digits=5, decimal_places=2, default=0)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('classement')
        verbose_name_plural = _('classements')
        unique_together = ['user', 'periode', 'date_periode']
        ordering = ['-score_total', '-rang_mondial']
        indexes = [
            models.Index(fields=['rang_mondial']),
            models.Index(fields=['rang_national']),
            models.Index(fields=['score_total', 'date_periode']),
        ]

    def __str__(self):
        return f"#{self.rang_mondial} {self.user.full_name} - N{self.niveau} ({self.get_periode_display()})"
    
    def get_classe_sociale(self):
        """Détermine la classe sociale selon l'échelle"""
        if self.score_total >= 50000:
            return GlobalLeaderboard.Echelon.LEGENDE
        elif self.score_total >= 30000:
            return GlobalLeaderboard.Echelon.SAGE
        elif self.score_total >= 15000:
            return GlobalLeaderboard.Echelon.MAITRE
        elif self.score_total >= 8000:
            return GlobalLeaderboard.Echelon.EXPERT
        elif self.score_total >= 3000:
            return GlobalLeaderboard.Echelon.ETUDIAN
        elif self.score_total >= 500:
            return GlobalLeaderboard.Echelon.APPRENTI
        else:
            return GlobalLeaderboard.Echelon.NOVICE


class XPAction(models.Model):
    """
    Journal détaillé actions récompensées en XP
    Inspiré: Duolingo (daily streaks), Coursera (course completion)
    """
    ACTION_TYPES = [
        ('connexion', 'Connexion quotidienne'),
        ('composition_finie', 'Examen terminé'),
        ('note_excellente', 'Note ≥ 16/20'),
        ('badge_obtenu', 'Badge débloqué'),
        ('qcm_reussi', 'QCM réussi'),
        ('aide_partenaire', 'Aide donnée à pair'),
        ('contribution_forum', 'Post/forum créé'),
        ('streak_bonus', 'Bonus série'),
        ('competition_gagnee', 'Compétition remportée'),
        ('mentorat_heure', 'Heure de mentorat'),
        ('cours_termine', 'Cours complété'),
        ('participation_event', 'Événement participé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='xp_actions')
    action_type = models.CharField(_('type action'), max_length=50, choices=ACTION_TYPES)
    points_gagnes = models.PositiveIntegerField(_('points XP gagnés'), default=0)
    description = models.TextField(_('description'), blank=True)
    
    # Contexte adicional
    metadata = models.JSONField(_('métadonnées'), default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('action XP')
        verbose_name_plural = _('actions XP')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type']),
        ]


class StreakRecord(models.Model):
    """
    Système de streaks motivationnel avancé
    Inspiré: Duolingo (streak fire), Discord (activity levels)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='streak')
    
    # Séries actuelles
    current_streak = models.PositiveIntegerField(_('série actuelle jours'), default=0)
    longest_streak = models.PositiveIntegerField(_('plus longue série record'), default=0)
    
    # Tracking historique
    last_activity_date = models.DateField(_('dernière activité'), null=True, blank=True)
    last_check_date = models.DateField(_('dernier check'), null=True, blank=True)
    
    # Bonuses series
    streak_bonus_level = models.PositiveIntegerField(_('niveau bonus streak'), default=0)
    streak_multiplier = models.DecimalField(_('multiplicateur XP'), max_digits=3, decimal_places=2, default=1.0)
    
    # Statistiques complémentaires
    days_active_this_month = models.PositiveIntegerField(_('jours actifs ce mois'), default=0)
    total_logins = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('série activité')
        verbose_name_plural = _('séries activité')

    def update_streak(self):
        """Mise à jour intelligente des streaks avec gestion fuseau horaire"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if self.last_activity_date == today:
            return  # Déjà mis à jour aujourd'hui
        
        if self.last_activity_date and self.last_activity_date < yesterday:
            # Brise la série
            self.current_streak = 0
            self.streak_bonus_level = 0
            self.streak_multiplier = 1.0
        elif self.last_activity_date == yesterday or not self.last_activity_date:
            # Continue ou début
            self.current_streak += 1
            
            # Bonus milestones
            if self.current_streak >= 30:
                self.streak_bonus_level = 5
                self.streak_multiplier = 2.0
            elif self.current_streak >= 7:
                self.streak_bonus_level = 3
                self.streak_multiplier = 1.5
            elif self.current_streak >= 3:
                self.streak_bonus_level = 1
                self.streak_multiplier = 1.2
            
            # Record
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
        
        self.last_activity_date = today
        self.total_logins += 1
        self.last_check_date = today
        
        # Compteur mensuel
        current_month = today.month
        current_year = today.year
        # À implémenter: reset mensualisé
        
        self.save()
    
    def has_daily_reward(self):
        """Vérifie si récompense quotidienne disponible"""
        if not self.last_check_date:
            return True
        tomorrow = self.last_check_date + timedelta(days=1)
        return date.today() >= tomorrow
    
    def claim_daily_reward(self):
        """Réclame récompense quotidienne SANS Celery"""
        from .models import XPAction
        
        base_points = 10 + (self.streak_bonus_level * 5)
        total_points = int(base_points * float(self.streak_multiplier))
        
        # Création journal XP directement dans la requête
        xp_action = XPAction.objects.create(
            user=self.user,
            action_type="connexion",
            points_gagnes=total_points,
            description=f"Bonus série {self.streak_bonus_level}x ({base_points} XP de base)",
            metadata={
                'base': base_points,
                'multiplier': float(self.streak_multiplier),
                'streak_level': self.streak_bonus_level
            }
        )
        
        self.last_check_date = date.today()
        self.save(update_fields=['last_check_date'])
        
        logger = __import__('logging').getLogger(__name__)
        logger.info(f"[Gamification] Récompense quotidienne: +{total_points} XP pour utilisateur {self.user_id}")
        
        return total_points


class Competition(models.Model):
    """
    Compétitions temporelles type Codeforces/HackerRank
    Inspiré: Discord (events), Coursera (challenges)
    """
    class Status(models.TextChoices):
        PREPARATION = 'preparation', _('Préparation')
        EN_COURS = 'en_cours', _('En cours')
        TERMINEE = 'terminee', _('Terminée')
        ANNULEE = 'annulee', _('Annulée')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(_('titre'), max_length=200)
    description = models.TextField(_('description'))
    
    # Catégories
    categorie = models.CharField(_('catégorie'), max_length=100, default='Général')
    difficulte = models.CharField(_('difficulté'), max_length=20, default='moyen',
                                   choices=[('facile', 'Facile'), ('moyen', 'Moyen'), ('difficile', 'Difficile')])
    
    # Timing
    date_debut = models.DateTimeField(_('début'))
    date_fin = models.DateTimeField(_('fin'))
    duree_minutes = models.PositiveIntegerField(_('durée minutes'), default=60)
    
    # Récompenses
    prix_total = models.PositiveIntegerField(_('prix total XP'), default=1000)
    places_premieres = models.PositiveIntegerField(_('premiers prix'), default=1)
    
    # Participation
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PREPARATION)
    participants_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['status', 'date_debut']),
        ]

    def __str__(self):
        return f"{self.titre} ({self.get_status_display()})"


class CommunityContribution(models.Model):
    """
    Contributions communautaires type Discord forum/GitHub PRs
    """
    class Type(models.TextChoices):
        REPONSE_AIDE = 'reponse_aide', _('Réponse aide élève')
        PARTAGE_RESSOURCE = 'partage_ressource', _('Partage ressource')
        CREATION_CONTENU = 'creation_contenu', _('Création contenu')
        MODERATION = 'moderation', _('Modération')
        ORGANISATION_EVENT = 'organisation_event', _('Organisation événement')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contributor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contributions')
    type_contribution = models.CharField(_('type'), max_length=20, choices=Type.choices)
    titre = models.CharField(_('titre'), max_length=200)
    contenu = models.TextField(_('contenu'))
    
    # Impact
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    vues = models.PositiveIntegerField(default=0)
    
    # Récompense
    xp_recompense = models.PositiveIntegerField(default=25)
    est_recompensee = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-upvotes', '-created_at']

    def __str__(self):
        return f"{self.get_type_contribution_display()} par {self.contributor.full_name}"
